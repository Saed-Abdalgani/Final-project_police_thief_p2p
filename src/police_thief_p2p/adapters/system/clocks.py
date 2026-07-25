"""System and deterministic fake clock adapters."""

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


class SystemClock:
    """Use operating-system monotonic and UTC clocks."""

    __slots__ = ()

    def monotonic(self) -> float:
        """Return the system monotonic clock."""
        return time.monotonic()

    def utc_now(self) -> datetime:
        """Return the current timezone-aware UTC timestamp."""
        return datetime.now(UTC)


@dataclass(slots=True)
class FakeClock:
    """Advance deterministic deadlines without sleeping."""

    start_utc: datetime = field(default_factory=lambda: datetime(2026, 1, 1, tzinfo=UTC))
    _monotonic: float = 0.0

    def __post_init__(self) -> None:
        """Reject ambiguous naive timestamps."""
        if self.start_utc.tzinfo is None:
            msg = "start_utc must be timezone-aware"
            raise ValueError(msg)

    def monotonic(self) -> float:
        """Return deterministic monotonic time."""
        return self._monotonic

    def utc_now(self) -> datetime:
        """Return deterministic UTC time."""
        return self.start_utc + timedelta(seconds=self._monotonic)

    def advance(self, seconds: float) -> None:
        """Advance both views of time by a non-negative duration."""
        if seconds < 0:
            msg = "clock cannot move backward"
            raise ValueError(msg)
        self._monotonic += seconds
