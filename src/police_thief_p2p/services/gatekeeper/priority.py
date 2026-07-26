"""Bounded priority/concurrency admission with explicit backpressure."""

import asyncio
import heapq
from dataclasses import dataclass, field
from enum import StrEnum


class AdmissionOutcome(StrEnum):
    """Queue admission result."""

    ACQUIRED = "acquired"
    REJECTED_BACKPRESSURE = "rejected-backpressure"


@dataclass(order=True, slots=True)
class _Waiter:
    priority: int
    sequence: int
    future: asyncio.Future[None] = field(compare=False)


class PrioritySemaphore:
    """Limit active calls and wake bounded waiters in priority/FIFO order."""

    __slots__ = ("_active", "_capacity", "_limit", "_lock", "_sequence", "_waiters")

    def __init__(self, *, limit: int, queue_capacity: int) -> None:
        """Create positive concurrency and queue ceilings."""
        if limit < 1 or queue_capacity < 1:
            raise ValueError("priority semaphore limits are invalid")
        self._limit = limit
        self._capacity = queue_capacity
        self._active = 0
        self._sequence = 0
        self._waiters: list[_Waiter] = []
        self._lock = asyncio.Lock()

    @property
    def active(self) -> int:
        """Return current provider concurrency."""
        return self._active

    @property
    def queued(self) -> int:
        """Return current bounded wait depth."""
        return len(self._waiters)

    async def acquire(self, priority: int) -> AdmissionOutcome:
        """Acquire immediately, queue by priority, or reject with backpressure."""
        future: asyncio.Future[None] | None = None
        async with self._lock:
            if self._active < self._limit and not self._waiters:
                self._active += 1
                return AdmissionOutcome.ACQUIRED
            if len(self._waiters) >= self._capacity:
                return AdmissionOutcome.REJECTED_BACKPRESSURE
            self._sequence += 1
            future = asyncio.get_running_loop().create_future()
            heapq.heappush(self._waiters, _Waiter(priority, self._sequence, future))
        try:
            await future
        except BaseException:
            async with self._lock:
                self._waiters = [item for item in self._waiters if item.future is not future]
                heapq.heapify(self._waiters)
            raise
        return AdmissionOutcome.ACQUIRED

    async def release(self) -> None:
        """Release one slot and wake the highest-priority oldest waiter."""
        async with self._lock:
            while self._waiters:
                waiter = heapq.heappop(self._waiters)
                if not waiter.future.cancelled():
                    waiter.future.set_result(None)
                    return
            self._active -= 1
            if self._active < 0:
                raise RuntimeError("priority semaphore released without acquire")
