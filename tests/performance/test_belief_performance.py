import json
import time
from pathlib import Path

import pytest

from police_thief_p2p.domain import BarrierSet, Board, Position
from police_thief_p2p.services.belief.evidence import verify_scent_reveal
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.belief.reliability import HintReliability
from police_thief_p2p.services.belief.service import BeliefService
from tests.helpers.belief import make_scent_frame, make_scent_reveal

pytestmark = [pytest.mark.performance, pytest.mark.no_cover]
RESULT = Path(__file__).parents[2] / "results/benchmarks/m6_belief.json"


@pytest.mark.parametrize("size", [7, 15])
def test_35_step_belief_update_budget(size: int) -> None:
    cells = tuple(
        (row, col, "0.100000") for row in range(min(5, size)) for col in range(min(5, size))
    )
    frame = make_scent_frame(size, cells)
    evidence = verify_scent_reveal(frame, make_scent_reveal(frame))
    service = BeliefService()
    belief = BeliefGrid.uniform(Board(size))
    started = time.perf_counter()
    for _ in range(35):
        belief = service.update(
            belief,
            evidence,
            barriers=BarrierSet(),
            hint="near the center",
            observer_position=Position(0, 0),
            reliability=HintReliability(),
        ).belief
    elapsed = time.perf_counter() - started
    assert elapsed < 2.0


def test_stored_belief_p95_campaign_passes() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    measurements = result["measurements"]
    gates = result["gates"]
    assert measurements["belief_35_steps_7x7"]["p95_ms"] < gates["belief_35_steps_7x7_p95_max_ms"]
    assert (
        measurements["belief_35_steps_15x15"]["p95_ms"] < gates["belief_35_steps_15x15_p95_max_ms"]
    )
    assert result["method"]["updates_per_sample"] == 35
    assert gates["result"] == "PASS"
