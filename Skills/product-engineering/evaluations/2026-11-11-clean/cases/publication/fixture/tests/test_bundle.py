from pathlib import Path
import tempfile
import unittest
from artifact_bundle import publish, open_package
from report_view import current_report

class BundleSmokeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='bundle-public-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'reports'

    def test_no_published_report(self):
        self.assertIsNone(open_package(self.root))
        self.assertIsNone(current_report(self.root))

    def test_first_report_is_consumable(self):
        token = publish(self.root, {'summary.json': b'{"title":"Stock"}', 'detail.txt': b'12 units'})
        self.assertEqual(open_package(self.root).release_id, token)
        self.assertEqual(current_report(self.root), 'Stock\n12 units')

    def test_names_are_sorted_and_unknown_name_is_key_error(self):
        publish(self.root, {'z.txt': b'z', 'a.txt': b'a'})
        reader = open_package(self.root)
        self.assertEqual(reader.names, ('a.txt', 'z.txt'))
        with self.assertRaises(KeyError):
            reader.read('missing.txt')

    def test_validator_reads_candidate(self):
        seen = []
        publish(self.root, {'data.csv': b'a,b\n1,2\n'},
                validate=lambda candidate: seen.append(candidate.read('data.csv')))
        self.assertEqual(seen, [b'a,b\n1,2\n'])

if __name__ == '__main__':
    unittest.main()
