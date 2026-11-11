import sqlite3
from contextlib import contextmanager

TERMINAL = {"succeeded", "failed", "review"}

class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS operations (
                id TEXT PRIMARY KEY, amount INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued', token INTEGER NOT NULL DEFAULT 0,
                lease_until REAL NOT NULL DEFAULT 0, dispatched INTEGER NOT NULL DEFAULT 0,
                deadline REAL, receipt TEXT, error TEXT)""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, op_id, amount):
        if not isinstance(op_id, str) or not op_id or type(amount) is not int or amount <= 0:
            raise ValueError("nonempty id and positive integer amount required")
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO operations(id,amount) VALUES (?,?)", (op_id, amount))
            actual = db.execute("SELECT amount FROM operations WHERE id=?", (op_id,)).fetchone()[0]
            if actual != amount:
                raise ValueError("operation id already has a different amount")

    def get(self, op_id):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM operations WHERE id=?", (op_id,)).fetchone()
            if row is None:
                raise KeyError(op_id)
            return dict(row)

    def claim(self, op_id, now, lease):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM operations WHERE id=?", (op_id,)).fetchone()
            if row is None:
                raise KeyError(op_id)
            if row['status'] in TERMINAL:
                return row['status'], None
            if row['status'] != 'queued' and row['lease_until'] > now:
                return 'busy', None
            db.execute("UPDATE operations SET status='running', token=token+1, lease_until=? WHERE id=?", (now+lease, op_id))
            return 'claimed', dict(db.execute("SELECT * FROM operations WHERE id=?", (op_id,)).fetchone())

    def save(self, op_id, token, now, **changes):
        # Workers report the latest outcome here.
        with self.connect() as db:
            columns = ', '.join(name+'=?' for name in changes)
            db.execute('UPDATE operations SET '+columns+' WHERE id=?', (*changes.values(), op_id))
            return True
