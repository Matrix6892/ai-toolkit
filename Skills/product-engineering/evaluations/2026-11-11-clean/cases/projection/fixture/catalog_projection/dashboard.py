"""Consumer: totals shown next to the catalog must match its committed page."""
from .projector import catch_up

def prepare(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS dashboard_totals (singleton INTEGER PRIMARY KEY, item_count INTEGER NOT NULL, quantity INTEGER NOT NULL)")
    conn.execute("INSERT OR IGNORE INTO dashboard_totals VALUES (1, 0, 0)")
    conn.commit()

def refresh(conn, source, *, max_pages=None):
    return catch_up(conn, source, on_page=update_totals, max_pages=max_pages)

def update_totals(conn, page):
    count, quantity = conn.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0) FROM items").fetchone()
    conn.execute("UPDATE dashboard_totals SET item_count=?, quantity=? WHERE singleton=1", (count, quantity))

def totals(conn):
    return conn.execute("SELECT item_count, quantity FROM dashboard_totals WHERE singleton=1").fetchone()
