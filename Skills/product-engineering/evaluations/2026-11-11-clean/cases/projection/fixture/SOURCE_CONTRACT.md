# Inventory journal contract

`Source.read(after)` returns an immutable `Page`. `after=None` starts a complete
history, including removed items. A cursor is an opaque string; pass it back
unchanged. Do not parse or compare cursors. The service retains this history;
there is no expiry or gap repair to implement.

- `next_cursor` is the exclusive checkpoint for all events in this page.
- A page can have zero events and still move the checkpoint: filtering and
  compaction leave holes. Only `done=True` says this catch-up has reached the end.
- Nonterminal pages always advance the cursor. A terminal page can advance it,
  including an empty terminal page. An empty terminal page may also return the
  current cursor. Every fetched page is a page even when empty or unchanged.
- Failures of `read` raise an exception without returning a page. They do not
  invalidate any previously returned checkpoint. A subsequent call may retry it.
- After a checkpoint, deliveries may repeat earlier events or arrive out of
  revision order. `done` is for this read, not a permanent end of the journal.

Each `Event` has an `item_id`, positive integer `generation`, positive integer
`revision`, and `kind` (`upsert` or `delete`). IDs may be reused after removal.
The generation increases on reuse, and revision restarts at 1. Within a
generation, revisions increase for corrections, quantity changes, and removal.
For each ID the latest event is the maximum **(generation, revision)** pair,
compared in that order. Arrival order has no authority. Across IDs, versions
have no ordering relationship. Equal pairs for an ID always have identical
kind and payload, so duplicates need no tie breaker. Delete is a normal versioned
event, even when the ID has never been seen locally; it must suppress older
upserts. A newer upsert may restore the item in the same or a later generation.
An upsert contains a complete replacement title (string) and quantity (integer
>= 0). A delete has title and quantity `None`.

The source supplies only valid events and pages. Concurrent writers, invalid
payloads, missing history and expiring cursors are outside this exercise.
