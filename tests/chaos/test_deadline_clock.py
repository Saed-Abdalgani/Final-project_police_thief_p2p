import pytest

from police_thief_p2p.adapters.system.clocks import FakeClock

pytestmark = pytest.mark.chaos


def test_fake_deadline_campaign_never_sleeps_or_moves_backward() -> None:
    clock = FakeClock()
    deadline = clock.monotonic() + 30
    for increment in (1, 4, 10, 15):
        clock.advance(increment)
    assert clock.monotonic() == deadline
    with pytest.raises(ValueError, match="backward"):
        clock.advance(-1)
