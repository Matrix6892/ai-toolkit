# Candidate and execution protocol

The Erasure planner reads a consistent catalog snapshot.
It joins each LIVE bundle to its current project and computes the effective deadline.
If catalog time is at or beyond that deadline, it issues a signed ticket.
Ticket fields: ticketId, tenantId, bundleId, keyId, projectId, rowRevision, expiresAt.
The planner commits no state change and holds no locks after returning.
A ticket can be executed later by any authenticated Erasure worker.
The worker verifies the signature, tenant, bundle ID, key ID and expiry.
Execution opens a transaction and locks the named bundle row.
It compares LIVE state, keyId, projectId and rowRevision with the ticket.
A mismatch rejects the ticket and requires planning again.
On a match it sets state to ERASED and increments rowRevision.
It inserts the destruction receipt in the same transaction, then commits.
The original planning check is the deadline eligibility check for this ticket.
An individual extension or reassignment therefore invalidates an outstanding ticket.
Workers may retry a ticket until it expires or execution yields a terminal result.
The API returns either the committed receipt or an eligibility rejection.
No key destruction starts before a receipt is durably committed.
The planner's snapshot can be old relative to execution; ticket lifetime bounds that age.
