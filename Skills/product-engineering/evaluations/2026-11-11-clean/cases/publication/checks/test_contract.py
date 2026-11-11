import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from artifact_bundle import PackageError, publish, open_package
from report_view import render, current_report


def report(title, detail):
    return {'summary.json': json.dumps({'title': title}).encode(), 'detail.txt': detail.encode()}


def tree(root):
    if not root.exists():
        return None
    return {str(p.relative_to(root)): p.read_bytes() if p.is_file() else None for p in root.rglob('*')}


class PublicationContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='bundle-hidden-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'shared'

    def test_01_first_validation_does_not_activate_candidate(self):
        seen = []
        def validate(candidate):
            seen.append((candidate.read('data.csv'), open_package(self.root)))
        publish(self.root, {'data.csv': b'1,2\n'}, validate=validate)
        self.assertEqual(seen, [(b'1,2\n', None)])
        self.assertEqual(open_package(self.root).read('data.csv'), b'1,2\n')

    def test_02_validation_observes_previous_complete_report(self):
        old_id = publish(self.root, report('Before', 'old'))
        seen = []
        def validate(candidate):
            active = open_package(self.root)
            seen.append((active.release_id, render(active), render(candidate)))
        new_id = publish(self.root, report('After', 'new'), validate=validate)
        self.assertNotEqual(old_id, new_id)
        self.assertEqual(seen, [(old_id, 'Before\nold', 'After\nnew')])
        self.assertEqual(current_report(self.root), 'After\nnew')

    def test_03_rejected_candidate_preserves_previous_pointer_and_files(self):
        publish(self.root, report('Accepted', 'stable'))
        pointer_before = (self.root / 'CURRENT').read_bytes()
        previous = open_package(self.root)
        error = LookupError('candidate is not suitable')
        def reject(candidate):
            self.assertEqual(render(candidate), 'Rejected\nbad')
            raise error
        with self.assertRaises(LookupError) as caught:
            publish(self.root, report('Rejected', 'bad'), validate=reject)
        self.assertIs(caught.exception, error)
        self.assertEqual((self.root / 'CURRENT').read_bytes(), pointer_before)
        self.assertEqual(render(previous), 'Accepted\nstable')
        self.assertEqual(current_report(self.root), 'Accepted\nstable')

    def test_04_rejected_first_candidate_keeps_current_absent(self):
        error = RuntimeError('reject')
        def reject(candidate):
            raise error
        with self.assertRaises(RuntimeError) as caught:
            publish(self.root, {'a.txt': b'a'}, validate=reject)
        self.assertIs(caught.exception, error)
        self.assertFalse((self.root / 'CURRENT').exists())
        self.assertIsNone(open_package(self.root))

    def test_05_retained_reader_survives_multiple_successful_publications(self):
        old_id = publish(self.root, report('Old', 'one'))
        old = open_package(self.root)
        middle_id = publish(self.root, report('Middle', 'two'))
        middle = open_package(self.root)
        latest_id = publish(self.root, report('Latest', 'three'))
        self.assertEqual(len({old_id, middle_id, latest_id}), 3)
        self.assertEqual(old.release_id, old_id)
        self.assertEqual(render(old), 'Old\none')
        self.assertEqual(render(middle), 'Middle\ntwo')
        self.assertEqual(current_report(self.root), 'Latest\nthree')

    def test_06_replacement_names_and_exact_binary_payloads(self):
        publish(self.root, {'old.txt': b'old'})
        files = {'empty.txt': b'', 'bytes.csv': b'\x00\xff\r\n\x80', 'text.txt': 'Привет'.encode()}
        publish(self.root, files)
        reader = open_package(self.root)
        self.assertEqual(reader.names, tuple(sorted(files)))
        for name, data in files.items():
            self.assertEqual(reader.read(name), data)
        with self.assertRaises(KeyError):
            reader.read('old.txt')

    def test_07_unrelated_files_in_shared_root_and_releases_survive(self):
        foreign = self.root / 'releases' / 'foreign-work'
        foreign.mkdir(parents=True)
        (foreign / 'notes.txt').write_bytes(b'owned elsewhere')
        (self.root / 'CURRENT.tmp').write_bytes(b'not ours')
        (self.root / '.staging').mkdir()
        (self.root / '.staging' / 'keep').write_bytes(b'keep')
        expected = {p: p.read_bytes() for p in (foreign / 'notes.txt', self.root / 'CURRENT.tmp', self.root / '.staging' / 'keep')}
        publish(self.root, {'a.txt': b'first'})
        publish(self.root, {'a.txt': b'second'})
        for path, content in expected.items():
            self.assertEqual(path.read_bytes(), content)

    def test_08_invalid_inputs_fail_before_any_mutation_or_validation(self):
        cases = ({}, {'nested/name.txt': b'x'}, {'../escape.txt': b'x'},
                 {'manifest.json': b'{}'}, {'Upper.txt': b'x'},
                 {'a.txt': 'not bytes'}, {'a.txt': bytearray(b'x')}, {1: b'x'})
        for initial in (False, True):
            for index, files in enumerate(cases):
                case_root = self.root / f'case-{initial}-{index}'
                if initial:
                    publish(case_root, {'good.txt': b'accepted'})
                before = tree(case_root)
                with self.subTest(initial=initial, files=files):
                    seen = []
                    with self.assertRaises(ValueError):
                        publish(case_root, files, validate=seen.append)
                    self.assertEqual(seen, [])
                    self.assertEqual(tree(case_root), before)

    def test_09_same_length_corruption_is_not_returned_as_payload(self):
        release = publish(self.root, {'data.csv': b'10,20\n'})
        reader = open_package(self.root)
        (self.root / 'releases' / release / 'data.csv').write_bytes(b'99,20\n')
        with self.assertRaises(PackageError):
            reader.read('data.csv')
        with self.assertRaises(PackageError):
            open_package(self.root).read('data.csv')

    def test_10_missing_declared_payload_is_typed_and_preserves_cause(self):
        release = publish(self.root, {'a.txt': b'a'})
        reader = open_package(self.root)
        (self.root / 'releases' / release / 'a.txt').unlink()
        with self.assertRaises(PackageError) as caught:
            reader.read('a.txt')
        self.assertIsInstance(caught.exception.__cause__, OSError)
        with self.assertRaises(KeyError):
            reader.read('never.txt')

    def test_11_invalid_pointer_shapes_and_encoding_are_package_errors(self):
        self.root.mkdir()
        cases = (b'{', b'\xff', b'[]', b'{}', b'{"release":null}',
                 b'{"release":"../outside"}', b'{"release":"A"}',
                 json.dumps({'release': 'a'*32, 'extra': 1}).encode())
        for payload in cases:
            with self.subTest(payload=payload):
                (self.root / 'CURRENT').write_bytes(payload)
                with self.assertRaises(PackageError):
                    open_package(self.root)

    def test_12_missing_or_invalid_manifest_is_not_no_active_package(self):
        release = publish(self.root, {'a.txt': b'a'})
        manifest = self.root / 'releases' / release / 'manifest.json'
        manifest.unlink()
        with self.assertRaises(PackageError) as caught:
            open_package(self.root)
        self.assertIsInstance(caught.exception.__cause__, OSError)
        good_hash = hashlib.sha256(b'a').hexdigest()
        cases = (b'{', b'\xff', b'[]', b'{}', b'{"format":1,"files":{}}',
                 json.dumps({'format': True, 'files': {'a.txt': good_hash}}).encode(),
                 json.dumps({'format': 2, 'files': {'a.txt': good_hash}}).encode(),
                 json.dumps({'format': 1, 'files': {'a.txt': 'not a hash'}}).encode(),
                 json.dumps({'format': 1, 'files': {'../a.txt': good_hash}}).encode())
        for payload in cases:
            with self.subTest(payload=payload):
                manifest.write_bytes(payload)
                with self.assertRaises(PackageError):
                    open_package(self.root)

    def test_13_existing_valid_disk_protocol_remains_readable(self):
        release = '0123456789abcdef0123456789abcdef'
        directory = self.root / 'releases' / release
        directory.mkdir(parents=True)
        files = report('Existing', 'keep me')
        for name, payload in files.items():
            (directory / name).write_bytes(payload)
        hashes = {name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()}
        (directory / 'manifest.json').write_text(json.dumps({'files': hashes, 'format': 1}, indent=2))
        (self.root / 'CURRENT').write_text(json.dumps({'release': release}, indent=2))
        reader = open_package(self.root)
        self.assertEqual(render(reader), 'Existing\nkeep me')
        publish(self.root, report('New', 'published later'))
        self.assertEqual(render(reader), 'Existing\nkeep me')
        self.assertEqual((directory / 'detail.txt').read_bytes(), b'keep me')

    def test_14_consumer_interleaved_with_publication_uses_one_release(self):
        publish(self.root, report('First heading', 'first detail'))
        captured = open_package(self.root)
        class InterleavedReader:
            def read(inner, name):
                result = captured.read(name)
                if name == 'summary.json':
                    publish(self.root, report('Second heading', 'second detail'))
                return result
        self.assertEqual(render(InterleavedReader()), 'First heading\nfirst detail')
        self.assertEqual(current_report(self.root), 'Second heading\nsecond detail')

    def test_15_retry_after_validator_failure_can_publish(self):
        calls = []
        def reject(candidate):
            calls.append(candidate.read('a.txt'))
            raise ArithmeticError('try again with a corrected report')
        with self.assertRaises(ArithmeticError):
            publish(self.root, {'a.txt': b'bad'}, validate=reject)
        release = publish(self.root, {'a.txt': b'corrected'}, validate=lambda candidate: calls.append(candidate.read('a.txt')))
        reader = open_package(self.root)
        self.assertEqual((reader.release_id, reader.read('a.txt')), (release, b'corrected'))
        self.assertEqual(calls, [b'bad', b'corrected'])

if __name__ == '__main__':
    unittest.main()
