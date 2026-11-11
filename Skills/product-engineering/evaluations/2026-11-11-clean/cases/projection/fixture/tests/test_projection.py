import unittest
from catalog_projection import Event, Page, open_projection, catch_up, list_items, get_cursor
from catalog_projection import dashboard

class OnePage:
    def read(self, after):
        if after is None:
            return Page((Event("lamp", 1, 1, "upsert", "Desk lamp", 3),), "tail/A", True)
        return Page((), "tail/A", True)

class ProjectionSmokeTests(unittest.TestCase):
    def setUp(self):
        self.conn = open_projection(":memory:")
        self.addCleanup(self.conn.close)

    def test_first_page_is_readable(self):
        report = catch_up(self.conn, OnePage())
        self.assertEqual(list_items(self.conn), [("lamp", "Desk lamp", 3)])
        self.assertEqual(get_cursor(self.conn), "tail/A")
        self.assertEqual((report.pages, report.applied, report.cursor), (1, 1, "tail/A"))

    def test_dashboard_consumes_sql_rows(self):
        dashboard.prepare(self.conn)
        dashboard.refresh(self.conn, OnePage())
        self.assertEqual(dashboard.totals(self.conn), (1, 3))

    def test_page_limit_is_checked_before_source(self):
        with self.assertRaises(ValueError):
            catch_up(self.conn, object(), max_pages=0)

    def test_full_upsert_replaces_previous_content(self):
        class Corrections:
            def read(self, after):
                return Page((Event("lamp", 1, 1, "upsert", "Wrong", 9),
                             Event("lamp", 1, 2, "upsert", "Desk lamp", 3)), "tail", True)
        report = catch_up(self.conn, Corrections())
        self.assertEqual(report.applied, 2)
        self.assertEqual(list_items(self.conn), [("lamp", "Desk lamp", 3)])

if __name__ == "__main__":
    unittest.main()
