# Catalog read projection

Python 3.11+, standard library only. Run `python3 -m unittest discover -s tests -v`.

A local catalog screen uses SQLite rather than asking the inventory service for
every row. `catch_up` replays the service journal; `dashboard.refresh` also keeps
the screen's totals. Read SOURCE_CONTRACT.md before changing journal handling.

## Stable Python API

Exports from `catalog_projection` (also available in their current modules):

- `Event(item_id, generation, revision, kind, title=None, quantity=None)` and
  `Page(events, next_cursor, done)` are frozen dataclasses. `Source.read(after)`
  is structural: any object with that method is accepted.
- `open_projection(path)` creates or opens a SQLite connection and initializes
  an empty projection if needed. The caller closes it. `:memory:` is supported.
- `get_cursor(conn)` returns the last committed opaque string, initially `None`.
- `list_items(conn)` returns `(item_id, title, quantity)` tuples sorted by ID;
  removed items are absent.
- `catch_up(conn, source, *, on_page=None, max_pages=None)` returns frozen
  `SyncReport(pages, applied, cursor)`. Pages is the number of committed fetched
  pages in this call, including empty pages. Applied counts events that strictly
  advance an ID's winning version, including deletes of unseen IDs. Duplicate
  and stale events do not count. Cursor is the last committed checkpoint.
  `max_pages=None` catches up through the first `done` page. A positive integer
  limits fetched pages; nonpositive values raise ValueError before reading.
  Repeated bounded calls must produce the same projection as one full call.
- Each page is one transaction: winning versions, visible items, checkpoint,
  and `on_page` writes commit together. If source reading or page processing
  raises, propagate that exception. The failed page leaves no writes; earlier
  successful pages stay committed. The connection must then be usable to retry.
- `on_page(conn, page)`, when supplied, runs exactly once per attempted fetched
  page, after this page's winning data and cursor are visible on that connection
  and before commit. It may read/write ordinary application tables and may
  raise. It must not close the connection, manage transactions, call catch_up
  recursively or cause nontransactional external effects. A retry invokes it
  again. Connections are passed to catch_up with no active transaction; the
  caller does not write concurrently.

## Persistence and consumers

`items(item_id, title, quantity)` is the stable SQL read interface. Keep its name,
columns and meaning: dashboard uses it directly. `projection_meta(singleton,
cursor)` and `item_state(item_id, generation, revision, deleted)` are the current
persistence schema. `item_state` records the winner even when deleted; `deleted`
is 0 or 1. Preserve compatible databases without changing their correct prefix
or checkpoint. You may add private schema if needed, but automatic migration of
these valid databases must preserve this behavior. No legacy schema exists in
this exercise and a schema change is not required.

Previously corrupted projections are repaired operationally by closing and
removing the disposable SQLite projection, then replaying from `None`. The
upstream journal is authoritative. Detecting and repairing historical corruption
in place is not part of catch_up. Test databases start empty or represent a
correctly applied prefix of the journal.

`dashboard.prepare(conn)` creates the consumer's totals table.
`dashboard.refresh(conn, source, *, max_pages=None)` passes its totals update as
`on_page`, returns the report, and retains all catch_up guarantees.
`dashboard.totals(conn)` returns `(item_count, total_quantity)`.
