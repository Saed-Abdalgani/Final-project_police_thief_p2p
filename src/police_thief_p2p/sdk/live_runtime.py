"""Thread-safe bounded live snapshot delivery and lifecycle ports."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import Event, Lock, Thread
from typing import Protocol

from police_thief_p2p.sdk.live_view import LocalView, ViewStatus


class LifecycleCommand(StrEnum):
    """Operator lifecycle commands accepted by the SDK."""

    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    RESTART = "restart"
    QUIT = "quit"


class LifecyclePort(Protocol):
    """Application-owned lifecycle controller hidden behind the SDK."""

    def execute(self, command: LifecycleCommand) -> None:
        """Execute one validated lifecycle command."""


class SnapshotChannel:
    """Bounded latest-value channel that preserves essential snapshots."""

    __slots__ = ("_items", "_lock", "_max_size")

    def __init__(self, max_size: int = 8) -> None:
        """Create a channel with a strict positive bound."""
        if type(max_size) is not int or max_size < 2:
            raise ValueError("snapshot channel size must be at least two")
        self._items: deque[LocalView] = deque()
        self._lock = Lock()
        self._max_size = max_size

    def publish(self, snapshot: LocalView) -> None:
        """Publish one immutable snapshot, coalescing visuals under pressure."""
        if not isinstance(snapshot, LocalView):
            raise TypeError("snapshot channel accepts LocalView only")
        essential = snapshot.final or snapshot.status in {ViewStatus.TERMINAL, ViewStatus.ERROR}
        with self._lock:
            if len(self._items) >= self._max_size:
                disposable = next(
                    (
                        index
                        for index, item in enumerate(self._items)
                        if not item.final
                        and item.status not in {ViewStatus.TERMINAL, ViewStatus.ERROR}
                    ),
                    None,
                )
                if disposable is not None:
                    del self._items[disposable]
                elif not essential:
                    return
                else:
                    self._items.popleft()
            self._items.append(snapshot)

    def drain_latest(self) -> LocalView | None:
        """Return the newest snapshot and coalesce superseded intermediates."""
        with self._lock:
            if not self._items:
                return None
            latest = next(
                (
                    item
                    for item in reversed(self._items)
                    if item.final or item.status in {ViewStatus.TERMINAL, ViewStatus.ERROR}
                ),
                self._items[-1],
            )
            self._items.clear()
            return latest

    def pending(self) -> int:
        """Return bounded queue depth for diagnostics."""
        with self._lock:
            return len(self._items)


@dataclass(frozen=True, slots=True)
class LiveWorker:
    """Background gameplay worker and cooperative stop handle."""

    thread: Thread
    stop_event: Event

    def stop(self) -> None:
        """Request cooperative worker shutdown."""
        self.stop_event.set()

    def join(self, timeout: float = 5.0) -> None:
        """Wait a bounded time for worker shutdown."""
        self.thread.join(timeout)


def start_live_worker(
    target: Callable[[Callable[[LocalView], None], Event], None],
    channel: SnapshotChannel,
) -> LiveWorker:
    """Run gameplay work outside the caller/Tk thread."""
    stop_event = Event()
    thread = Thread(
        target=target,
        args=(channel.publish, stop_event),
        name="police-thief-gameplay",
        daemon=True,
    )
    thread.start()
    return LiveWorker(thread, stop_event)
