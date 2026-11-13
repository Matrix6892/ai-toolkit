# Catalog and ownership

Catalog rows are held in one durable transactional database.
Project: tenantId, projectId, policyRevision, retainUntil.
Bundle: tenantId, bundleId, projectId, rowRevision, state, ownRetainUntil, keyId.
The project ID in a bundle is an exact foreign key in the same tenant.
A project row is retained while any associated bundle or destruction receipt exists.
The Policy process owns project deadline changes.
The Inventory process owns bundle registration, individual extensions and reassignment.
The Erasure process owns the LIVE-to-ERASED transition.
Each process has only the database operations described in this packet.
A registration transaction reads the current project row and inserts a LIVE bundle.
An individual extension transaction increases ownRetainUntil and rowRevision.
Reassignment locks the source project, destination project and bundle together.
It changes projectId and increments rowRevision in that transaction.
It also raises ownRetainUntil to the maximum of its prior value and the source deadline.
Therefore reassignment cannot discard a previously accepted retention obligation.
Registering, extending or reassigning an ERASED bundle is rejected.
Database transactions expose all their writes together, or expose none.
Locks named in an operation stay held through its commit.
A transaction reading a locked row waits and then reads its committed value.
