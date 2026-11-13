# Assay Gateway exchange agreement
Owner: Laboratory Integrations
Status: pilot implementation design
Counterparty: Northbank partner laboratory

## Incoming result
The laboratory posts result_id, sample_id, outcome and signed_at.
Outcome is NEGATIVE or POSITIVE.
The signed payload identifies the immutable sample drawn by collection staff.
A valid signature authenticates the laboratory, not current eligibility.
The gateway resolves sample_id against Registry before accepting the result.
Unknown sample IDs go to an operator queue and do not update eligibility.
Network failures leave the message unacknowledged for retry.
The gateway stores the original signed payload for the pilot retention period.

## Duplicate handling
result_id is a laboratory-wide unique immutable identifier.
Resending an accepted result is acknowledged without creating a second result.
A changed payload using an existing result_id is quarantined for staff.
A second final result for one sample is treated as a conflict.
Conflicts are visible to collection staff before further automated processing.
The scenarios below use a single uncontested final result per sample.
The laboratory provides no accession-wide certification endpoint.

## Local projection
The gateway maintains accession_clearance keyed by accession_id.
A NEGATIVE result sets that accession clearance to RELEASED.
A POSITIVE result sets that accession clearance to HELD.
The row retains the source sample_id and an increasing projection revision.
jar_id and sampled generation remain in the receipt history.
They are not dimensions of accession_clearance.
An accession with no row is treated as HELD.

## Delivery semantics
Receipt and local projection update commit atomically in the gateway database.
The gateway's outgoing outbox record is committed in that same transaction.
A timeout after commit may cause an incoming result to be retried.
The duplicate rule prevents another local update for that result.
Outgoing event delivery is at least once and may be delayed.
Dispatch can be offline while the laboratory continues posting results.
The gateway reports queue delay in its operator dashboard.

## Registry events
JarSealed and JarResealed are consumed to reset accession_clearance to HELD.
The reset resolves the jar's accession and increments the projection revision.
Reset and receipt updates are processed in local arrival order.
The row lock serializes simultaneous handlers for the same accession.
There is no comparison of a result's sampled generation with current generation.

## Interface for Dispatch
GET /clearance/{accession_id} returns HELD or RELEASED and projection revision.
The response includes the source sample_id for audit.
The endpoint reads the committed gateway database, not a replica.
It does not accept a jar_id or generation argument.
Gateway clients can subscribe to matching ClearanceChanged snapshots.

## Scientific audit display
The accession page lists every sample under its collection identity.
Every row shows sample_id, jar_id, sampled generation and outcome.
The display retains old results after a jar has been resealed.
Rows from different jars may appear next to each other in the same timeline.
The display includes a notice to inspect physical scope before interpreting results.
A timeline is not itself a ticket-authorizing API.

## Failure handling
A failed registry sample lookup prevents result acceptance.
A signature failure records a rejected envelope with its reason.
Outbox transmission failures retry the original committed record.
Read failures in Dispatch are surfaced as an eligibility-unavailable message.
Operators do not rewrite an assay outcome to clear an integration failure.
No scheduled timeout converts an unanswered sample to NEGATIVE.

## Access and maintenance
The laboratory credential can submit results but cannot edit sample registration.
Collection staff can inspect payloads but cannot forge laboratory signatures.
Gateway maintainers can replay retained outgoing events after an outage.
Replay preserves event_id and the original projection revision.
Projection state can be rebuilt from retained receipts and registry events.
The normal rebuild procedure stops new dispatch until the consumer catches up.
A mid-rebuild display is labelled unavailable to dispatch clients.

## Pilot examples
A negative result for sample S-A updates the row for accession NB-71.
The accession page still shows that S-A was drawn from J-A generation 1.
A later reseal event resets the row even if the assay receipt stays visible.
A new result arriving after that reset runs the ordinary receipt update.

## Open policy items
The laboratory may later add a second assay for a different fungus species.
How multiple assay kinds combine is not decided by this pilot.
The current protocol accepts only the single configured viable-fungus assay.
Long-term expiry of a negative assay is also not defined here.
No automatic expiry is applied within the spring pilot interval.
These questions require Collection Services approval before expanding the protocol.

## Verification notes
Contract examples are exercised with fixed sample and jar identities.
Receipt replay must not multiply the number of assay records.
Failed lookups must not create partial local projection rows.
A registry outage must prevent acceptance of unknown sample coordinates.
The signed_at timestamp is for audit and is never an ordering fence.
Clock synchronization is monitored but is not needed for the pilot's ordering rule.
