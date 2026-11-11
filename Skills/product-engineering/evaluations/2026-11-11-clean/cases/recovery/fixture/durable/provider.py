from dataclasses import dataclass

class OutcomeUnknown(Exception):
    """The caller cannot tell whether an effect was committed."""

class DefinitelyRejected(Exception):
    """This call committed no effect; a permanent request rejection."""

@dataclass(frozen=True)
class Observation:
    status: str  # found, absent, expired
    receipt: str | None = None
