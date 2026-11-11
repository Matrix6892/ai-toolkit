import tempfile
import unittest
from pathlib import Path
from durable import Store, Worker, OutcomeUnknown, DefinitelyRejected, Observation

class Crash(BaseException): pass

class Clock:
    def __init__(self): self.now=100
    def __call__(self): return self.now

class Provider:
    def __init__(self, clock):
        self.clock=clock; self.records={}; self.calls=[]; self.effects=[]
        self.execute_hook=None; self.lookup_hook=None; self.mode='ok'; self.lookup_mode=None
    def execute(self, key, amount, deadline):
        self.calls.append(('execute', key, amount, deadline))
        if self.execute_hook:
            hook,self.execute_hook=self.execute_hook,None; hook()
        if self.mode == 'before':
            self.mode='ok'; raise OutcomeUnknown('connection lost')
        if self.mode == 'reject': raise DefinitelyRejected('invalid account')
        prior=self.records.get(key)
        if prior and self.clock()<prior[2]:
            if prior[1:] != (amount,deadline): raise AssertionError('key parameters changed')
            return prior[0]
        receipt=f'voucher-{len(self.effects)+1}'
        self.effects.append((key,amount,receipt)); self.records[key]=(receipt,amount,deadline)
        mode,self.mode=self.mode,'ok'
        if mode=='after': raise OutcomeUnknown('connection lost')
        if mode=='crash': raise Crash()
        if mode=='unexpected': raise RuntimeError('transport bug')
        return receipt
    def lookup(self,key,deadline):
        self.calls.append(('lookup',key,deadline))
        if self.lookup_hook:
            hook,self.lookup_hook=self.lookup_hook,None; hook()
        if self.lookup_mode=='unknown': raise OutcomeUnknown('lookup unavailable')
        if self.lookup_mode=='absent': return Observation('absent')
        if key in self.records and self.clock()<deadline:
            return Observation('found',self.records[key][0])
        if self.lookup_mode=='retained' and key in self.records:
            return Observation('found',self.records[key][0])
        return Observation('absent' if self.clock()<deadline else 'expired')

