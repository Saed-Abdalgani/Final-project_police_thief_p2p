"""Bounded priority work queues with explicit backpressure outcomes."""

import heapq
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum


class WorkPriority(IntEnum):
    """Lower values run first; gameplay/audit outrank optional work."""

    GAMEPLAY = 0
    AUDIT = 1
    REPORTING = 2
    BANTER = 3


class EnqueueOutcome(StrEnum):
    """Explicit queue admission result."""

    ACCEPTED = "accepted"
    REJECTED_BACKPRESSURE = "rejected-backpressure"
    EVICTED_OPTIONAL = "evicted-optional"


@dataclass(order=True, frozen=True, slots=True)
class WorkItem:
    """Stable priority/FIFO work record."""

    priority: WorkPriority
    sequence: int
    kind: str = field(compare=False)
    payload: object = field(compare=False)


class BoundedWorkQueue:
    """Bound memory and preserve critical work by evicting optional tail items."""

    __slots__ = ("_capacity", "_items", "_sequence")

    def __init__(self, capacity: int) -> None:
        """Create a queue with a strict positive entry capacity."""
        if capacity < 1:
            raise ValueError("work queue capacity must be positive")
        self._capacity = capacity
        self._items: list[WorkItem] = []
        self._sequence = 0

    def enqueue(self, priority: WorkPriority, kind: str, payload: object) -> EnqueueOutcome:
        """Admit bounded work or return explicit backpressure."""
        self._sequence += 1
        item = WorkItem(priority, self._sequence, kind, payload)
        if len(self._items) < self._capacity:
            heapq.heappush(self._items, item)
            return EnqueueOutcome.ACCEPTED
        worst = max(self._items)
        if item.priority < worst.priority:
            self._items.remove(worst)
            heapq.heapify(self._items)
            heapq.heappush(self._items, item)
            return EnqueueOutcome.EVICTED_OPTIONAL
        return EnqueueOutcome.REJECTED_BACKPRESSURE

    def dequeue(self) -> WorkItem | None:
        """Return the highest-priority oldest work item."""
        return None if not self._items else heapq.heappop(self._items)

    def __len__(self) -> int:
        """Return current bounded depth."""
        return len(self._items)
