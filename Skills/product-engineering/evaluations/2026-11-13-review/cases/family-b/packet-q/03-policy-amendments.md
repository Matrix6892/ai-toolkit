# Contract amendment interface

PUT /projects/{id}/retention accepts deadline and expectedPolicyRevision.
The tenant is derived from the authenticated service identity.
The request is successful only after the following transaction commits.
The Policy process locks the project row and reads its current revision.
It rejects an unexpected revision with 409 and the current revision.
It rejects a deadline earlier than the stored deadline with 422.
It increases retainUntil and policyRevision in the same project-row transaction.
A repeated deadline is accepted and still advances policyRevision.
The transaction updates no bundle rows.
The response contains the committed project revision and deadline.
No external acknowledgement is needed to make that amendment effective.
A transport timeout is an unknown result; the caller reads the project before retrying.
The API supports a stable request ID with a durable stored response for exact retries.
Stored responses are tenant scoped and committed with the project update.
Notifications feed dashboards and deadline indexes after commit.
Notifications can be duplicated, delayed or delivered out of order.
Dashboard consumers retain the largest observed policyRevision.
The deadline index helps find candidates but never authorizes destruction.
Policy service rollback does not roll back a committed amendment.
