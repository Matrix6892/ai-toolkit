# Recovery and operations

The catalog transaction that marks ERASED inserts a destruction receipt.
A receipt contains tenantId, bundleId, keyId and an immutable operation ID.
A key worker polls committed receipts and destroys that exact key.
Key destruction is idempotent by keyId; keys are never recycled.
The worker cannot manufacture receipts or change retention deadlines.
A crash after the ERASED commit leaves the receipt available for retry.
A crash before that commit leaves neither ERASED nor a receipt.
Duplicate execution requests return the stored receipt for an already ERASED bundle.
A failed eligibility check leaves the bundle LIVE and emits no receipt.
Observers can distinguish catalog erasure from completed physical key destruction.
Readers reject ERASED bundles even while physical destruction is pending.
The destruction queue is an optimization; receipt polling is the recovery authority.
Services authenticate with tenant-bound credentials; the issuer signs candidate tickets.
Tickets cannot be edited by clients and are rejected after their catalog-time expiry.
Ticket lifetime is five minutes; worker clocks have no authority over expiry.
A ticket authorizes only its exact bundle ID, key ID and tenant.
Candidate scans and executions may overlap contract amendment requests.
There is no maintenance window that excludes contract changes during erasure.
Audit records preserve the amendment response, ticket ID and destruction receipt.
