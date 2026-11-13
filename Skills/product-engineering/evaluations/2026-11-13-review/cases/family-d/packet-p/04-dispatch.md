# Research dispatch: eligibility and ticket design
Owner: Research Fulfilment
Status: pilot implementation design
Applies to seed jars selected for an institute request

## Request lifecycle
An institute asks for seed from an accession and specifies quantity.
Allocation chooses a physical jar before eligibility is checked.
The picker scans that jar's label at the storage station.
A request can try another jar when its first choice remains on hold.
A ticket records request_id, jar_id, generation and the picking operator.
Dispatch tickets are unique per request allocation attempt.

## Work reservation
Dispatch acquires the registry work lease for the chosen jar.
The lease freezes generation while Dispatch makes its decision and draws seed.
Repacking, sample draws and dispatch work all compete for that same lease.
The lease holder reads the primary registry row after acquiring the lease.
A primary read includes the current generation and lifecycle.
Failure to acquire or renew the lease stops ticket creation.
A ticket is committed before the authorized draw starts.
The application checks the lease is still valid before committing the ticket.
A completed draw releases the lease after updating allocation state.

## Eligibility source
Dispatch stores a local copy of each ClearanceChanged snapshot by accession_id.
The copy keeps HELD or RELEASED, revision and the source sample_id.
It applies a snapshot only if its revision exceeds the stored revision.
A missing local row means HELD.
The local row is the authority used for biological eligibility.
No synchronous gateway call is made during a pick.

## Ticket transaction
After reserving the jar, look up its current accession_id in local clearance.
A RELEASED row allows the ticket transaction to commit.
HELD or missing rows reject the attempt.
Record the jar's current generation and the local clearance revision in the ticket.
The transaction does not resolve the source sample coordinates.
A later clearance change does not revoke an already committed draw.

## Asynchronous delivery
Events are complete snapshots with increasing gateway revisions per accession.
Dispatch preserves the greatest observed revision for each accession.
Jar Registry events go to Gateway; Dispatch does not consume them directly.
The gateway outbox can be delayed independently of registry work.
A valid registry lease does not wait for gateway queue delivery.

## Picker response
A held jar is shown with a reason and the last sample reference when available.
An unavailable lookup is shown as retry later and cannot create a ticket.
The interface groups available stock by accession for scientific relevance.
The picker still scans and reserves one physical jar for every ticket.
Displayed cached stock counts do not themselves authorize a ticket.
The print service receives only already committed dispatch tickets.
A print retry reuses the ticket ID and cannot create a new decision.

## Recovery and idempotency
request_allocation_id is the idempotency key for ticket creation.
A retry returns the existing ticket if its first transaction committed.
It does not reallocate a different physical jar under that same key.
A lease lost before ticket commit produces no ticket.
The retry acquires a fresh lease and rereads the registry.
A ticket already used for a draw is not replayed as another draw.
The storage station records completed draws by ticket ID.

## Ownership boundary
Collection Services defines which biological evidence is sufficient.
Gateway authenticates and stores laboratory evidence and its projection.
Registry serializes physical state transitions and supplies current coordinates.
Dispatch is accountable for refusing a ticket without sufficient evidence.
No request urgency field bypasses the eligibility predicate.
Manual overrides are not part of the automated pilot implementation.

## Observability
Each decision log contains jar_id and current generation from Registry.
It also includes the evidence or projection revision used for the decision.
A refused decision logs its cause without exposing recipient contact details.
The dashboard separates assay holds, lookup failures and depleted quantities.
Logs make replay ordering diagnosable after an integration incident.
No alert receipt changes eligibility state.

## Operational exercises
Exercise a negative assay followed by a shelf transfer and a successful pick.
Exercise duplicate event delivery and ensure the same revision is retained.
Exercise unknown accessions and ensure a missing clearance row refuses a pick.
Exercise gateway outage while existing local clearance rows remain readable.

## Assumptions
Handling staff obey the scan-before-opening procedure in Registry notes.
A valid gateway response is trusted within the authenticated service network.
The assay itself is assumed scientifically valid for its sampled coordinates.
Neither queue latency nor eventual consistency has a fixed maximum here.
A result from an unconfigured assay kind is rejected before eligibility update.
Physical seed-count discrepancies require a separate stock reconciliation.
The scope of this document is the biological dispatch decision.

## Review questions recorded for later
Future overseas recipients may require destination-specific certificates.
No such certificate policy is specified or inferred in the spring pilot.
Whether assay evidence should expire after the spring interval is undecided.
Longer retention and multi-assay dispatch rules need a later design revision.
