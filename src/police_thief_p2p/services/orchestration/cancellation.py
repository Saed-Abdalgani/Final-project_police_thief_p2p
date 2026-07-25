"""Cooperative cancellation shared by bounded orchestration work."""

from threading import Event


class CancellationToken:
    """Thread-safe cancellation signal for strategy, LLM, transport, and reports."""

    __slots__ = ("_event",)

    def __init__(self) -> None:
        """Create a non-cancelled token."""
        self._event = Event()

    def cancel(self) -> None:
        """Request cooperative cancellation."""
        self._event.set()

    def cancelled(self) -> bool:
        """Return whether cancellation was requested."""
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        """Fail the current cooperative work unit after cancellation."""
        if self.cancelled():
            raise RuntimeError("operation cancelled")
