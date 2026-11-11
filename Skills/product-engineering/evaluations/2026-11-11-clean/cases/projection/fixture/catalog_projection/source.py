"""Wire shapes for the inventory service journal. See SOURCE_CONTRACT.md."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Event:
    item_id: str
    generation: int
    revision: int
    kind: str
    title: str | None = None
    quantity: int | None = None

@dataclass(frozen=True)
class Page:
    events: tuple[Event, ...]
    next_cursor: str
    done: bool

class Source(Protocol):
    def read(self, after: str | None) -> Page: ...
