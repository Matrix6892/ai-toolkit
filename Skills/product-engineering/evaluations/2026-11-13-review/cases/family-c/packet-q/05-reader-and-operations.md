# Packet assembly and operational checks
After readiness, the assembler opens one repeatable-read transaction on the primary.
It checks the control row again and loads versions numbered at or below the cutoff.
For each finding it takes the largest eligible event number as the effective state.
An effective unresolved blocking finding marks the referenced preview blocked.
The ledger includes all effective findings, including closed findings with their disposition.
The manifest lists the captured cutoff and each referenced immutable preview digest.
Preview files are fetched by digest and checked before packaging; fetch failure fails the job.
A ZIP and ledger are published together only when all fetches and generation succeed.
A job ID has one final immutable object key; publishing is conditional on no prior result.
The manifest digest and ZIP digest are stored in the completed job record.
Pending jobs can be retried at the same cutoff; a retry must not recapture a newer head.
No worker may turn a timed-out job into success with a reduced set of rows.
The exporter has no source-log read permission; the projection is its data interface.
Operational metrics include source head, durable consumer position and oldest pending job.
A delivery alert means someone should inspect the job; it does not waive its contract.
Replay restores version rows idempotently after a consumer fault.
Unit checks cover reopening, cutoff exclusion, duplicate delivery and immutable downloads.
Platform acceptance covers atomic commits, broker redelivery and immutable object retention.
The architecture review should assess the overall user contract and material tradeoffs.