class Acceptance(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.sqlite';self.store=Store(self.path)
        self.clock=Clock();self.provider=Provider(self.clock)
        self.store.enqueue('a',7);self.worker=self.new_worker()
    def new_worker(self): return Worker(Store(self.path),self.provider,self.clock)
    def row(self): return self.store.get('a')
    def crash(self):
        self.provider.mode='crash'
        with self.assertRaises(Crash):self.worker.run('a')
    def test_01_write_ahead_evidence(self):
        def inspect():
            row=Store(self.path).get('a')
            self.assertEqual(row['dispatched'],1);self.assertEqual(row['deadline'],130)
        self.provider.execute_hook=inspect
        self.assertEqual(self.worker.run('a'),'succeeded')
        self.assertEqual(self.provider.calls[0][1],'op:a')
    def test_02_unknown_after_commit_reconciles(self):
        self.provider.mode='after';self.assertEqual(self.worker.run('a'),'uncertain')
        self.clock.now+=11
        self.assertEqual(self.new_worker().run('a'),'succeeded')
        self.assertEqual(len(self.provider.effects),1)
        self.assertEqual(len([c for c in self.provider.calls if c[0]=='execute']),1)
        self.assertTrue(any(c[0]=='lookup' for c in self.provider.calls))
    def test_03_unknown_before_commit_replays_same_identity(self):
        self.provider.mode='before';self.worker.run('a');self.clock.now+=11
        self.assertEqual(self.new_worker().run('a'),'succeeded')
        attempts=[c for c in self.provider.calls if c[0]=='execute']
        self.assertEqual(attempts,[('execute','op:a',7,130)]*2)
    def test_04_crash_recovery_after_restart(self):
        self.crash();self.clock.now=111
        self.assertEqual(self.new_worker().run('a'),'succeeded')
        self.assertEqual(len(self.provider.effects),1)
    def test_05_expired_history_requires_review(self):
        self.crash();self.clock.now=131
        self.assertEqual(self.new_worker().run('a'),'review')
        self.assertEqual(len(self.provider.effects),1)
        count=len(self.provider.calls)
        self.assertEqual(self.new_worker().run('a'),'review')
        self.assertEqual(len(self.provider.calls),count)
    def test_06_found_after_expiry_still_settles(self):
        self.crash();self.clock.now=131;self.provider.lookup_mode='retained'
        self.assertEqual(self.new_worker().run('a'),'succeeded')
        self.assertEqual(self.row()['receipt'],'voucher-1')
    def test_07_absence_after_window_is_not_permission(self):
        self.provider.mode='before';self.worker.run('a');self.clock.now=130
        self.provider.lookup_mode='absent'
        self.assertEqual(self.new_worker().run('a'),'review')
        self.assertEqual(len(self.provider.effects),0)
    def test_08_live_lease_blocks_second_worker(self):
        nested=[]
        self.provider.execute_hook=lambda:nested.append(self.new_worker().run('a'))
        self.assertEqual(self.worker.run('a'),'succeeded')
        self.assertEqual(nested,['busy']);self.assertEqual(len(self.provider.effects),1)
    def test_09_stale_success_cannot_replace_newer_owner(self):
        nested=[]
        def takeover():
            self.clock.now=111;nested.append(self.new_worker().run('a'))
        self.provider.execute_hook=takeover
        self.assertEqual(self.worker.run('a'),'stale')
        self.assertEqual(nested,['succeeded']);self.assertEqual(self.row()['token'],2)
        self.assertEqual(self.row()['receipt'],'voucher-1');self.assertEqual(len(self.provider.effects),1)
    def test_10_expired_owner_without_successor_is_stale(self):
        self.provider.execute_hook=lambda:setattr(self.clock,'now',110)
        self.assertEqual(self.worker.run('a'),'stale')
        self.assertNotEqual(self.row()['status'],'succeeded')
        self.assertEqual(self.new_worker().run('a'),'succeeded')
    def test_11_lookup_delay_crosses_deadline(self):
        self.provider.mode='before';self.worker.run('a');self.clock.now=121
        self.provider.lookup_mode='absent'
        self.provider.lookup_hook=lambda:setattr(self.clock,'now',130)
        # Lease acquired at 121 remains valid until 131, but retention expires at 130.
        self.assertEqual(self.new_worker().run('a'),'review')
        self.assertEqual(len(self.provider.effects),0)
    def test_12_stale_lookup_cannot_dispatch(self):
        self.provider.mode='before';self.worker.run('a');self.clock.now=111
        nested=[]
        def takeover():
            self.clock.now=122;nested.append(self.new_worker().run('a'))
        self.provider.lookup_hook=takeover
        self.assertEqual(self.new_worker().run('a'),'stale')
        self.assertEqual(nested,['succeeded']);self.assertEqual(len(self.provider.effects),1)
        self.assertEqual(len([c for c in self.provider.calls if c[0]=='execute']),2)
    def test_13_lookup_unavailable_stays_recoverable(self):
        self.crash();self.clock.now=111;self.provider.lookup_mode='unknown'
        self.assertEqual(self.new_worker().run('a'),'uncertain')
        self.assertEqual(self.row()['deadline'],130)
        self.provider.lookup_mode=None;self.clock.now=122  # after the retained lease expires; still before retention deadline
        self.assertEqual(self.new_worker().run('a'),'succeeded')
    def test_14_rejection_is_terminal(self):
        self.provider.mode='reject';self.assertEqual(self.worker.run('a'),'failed')
        count=len(self.provider.calls);self.clock.now=200
        self.assertEqual(self.new_worker().run('a'),'failed');self.assertEqual(len(self.provider.calls),count)
        self.assertEqual(len(self.provider.effects),0)
    def test_15_unexpected_exception_preserves_recovery(self):
        self.provider.mode='unexpected'
        with self.assertRaises(RuntimeError):self.worker.run('a')
        self.assertEqual(self.row()['dispatched'],1);self.clock.now=111
        self.assertEqual(self.new_worker().run('a'),'succeeded');self.assertEqual(len(self.provider.effects),1)
    def test_16_old_queued_operation_can_start(self):
        self.clock.now=10000
        self.assertEqual(self.worker.run('a'),'succeeded')
        self.assertEqual(self.row()['deadline'],10030)

if __name__=='__main__':unittest.main()
