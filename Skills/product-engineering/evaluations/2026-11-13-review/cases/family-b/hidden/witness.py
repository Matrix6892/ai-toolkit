#!/usr/bin/env python3
"""Bounded executable model of catalog transaction commit order, not a production bug."""
from pathlib import Path
from itertools import permutations
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent

def simulate(packet, order):
    # One LIVE bundle, project deadline 90, individual deadline 80, catalog time 100.
    # Extensions set the relevant deadline to 200. All transactions below are atomic.
    state = dict(live=True, policy=90, policy_rev=1, own=80, row_rev=1, project='A')
    ticket = None
    obligations = []
    receipts = []
    trace = []
    violations = []
    for action in order:
        if action == 'prepare':
            if state['live'] and max(state['policy'], state['own']) <= 100:
                ticket = {k: state[k] for k in ('row_rev', 'policy_rev', 'project')}
                trace.append('prepare: signed ticket issued')
            else:
                trace.append('prepare: no eligible bundle')
        elif action == 'amend':
            state['policy'] = 200
            state['policy_rev'] += 1
            if state['live']:
                obligations.append(('project amendment', 200))
            trace.append('amend: project deadline 200 committed')
        elif action == 'individual':
            if state['live']:
                state['own'] = 200
                state['row_rev'] += 1
                obligations.append(('individual extension', 200))
                trace.append('individual: own deadline 200 committed')
        elif action == 'move':
            if state['live']:
                # Destination project B has the same deadline/revision as A initially.
                state['own'] = max(state['own'], state['policy'])
                state['project'] = 'B'
                state['policy'] = 90
                state['policy_rev'] = 1
                state['row_rev'] += 1
                trace.append('move: reassigned; source obligation retained individually')
        elif action == 'execute':
            match = ticket is not None and state['live'] and all(
                state[k] == ticket[k] for k in ('row_rev', 'project'))
            if packet == 'packet-q' and ticket is not None:
                match = match and state['policy_rev'] == ticket['policy_rev']
            if match:
                # State transition and receipt insert are the same transaction.
                violations += [name for name, deadline in obligations if deadline > 100]
                state['live'] = False
                state['row_rev'] += 1
                receipts.append('receipt-1')
                trace.append('execute: ERASED committed at time 100')
            else:
                trace.append('execute: eligibility rejected')
        else:
            raise AssertionError(action)
    assert len(receipts) <= 1
    assert bool(receipts) == (not state['live'])
    return dict(trace=trace, violations=violations, erased=not state['live'])

def main():
    oracle = json.loads((ROOT / 'hidden/oracle.json').read_text())
    for name, expected in oracle['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    failing = simulate('packet-p', ('prepare', 'amend', 'execute'))
    assert failing['violations'] == ['project amendment']
    protected = simulate('packet-q', ('prepare', 'amend', 'execute'))
    assert protected['violations'] == [] and not protected['erased']
    # Cover all commit orders of one amendment, extension and reassignment against
    # a planner/executor pair. No event delivery or stronger DB isolation is assumed.
    counts = {}
    for packet in ('packet-p', 'packet-q'):
        examined = failures = 0
        for order in permutations(('prepare', 'execute', 'amend', 'individual', 'move')):
            if order.index('prepare') > order.index('execute'):
                continue
            examined += 1
            result = simulate(packet, order)
            failures += bool(result['violations'])
            if packet == 'packet-q':
                assert not result['violations'], (order, result)
        counts[packet] = dict(schedules=examined, violating_schedules=failures)
    # Meaningful progress: before an extension, an eligible bundle can be erased.
    for packet in ('packet-p', 'packet-q'):
        r = simulate(packet, ('prepare', 'execute', 'amend'))
        assert r['erased'] and not r['violations']
    print(json.dumps({'status':'passed', 'minimal_counterexample':failing,
                      'protected_trace':protected, 'bounded_commit_orders':counts}, indent=2))

if __name__ == '__main__':
    main()
