# Jar Registry integration notes
Owner: Collections Platform
Audience: Assay Gateway and Dispatch maintainers
Revision: pilot schema freeze

## Registry model
An accession row holds species, collection location and harvest date.
A jar row holds jar_id, accession_id, generation, shelf and lifecycle.
The unique identity of a physical state is (jar_id, generation).
Generation is monotonic for a jar and cannot be reset by staff.
A jar lifecycle is STORED, RESERVED or DISPATCHED.
Reservations are short-lived exclusive work leases on one jar.
A lease is acquired only while the jar is STORED.
A completed shipment moves the jar allocation out of available stock.
Partial shipments leave the remainder in the same sealed state until opened.
This document does not specify remaining-seed accounting after the draw.
The eligibility decision precedes opening for the authorized shipment.

## Intake transaction
Create the accession if it does not already exist.
Create each physical jar separately with generation 1.
Commit the jar row and its JarSealed outbox record together.
The outbox is a durable queue record committed with the business row.
Delivery workers may send one outbox record more than once.
Consumers identify duplicates by event_id.
No transaction spans the registry and the laboratory.

## Opening and resealing
The operator scans the jar before opening its lid.
Registry acquires the same exclusive work lease used by dispatch.
The opening transaction increments generation and records the operator.
It writes a JarResealed event with the new generation in the same commit.
Release of the work lease happens after that commit.
A failed opening transaction is retried before the physical jar is returned.
The collection handling procedure blocks shelving unrecorded opened material.
The pilot assumes staff follow that procedure.
A separate supervisor handles broken scanners and unsafe physical material.

## Moving material
A replacement physical jar is created with a fresh identity.
The old jar is marked unavailable while material is transferred.
Lineage records source_jar_id and source_generation for research traceability.
Lineage is not an assay coverage relationship.
Moving a sealed jar updates shelf only.
A shelf event has no biological meaning for assay coverage.

## Assay sample registration
The operator obtains a sample ID before drawing through the port.
The registration transaction snapshots jar_id and current generation.
It also records accession_id as a display field for lab paperwork.
The sample record is immutable after the draw is accepted.
The pilot permits at most one registered assay sample per jar generation.
The port draw is protected by the jar work lease.
The sample is labelled with sample_id, jar_id and generation.
A sample cannot silently follow a jar across a later reseal.
A registration failure prevents the lab handoff.

## Registry read interfaces
GET /jars/{id} returns current generation and lifecycle.
GET /samples/{id} returns the immutable sample snapshot.
Batch list reads may come from an asynchronously updated display replica.
The reservation interface uses the primary registry state.
The work lease token identifies one jar and one acquisition.
An expired token cannot create a dispatch ticket.

## Events
JarSealed includes event_id, jar_id, accession_id and generation.
JarResealed includes the same fields plus operator_id.
SampleDrawn includes event_id and sample_id.
The committed sample record is the authority for the draw's coordinates.
Consumers may receive JarResealed after a later laboratory result.
Per-source retries preserve payload bytes, not global arrival order.
No cross-source ordering is promised.

## Retention
Jar and sample histories are retained throughout the pilot.
Accession records may be corrected for taxonomy without changing sample snapshots.
An accession merge keeps the old accession IDs as aliases.
Jar IDs and generations survive an accession merge unchanged.
Deleting an accession alias must not delete assay evidence.

## Recovery
The outbox relay restarts from its last acknowledged record.
Duplicates can be delivered after the consumer has committed its own state.
Registry backups include jar rows, generations, samples and outbox rows.
A restore is performed while dispatch is stopped by the operator runbook.
No mixed pre-restore and post-restore state is served during that window.
Restoring one service independently during active dispatch is unsupported.

## Dependencies
Registry does not interpret positive or negative assay values.
The lab cannot change jar generation through any integration endpoint.
Display exports are useful for stock planning but cannot reserve work.
Dispatch reservations serialize physical handling of a single jar.
The registry permits reservations for jars currently on biological hold.
Eligibility remains the dispatch application's responsibility.
