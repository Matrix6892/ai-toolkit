# Position tracking and export admission
The durable position is the highest persisted event number for this museum.
Let R be event numbers whose version rows are committed in the database.
Position is max(R), or zero when no version rows have been committed.
The worker locks the museum control row before updating position in its transaction.
After inserting its event row it sets position to max(position, its event number).
Position therefore never moves backward when workers complete their callbacks.
Read-committed isolation and the row lock serialize these position updates.
The transaction commits the inserted row and new position together.
Position is not derived from in-memory broker delivery or an acknowledgement counter.
A separate per-worker queue tracks unfinished callbacks for normal broker redelivery.
Callback queue contents are not queried by the exporter or included in the control row.
An export job with cutoff B waits until durable position is at least B.
No broker delivery number or client activity counter admits a packet.
The activity strip uses the same highest committed event number as its recency value.
That value lets the strip display newly handled work while an earlier callback is pending.
The per-museum lock is accepted: current peak is 15 mutations per second per museum.
The update is constant-space and requires no scan of review history.
Source and broker replay remain recovery mechanisms, not fallback packet inputs.
If a worker stalls, its callback stays owned until recovery or eventual redelivery.
