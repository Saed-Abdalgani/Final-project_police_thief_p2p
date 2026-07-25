from datetime import UTC, datetime

import pytest

from police_thief_p2p.adapters.system.clocks import FakeClock, SystemClock
from police_thief_p2p.services.ports import ClockPort


def test_system_clock_satisfies_port_and_returns_aware_utc() -> None:
    clock = SystemClock()
    assert isinstance(clock, ClockPort)
    assert clock.monotonic() >= 0
    assert clock.utc_now().tzinfo is UTC


def test_fake_clock_advances_without_sleeping() -> None:
    start = datetime(2026, 7, 25, tzinfo=UTC)
    clock = FakeClock(start_utc=start)

    clock.advance(3.5)

    assert clock.monotonic() == 3.5
    assert (clock.utc_now() - start).total_seconds() == 3.5
    assert isinstance(clock, ClockPort)


def test_fake_clock_rejects_backward_and_naive_time() -> None:
    clock = FakeClock()
    with pytest.raises(ValueError, match="backward"):
        clock.advance(-0.01)
    with pytest.raises(ValueError, match="timezone-aware"):
        FakeClock(start_utc=datetime(2026, 7, 25))
