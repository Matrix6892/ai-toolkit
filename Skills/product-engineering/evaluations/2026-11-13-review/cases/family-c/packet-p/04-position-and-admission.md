# Position tracking and export admission
The durable position is the largest contiguous persisted prefix for this museum.
Let R be event numbers whose version rows are committed in the database.
Position is the greatest n for which every number from 1 through n belongs to R.
The worker locks the museum control row before updating position in its transaction.
After inserting its event row it scans from position+1 until the first missing number.
It advances position only across rows visible in that transaction, including its own row.
Read-committed isolation and the row lock serialize these position updates.
For this calculation the scan uses a fresh statement snapshot after acquiring the lock.
If another worker's row is uncommitted, the scan stops; that worker later advances it.
The transaction commits the inserted row and new position together.
Position can lag persisted rows separated from it by a gap; this is expected.
An export job with cutoff B waits until durable position is at least B.
No broker delivery number, activity counter or maximum observed number admits a packet.
A separate activity-strip value is the highest committed event number, not this position.
That value lets the strip display newly handled work while an earlier callback is pending.
The added per-museum lock is accepted: current peak is 15 mutations per second per museum.
The transaction scans only newly contiguous rows; it does not scan full review history.
Source and broker replay remain recovery mechanisms, not fallback packet inputs.
If a worker stalls, exports wait and the activity strip may continue to move.
