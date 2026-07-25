import time

import pytest

from police_thief_p2p import SimulationSdk

pytestmark = pytest.mark.performance


def test_foundation_readiness_has_negligible_local_overhead() -> None:
    sdk = SimulationSdk()
    started = time.perf_counter()
    for _ in range(1_000):
        assert sdk.check_readiness().is_ready
    assert time.perf_counter() - started < 1.0
