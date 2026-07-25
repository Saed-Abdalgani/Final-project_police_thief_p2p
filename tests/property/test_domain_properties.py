import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from police_thief_p2p.domain import (
    Action,
    Board,
    Direction,
    GameRules,
    LocalGameState,
    Position,
    Role,
    initial_local_state,
    transition,
)
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.coordinates import CoordinateTransform, OriginCorner

ROOT = Path(__file__).parents[2]
BASE = json.loads((ROOT / "config/shared/game.example.json").read_text(encoding="utf-8"))


@settings(max_examples=10_000, deadline=None)
@given(
    size=st.integers(1, 30),
    row_seed=st.integers(0, 10_000),
    col_seed=st.integers(0, 10_000),
    role=st.sampled_from(list(Role)),
    action_seed=st.integers(0, 10_000),
)
def test_legal_action_closure_and_state_invariants_over_10000_examples(
    size: int,
    row_seed: int,
    col_seed: int,
    role: Role,
    action_seed: int,
) -> None:
    position = Position(row_seed % size, col_seed % size)
    state = LocalGameState(
        role=role,
        position=position,
        rules=GameRules(Board(size), 100, 20_000, 20_000),
        visited=frozenset({position}),
    )
    legal = state.legal_actions()
    action = legal[action_seed % len(legal)]
    result = transition(state, action)
    assert result.state.rules.board.contains(result.state.position)
    assert result.state.position in result.state.visited
    assert result.state.step_number == 1
    assert result.state.barriers_placed <= result.state.rules.max_barriers
    if action.action_type.value == "BARRIER":
        assert action.target is not None
        assert action.target in result.state.public_barriers


def test_origin_and_index_metamorphism_preserves_normalized_transition() -> None:
    expected_police = Position(0, 0)
    expected_thief = Position(3, 3)
    normalized_results: list[tuple[Position, Position, Position]] = []
    for origin in OriginCorner:
        for start_index in (0, 1):
            value = json.loads(json.dumps(BASE))
            board = value["board_and_agents"]
            board["axis_origin_corner"] = origin.value
            board["axis_start_index"] = start_index
            transform = CoordinateTransform(7, origin, start_index)
            board["cop_start"] = list(transform.from_canonical(expected_police))
            board["thief_start"] = list(transform.from_canonical(expected_thief))
            config = SharedConfig.model_validate(value)
            police = initial_local_state(config, Role.POLICE)
            thief = initial_local_state(config, Role.THIEF)
            moved = transition(police, Action.move(Direction.SOUTH)).state
            normalized_results.append((police.position, thief.position, moved.position))
    assert set(normalized_results) == {(expected_police, expected_thief, Position(1, 0))}
