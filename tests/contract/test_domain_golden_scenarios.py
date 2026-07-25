import json
from pathlib import Path
from typing import TypedDict, cast

import pytest

from police_thief_p2p.domain import (
    BarrierSet,
    Board,
    Position,
    RolePoints,
    TerminalReason,
    resolve_verified_terminal,
    score_terminal,
    series_tie_awards,
)
from police_thief_p2p.shared.config_models import SharedConfig

pytestmark = pytest.mark.contract
ROOT = Path(__file__).parents[2]


class Scenario(TypedDict, total=False):
    """Typed golden scenario fixture."""

    name: str
    police_position: list[int]
    thief_position: list[int]
    placed_barrier: list[int]
    barriers: list[list[int]]
    completed_steps: int
    technical: bool
    expected_reason: str
    expected_points: dict[str, int]


def _position(value: list[int]) -> Position:
    return Position(value[0], value[1])


def test_all_domain_golden_scenarios_resolve_and_score(
    shared_config: SharedConfig,
) -> None:
    document = json.loads(
        (ROOT / "data/conformance/domain/golden_scenarios.json").read_text(encoding="utf-8")
    )
    scenarios = cast(list[Scenario], document["scenarios"])
    assert {scenario["name"] for scenario in scenarios} == {
        "direct-capture",
        "barrier-capture",
        "corner-enclosure",
        "survival-threshold",
        "technical-loss",
    }
    for scenario in scenarios:
        placed = scenario.get("placed_barrier")
        reason = resolve_verified_terminal(
            board=Board(7),
            police_position=_position(scenario["police_position"]),
            thief_position=_position(scenario["thief_position"]),
            barriers=BarrierSet(frozenset(_position(value) for value in scenario["barriers"])),
            completed_steps=scenario["completed_steps"],
            survival_threshold=35,
            max_steps=35,
            placed_barrier=_position(placed) if placed is not None else None,
            technical=scenario.get("technical", False),
        )
        assert reason is TerminalReason(scenario["expected_reason"]), scenario["name"]
        assert score_terminal(reason, shared_config.scoring) == RolePoints(
            **scenario["expected_points"]
        )

    tie = document["series_tie"]
    assert tie["tie_score"] == 2
    assert series_tie_awards(tie["total_a"], tie["total_b"]) == tuple(tie["expected_awards"])
