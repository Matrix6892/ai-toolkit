# Provider guarantees

`execute(key: str, amount: int, deadline: float) -> str` returns a nonempty receipt.
Within the window `clock() < deadline`, every execution with identical key, amount and
deadline returns the same committed receipt if one exists, never creating another effect.
The provider does not fence service lease generations. Deadlines supplied for a key must
never change. The first dispatch chooses a 30-second retention window. After that window
provider storage may be purged; executing that key again may issue another voucher.

`lookup(key: str, deadline: float) -> Observation` returns:
- found, receipt: proof of a committed effect; valid even after deadline if still retained.
- absent, None: linearizable absence at lookup time, safe to retry only before deadline.
- expired, None: history unavailable; absence of an effect is not established.
Lookup never issues a voucher. It may raise OutcomeUnknown when temporarily unavailable.

execute may raise OutcomeUnknown before OR after committing an effect; its message does
not distinguish the cases. DefinitelyRejected means a permanent rejection with no effect
for this key; it occurs only when no prior effect exists for the key. If an effect already
exists in the retention window, execute returns its receipt instead. Ordinary unexpected
exceptions provide no stronger evidence than a crash. Calls can block across lease/window
expiry. There is no cancellation, global transaction with SQLite, or permanent deduplication.
