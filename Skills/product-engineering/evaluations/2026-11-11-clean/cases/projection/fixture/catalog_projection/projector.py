"""SQLite read model for the catalog screen."""
import sqlite3
from dataclasses import dataclass
from collections.abc import Callable
from .source import Page, Source

@dataclass(frozen=True)
class SyncReport:
    pages: int
    applied: int
    cursor: str | None

SCHEMA = """
CREATE TABLE IF NOT EXISTS projection_meta (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1), cursor TEXT
);
INSERT OR IGNORE INTO projection_meta VALUES (1, NULL);
CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY, title TEXT NOT NULL, quantity INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS item_state (
    item_id TEXT PRIMARY KEY, generation INTEGER NOT NULL,
    revision INTEGER NOT NULL, deleted INTEGER NOT NULL CHECK(deleted IN (0, 1))
);
"""

def open_projection(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn

def get_cursor(conn: sqlite3.Connection) -> str | None:
    return conn.execute("SELECT cursor FROM projection_meta WHERE singleton=1").fetchone()[0]

def list_items(conn: sqlite3.Connection) -> list[tuple[str, str, int]]:
    return conn.execute("SELECT item_id, title, quantity FROM items ORDER BY item_id").fetchall()

def catch_up(conn: sqlite3.Connection, source: Source, *,
             on_page: Callable[[sqlite3.Connection, Page], None] | None = None,
             max_pages: int | None = None) -> SyncReport:
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be positive")
    pages = applied = 0
    while max_pages is None or pages < max_pages:
        page = source.read(get_cursor(conn))
        if not page.events:
            break
        changed = 0
        for event in page.events:
            old = conn.execute("SELECT generation, revision FROM item_state WHERE item_id=?",
                               (event.item_id,)).fetchone()
            if old is not None and event.revision <= old[1]:
                continue
            if event.kind == "delete":
                conn.execute("DELETE FROM items WHERE item_id=?", (event.item_id,))
                conn.execute("DELETE FROM item_state WHERE item_id=?", (event.item_id,))
            else:
                conn.execute("INSERT OR REPLACE INTO items VALUES (?, ?, ?)",
                             (event.item_id, event.title, event.quantity))
                conn.execute("INSERT OR REPLACE INTO item_state VALUES (?, ?, ?, 0)",
                             (event.item_id, event.generation, event.revision))
            conn.commit()
            changed += 1
        conn.execute("UPDATE projection_meta SET cursor=? WHERE singleton=1", (page.next_cursor,))
        conn.commit()
        if on_page:
            on_page(conn, page)
            conn.commit()
        pages += 1
        applied += changed
        if page.done:
            break
    return SyncReport(pages, applied, get_cursor(conn))
