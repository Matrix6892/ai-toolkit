# Service contract and public API

A durable operation is identified by a caller-supplied nonempty string ID and an immutable
positive integer amount. Once accepted, retries with that ID refer to the same operation,
including after restarting Python or opening another Store for the same SQLite file.
The service must obey the dispatch/recovery policy below to avoid unsafe duplicate attempts. This is a policy-level guarantee, not a guarantee of exactly one provider effect under every schedule.
Success may only be recorded with an actual provider receipt. Failed means a permanent
provider rejection. Review means automation cannot safely settle the operation and a human
must investigate. Review is a valid safe terminal result, but must not replace automatic
recovery while provider evidence still permits it. No exactly-once guarantee is assumed. In particular, execute may remain in flight beyond the retention window; an older call can complete after another worker has replayed. The API offers no cancellation or permanent deduplication, so the service cannot eliminate that provider-level risk. State and authority must still follow this contract; describe this limitation rather than promising a stronger external guarantee.

Supported API (keep signatures/imports and row fields compatible):
- `from durable import Store, Worker, OutcomeUnknown, DefinitelyRejected, Observation`
- `Store(path)` initializes/reopens a SQLite file; connections are short-lived.
- `store.enqueue(op_id, amount)` is idempotent with equal input, raises ValueError for
  invalid input or reuse with a different amount; does not alter an existing operation.
- `store.get(op_id)` returns a dict including id, amount, status, token, lease_until,
  dispatched, deadline, receipt, error. Unknown IDs raise KeyError.
- `Worker(store, provider, clock, lease_seconds=10)`. `clock()` is an injected numeric
  monotonic time source; tests can advance it. All workers use the same time domain.
- `worker.run(op_id)` performs one bounded attempt and returns current outcome:
  queued/running/uncertain/succeeded/failed/review, busy if another live lease exists,
  stale if this invocation lost its authority before publishing an outcome.
  Unknown operation raises KeyError. There are no background threads or sleeps.
- Provider methods and exceptions are defined in PROVIDER.md; Observation is immutable.

Statuses: queued (never dispatched), running (leased), uncertain (external outcome unknown),
succeeded, failed, review. Last three are terminal and subsequent runs have no provider calls.
A live lease excludes a second run; expiry at `now >= lease_until` permits takeover.
Each takeover increments token. A token is a generation number preventing an older worker
from changing the new owner's row. Expired owners cannot publish outcomes or issue further
provider calls, even if no successor has acquired the row yet. An already in-flight provider
call cannot be cancelled by lease expiry; its outcome may need later reconciliation.

Before invoking execute, durable storage must record that an external attempt is possible,
with a stable key `op:{op_id}` and its immutable deadline (first dispatch time + 30 seconds).
The row's dispatched/deadline fields are the recovery evidence. Recovery of a dispatched
row consults provider lookup first. An absent observation before the deadline permits
replay using the SAME key, amount and deadline. Found settles success. Expired evidence
requires review. Even when lookup reports absent, local time at/after deadline forbids
execute. Recheck authority and time after lookup; it may have taken arbitrarily long.
Do not renew a retention deadline on a new claim. A never-dispatched operation may start
at any age. A crash can occur after any durable write or provider effect; a restarted
worker must use persisted evidence. Unknown outcomes stay recoverable, not terminal failures.

An uncaught process-level exception (for example a test's BaseException simulating a crash)
may propagate. Once recorded as dispatched, an operation remains recoverable after that
exception. Expected OutcomeUnknown from lookup or execute returns uncertain if still owned.
An unexpected ordinary exception must propagate without claiming success; preserve evidence.
The provider never calls the service in production, but tests can reenter run during calls
to model another worker progressing while this one is blocked. Call completion itself does
not restore lease authority. SQLite is the only durable service state.
