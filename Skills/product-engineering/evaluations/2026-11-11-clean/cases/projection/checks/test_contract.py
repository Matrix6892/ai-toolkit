"""Behavioral checks derived from SOURCE_CONTRACT.md and public persistence API."""
import itertools
from pathlib import Path
import tempfile
import unittest

from catalog_projection import Event, Page, open_projection, catch_up, get_cursor, list_items
from catalog_projection import dashboard


def put(item, generation, revision, title=None, quantity=1):
    return Event(item, generation, revision, 'upsert', title or item, quantity)


def delete(item, generation, revision):
    return Event(item, generation, revision, 'delete')


class Script:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def read(self, after):
        self.calls.append(after)
        return self.pages[after]


class ProjectionContractTests(unittest.TestCase):
    def connection(self, path=':memory:'):
        conn = open_projection(str(path))
        self.addCleanup(conn.close)
        return conn

    def test_01_empty_bridge_is_not_end_of_history(self):
        conn = self.connection()
        source = Script({None: Page((), 'hole/~z', False),
                         'hole/~z': Page((put('a', 1, 1),), 'opaque:!a', True)})
        report = catch_up(conn, source)
        self.assertEqual(source.calls, [None, 'hole/~z'])
        self.assertEqual(list_items(conn), [('a', 'a', 1)])
        self.assertEqual((report.pages, report.applied, report.cursor), (2, 1, 'opaque:!a'))

    def test_02_empty_terminal_page_commits_checkpoint_and_hook(self):
        conn = self.connection()
        seen = []
        source = Script({None: Page((put('a', 1, 1),), 'z', False),
                         'z': Page((), 'a', True)})
        report = catch_up(conn, source, on_page=lambda c, p: seen.append(get_cursor(c)))
        self.assertEqual(seen, ['z', 'a'])
        self.assertEqual((report.pages, report.applied, get_cursor(conn)), (2, 1, 'a'))

    def test_03_polling_terminal_same_cursor_is_a_committed_page(self):
        conn = self.connection()
        catch_up(conn, Script({None: Page((put('a', 1, 1),), 'end', True)}))
        seen = []
        report = catch_up(conn, Script({'end': Page((), 'end', True)}),
                          on_page=lambda c, p: seen.append(p))
        self.assertEqual(len(seen), 1)
        self.assertEqual((report.pages, report.applied, report.cursor), (1, 0, 'end'))

    def test_04_bounded_empty_pages_resume_after_reopening(self):
        with tempfile.TemporaryDirectory(prefix='projection-contract-') as directory:
            path = Path(directory) / 'projection.sqlite'
            source = Script({None: Page((), 'middle', False),
                             'middle': Page((put('a', 2, 1, quantity=0),), 'finish', True)})
            conn = open_projection(str(path))
            try:
                report = catch_up(conn, source, max_pages=1)
                self.assertEqual((report.pages, report.cursor), (1, 'middle'))
            finally:
                conn.close()
            conn = open_projection(str(path))
            try:
                report = catch_up(conn, source, max_pages=1)
                self.assertEqual(list_items(conn), [('a', 'a', 0)])
                self.assertEqual((report.pages, report.applied, report.cursor), (1, 1, 'finish'))
                self.assertEqual(source.calls, [None, 'middle'])
            finally:
                conn.close()

    def test_05_new_generation_restarts_revision(self):
        conn = self.connection()
        report = catch_up(conn, Script({None: Page((put('id', 7, 80, 'Old'),
                                                   put('id', 8, 1, 'New', 0)), 'end', True)}))
        self.assertEqual(list_items(conn), [('id', 'New', 0)])
        self.assertEqual(report.applied, 2)

    def test_06_prior_generation_cannot_win_with_large_revision(self):
        conn = self.connection()
        report = catch_up(conn, Script({None: Page((put('id', 8, 2, 'New'),
                                                   put('id', 7, 999, 'Old')), 'end', True)}))
        self.assertEqual(list_items(conn), [('id', 'New', 1)])
        self.assertEqual(report.applied, 1)

    def test_07_tombstone_survives_redelivery_after_reopen(self):
        with tempfile.TemporaryDirectory(prefix='projection-contract-') as directory:
            path = Path(directory) / 'projection.sqlite'
            source = Script({None: Page((put('a', 1, 1), delete('a', 1, 3)), 'deleted', False),
                             'deleted': Page((put('a', 1, 2), delete('a', 1, 3)), 'end', True)})
            conn = open_projection(str(path))
            try:
                catch_up(conn, source, max_pages=1)
            finally:
                conn.close()
            conn = open_projection(str(path))
            try:
                report = catch_up(conn, source)
                self.assertEqual(list_items(conn), [])
                self.assertEqual(report.applied, 0)
            finally:
                conn.close()

    def test_08_delete_of_unseen_id_is_a_versioned_winner(self):
        conn = self.connection()
        report = catch_up(conn, Script({None: Page((delete('a', 4, 2), put('a', 4, 1)), 'end', True)}))
        self.assertEqual(list_items(conn), [])
        self.assertEqual(report.applied, 1)

    def test_09_corrections_restore_and_replace_whole_payload(self):
        conn = self.connection()
        events = (put('a', 2, 1, 'First', 9), delete('a', 2, 3),
                  put('a', 2, 4, 'Restored', 0), put('a', 2, 2, 'Stale', 8))
        report = catch_up(conn, Script({None: Page(events, 'end', True)}))
        self.assertEqual(list_items(conn), [('a', 'Restored', 0)])
        self.assertEqual(report.applied, 3)

    def test_10_duplicates_and_versions_are_scoped_to_each_id(self):
        conn = self.connection()
        events = (put('z', 5, 30), put('a', 1, 1), put('a', 1, 1),
                  delete('never', 1, 1), delete('never', 1, 1))
        report = catch_up(conn, Script({None: Page(events, 'end', True)}))
        self.assertEqual(list_items(conn), [('a', 'a', 1), ('z', 'z', 1)])
        self.assertEqual(report.applied, 3)

    def test_11_hook_failure_rolls_back_first_page_and_allows_retry(self):
        conn = self.connection()
        conn.execute('CREATE TABLE audit (cursor TEXT)')
        conn.commit()
        source = Script({None: Page((put('a', 1, 1), delete('ghost', 3, 1)), 'end', True),
                         'end': Page((), 'end', True)})
        error = RuntimeError('consumer unavailable')
        def failing_hook(c, p):
            c.execute('INSERT INTO audit VALUES (?)', (get_cursor(c),))
            raise error
        with self.assertRaises(RuntimeError) as raised:
            catch_up(conn, source, on_page=failing_hook)
        self.assertIs(raised.exception, error)
        self.assertEqual((list_items(conn), get_cursor(conn)), ([], None))
        self.assertFalse(conn.in_transaction)
        self.assertEqual(conn.execute('SELECT * FROM audit').fetchall(), [])
        report = catch_up(conn, source)
        self.assertEqual((report.pages, report.applied, report.cursor), (1, 2, 'end'))
        self.assertEqual(list_items(conn), [('a', 'a', 1)])

    def test_12_failed_later_page_keeps_previous_catalog_and_totals(self):
        conn = self.connection()
        dashboard.prepare(conn)
        source = Script({None: Page((put('a', 1, 1, quantity=3),), 'first', False),
                         'first': Page((delete('a', 1, 2), put('b', 1, 1, quantity=7)), 'second', True),
                         'second': Page((), 'second', True)})
        def consumer(c, p):
            dashboard.update_totals(c, p)
            if p.next_cursor == 'second':
                raise LookupError('summary refresh failed')
        with self.assertRaises(LookupError):
            catch_up(conn, source, on_page=consumer)
        self.assertEqual((get_cursor(conn), list_items(conn), dashboard.totals(conn)),
                         ('first', [('a', 'a', 3)], (1, 3)))
        report = dashboard.refresh(conn, source)
        self.assertEqual((report.pages, report.applied), (1, 2))
        self.assertEqual((list_items(conn), dashboard.totals(conn)), ([('b', 'b', 7)], (1, 7)))

    def test_13_read_error_preserves_prefix_and_exception(self):
        conn = self.connection()
        error = OSError('inventory temporarily offline')
        class Unavailable:
            def read(self, after):
                if after is None:
                    return Page((put('a', 1, 1),), 'first', False)
                raise error
        with self.assertRaises(OSError) as raised:
            catch_up(conn, Unavailable())
        self.assertIs(raised.exception, error)
        self.assertEqual((get_cursor(conn), list_items(conn)), ('first', [('a', 'a', 1)]))
        report = catch_up(conn, Script({'first': Page((put('a', 1, 2, 'Fixed'),), 'end', True)}))
        self.assertEqual((report.applied, list_items(conn)), (1, [('a', 'Fixed', 1)]))

    def test_14_hook_observes_new_rows_and_cursor_before_publication(self):
        with tempfile.TemporaryDirectory(prefix='projection-contract-') as directory:
            path = Path(directory) / 'projection.sqlite'
            conn = open_projection(str(path))
            observer = open_projection(str(path))
            try:
                seen = []
                def observe(c, p):
                    seen.append((get_cursor(c), list_items(c), get_cursor(observer), list_items(observer)))
                catch_up(conn, Script({None: Page((put('a', 1, 1),), 'end', True)}), on_page=observe)
                self.assertEqual(seen, [('end', [('a', 'a', 1)], None, [])])
                self.assertEqual((get_cursor(observer), list_items(observer)), ('end', [('a', 'a', 1)]))
            finally:
                observer.close()
                conn.close()

    def test_15_valid_existing_prefix_preserves_cursor_and_versions(self):
        conn = self.connection()
        # The documented persistence schema permits a correct prefix without replay.
        conn.execute("INSERT INTO items VALUES ('a', 'Current', 2)")
        conn.execute("INSERT INTO item_state VALUES ('a', 9, 2, 0)")
        conn.execute("INSERT INTO item_state VALUES ('gone', 3, 9, 1)")
        conn.execute("UPDATE projection_meta SET cursor='saved' WHERE singleton=1")
        conn.commit()
        source = Script({'saved': Page((put('a', 8, 100, 'Obsolete'), put('gone', 3, 2),
                                       put('b', 1, 1)), 'end', True)})
        report = catch_up(conn, source)
        self.assertEqual(source.calls, ['saved'])
        self.assertEqual(list_items(conn), [('a', 'Current', 2), ('b', 'b', 1)])
        self.assertEqual(report.applied, 1)

    def test_16_page_partition_and_delivery_order_do_not_change_final_rows(self):
        # Exhaustive, deterministic orders, independently derive the winner from source contract.
        events = (put('a', 1, 50, 'Old'), delete('a', 1, 51),
                  put('a', 2, 1, 'Replacement', 4), delete('b', 1, 5))
        for order in itertools.permutations(events):
            for split in (1, 3):
                with self.subTest(order=order, split=split):
                    conn = open_projection(':memory:')
                    try:
                        source = Script({None: Page(order[:split], 'p', False),
                                         'p': Page(order[split:] + (put('b', 1, 1),), 'end', True)})
                        catch_up(conn, source, max_pages=1)
                        catch_up(conn, source)
                        self.assertEqual(list_items(conn), [('a', 'Replacement', 4)])
                    finally:
                        conn.close()

if __name__ == '__main__':
    unittest.main()
