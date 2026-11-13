# Source and service contracts
The review command API appends one accepted mutation to a museum's ordered event log.
A successful response means the event and its incrementing number are durable.
An append includes museum, guide, immutable preview digest, finding ID and complete new state.
Closing or reopening a finding produces a new event; no prior event is overwritten.
The event log starts at 1; museums do not share event-number sequences.
Reading the head and accepting an export request occur in one source transaction.
No subsequent review command can be numbered at or below the captured head.
The broker delivers each museum in number order and at least once.
Delivery order describes callbacks submitted to the consumer, not when their work finishes.
A worker pool may process callbacks concurrently, including different guides in one museum.
Broker acknowledgement occurs only after the local persistence transaction commits.
Redelivery after a lost acknowledgement is possible; event number is an idempotency key.
Log events remain replayable for a year; packet jobs are limited to this retention period.
Preview storage uses SHA-256 object names, verifies bytes and refuses overwrite.
A successful preview upload is readable immediately by its digest in the storage region.
All accepted review commands reference successfully uploaded previews.
Objects referenced by accepted reviews or retained packets remain pinned for their lifetime.
Storage has no mutable 'latest preview' link in the export path.
These contracts are supplied by the internal platform team, not inferred from dashboards.
