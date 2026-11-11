import tempfile
import unittest
from pathlib import Path
from durable import Store, Worker

class Provider:
    def __init__(self): self.calls = []
    def execute(self, key, amount, deadline):
        self.calls.append((key, amount, deadline)); return 'voucher-1'

class PublicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'state.sqlite'; self.store = Store(self.path)
    def test_enqueue_survives_reopen(self):
        self.store.enqueue('a', 7); self.store.enqueue('a', 7)
        self.assertEqual(Store(self.path).get('a')['amount'], 7)
        with self.assertRaises(ValueError): self.store.enqueue('a', 8)
    def test_simple_success_and_terminal_retry(self):
        self.store.enqueue('a', 7); provider = Provider()
        worker = Worker(self.store, provider, lambda: 0)
        self.assertEqual(worker.run('a'), 'succeeded')
        self.assertEqual(self.store.get('a')['receipt'], 'voucher-1')
        self.assertEqual(worker.run('a'), 'succeeded')
        self.assertEqual(len(provider.calls), 1)
    def test_invalid_input(self):
        for amount in (0, -1, True, '2'):
            with self.assertRaises(ValueError): self.store.enqueue('a', amount)

if __name__ == '__main__': unittest.main()
