# Boreal research archive: retention service

This is a synthetic design packet for an internal architecture review.
Boreal stores encrypted research bundles for customer projects.
Each bundle has its own independently erasable encryption key.
A project contract supplies a minimum retention deadline.
A bundle may also carry a later individually negotiated deadline.
The effective deadline is the maximum of those two deadlines.
Only LIVE bundles participate in retention and contract amendments.
A bundle stops being LIVE when its catalog state becomes ERASED.
That transition is the irreversible destruction decision; readers then lose access.
The key worker completes physical destruction after that decision.
A successful contract extension applies to every bundle LIVE at its commit point.
After accepting an extension, no such bundle may transition to ERASED before its new effective deadline.
An extension need not restore bundles already ERASED before its commit point.
Contract shortening is outside this release; extensions only increase deadlines.
Catalog time is authoritative and nondecreasing; clients cannot supply it.
An ERASED bundle cannot be restored or reused under the same bundle ID.
Tenants cannot address another tenant's projects or bundles.
Review the specified behavior and the proposed process boundaries.
Capacity forecasts and the implementation language are outside this review.
