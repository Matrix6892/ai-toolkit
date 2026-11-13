# Review database and consumer
The packet reader uses a local PostgreSQL projection of the event log.
Each event inserts an immutable row keyed by (museum, event_number).
The row contains the full event payload and its preview digest.
Duplicate delivery checks the existing row and verifies the same payload; it is a no-op.
Rows are never updated in place; disposition history therefore remains queryable.
A per-museum control row tracks the consumer's durable position.
The worker transaction inserts the row and updates that control row atomically.
The database commits synchronously and guarantees transaction atomicity and durability.
Readers use the primary; replicas and caches are outside the packet read path.
A museum begins with no events, no version rows and position zero.
Within a guide, database versions are resolved by event number, not completion timestamp.
Workers may finish out of order; a large preview's validation can occupy a worker longer.
A consumer crash discards its uncommitted transaction; the broker later redelivers it.
Committed version rows and the control row survive restart together.
Source event numbers are dense; every integer up to a head denotes one accepted mutation.
There are no intentionally dropped review events or side-channel review writes.
Retention keeps all rows needed by pending exports and 90-day retained packets.
The consumer publishes best-effort activity-strip updates after committing each callback.
The strip's timestamp and rough counters are never used as packet input.
