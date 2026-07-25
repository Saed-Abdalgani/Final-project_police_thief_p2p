"""Clock abstraction for deterministic deadlines and timestamps."""

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class ClockPort(Protocol):
    """Provide monotonic deadlines and timezone-aware UTC timestamps."""

    def monotonic(self) -> float:
        """Return a monotonic time value in seconds."""
        ...

    def utc_now(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        ...
