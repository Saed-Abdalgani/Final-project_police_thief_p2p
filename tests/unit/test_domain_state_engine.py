from dataclasses import fields, replace

import pytest

from police_thief_p2p.domain import (
    Action,
    ActionType,
    BarrierPlaced,
    BarrierSet,
    Board,
    Direction,
    GameRules,
    LocalGameState,
    Position,
    Role,
    TerminalReason,
    initial_local_state,
    transition,
)
from police_thief_p2p.shared.config_models import SharedConfig


def _state(
    *,
    role: Role = Role.POLICE,
    position: Position | None = None,
    rules: GameRules | None = None,
    barriers: BarrierSet | None = None,
    barriers_placed: int = 0,
    step_number: int = 0,
    terminal_reason: TerminalReason | None = None,
) -> LocalGameState:
    actual_position = position if position is not None else Position(1, 1)
    return LocalGameState(
        role=role,
        position=actual_position,
        rules=rules if rules is not None else GameRules(Board(3), 2, 5, 4),
        public_barriers=barriers if barriers is not None else BarrierSet(),
        barriers_placed=barriers_placed,
        step_number=step_number,
        visited=frozenset({actual_position}),
        terminal_reason=terminal_reason,
    )


def test_local_state_has_no_opponent_truth_field() -> None:
    names = {field.name for field in fields(LocalGameState)}
    assert names == {
        "role",
        "position",
        "rules",
        "public_barriers",
        "barriers_placed",
        "step_number",
        "visited",
        "terminal_reason",
    }
    assert all("opponent" not in name and "thief_position" not in name for name in names)


def test_role_specific_initial_state_uses_negotiated_starts(
    shared_config: SharedConfig,
) -> None:
    police = initial_local_state(shared_config, Role.POLICE)
    thief = initial_local_state(shared_config, Role.THIEF)
    assert police.position == Position(0, 0)
    assert thief.position == Position(3, 3)
    assert police.public_barriers == thief.public_barriers == BarrierSet()
    assert police.barriers_placed == thief.barriers_placed == 0
    assert police.visited == frozenset({police.position})
    assert thief.visited == frozenset({thief.position})


def test_game_rules_validate_and_derive_from_shared(shared_config: SharedConfig) -> None:
    rules = GameRules.from_shared(shared_config)
    assert rules == GameRules(Board(7), 14, 35, 35)
    with pytest.raises(TypeError, match="integers"):
        GameRules(Board(3), True, 1, 1)
    with pytest.raises(TypeError, match="Board"):
        GameRules("board", 1, 1, 1)  # type: ignore[arg-type]
    for values in ((-1, 1, 1), (0, 0, 1), (0, 1, 0)):
        with pytest.raises(ValueError, match="limits"):
            GameRules(Board(3), *values)


def test_local_state_rejects_invalid_invariants() -> None:
    rules = GameRules(Board(3), 2, 5, 4)
    cases = (
        {"position": Position(3, 0), "visited": frozenset({Position(3, 0)})},
        {"barriers_placed": 3},
        {"step_number": -1},
        {"visited": frozenset({Position(0, 0)})},
        {
            "role": Role.THIEF,
            "public_barriers": BarrierSet(frozenset({Position(1, 1)})),
        },
        {"public_barriers": BarrierSet(frozenset({Position(3, 0)}))},
    )
    for overrides in cases:
        kwargs: dict[str, object] = {
            "role": Role.POLICE,
            "position": Position(1, 1),
            "rules": rules,
            "visited": frozenset({Position(1, 1)}),
        }
        kwargs.update(overrides)
        with pytest.raises(ValueError, match=r".+"):
            LocalGameState(**kwargs)  # type: ignore[arg-type]


def test_local_state_rejects_invalid_runtime_contract_types() -> None:
    position = Position(1, 1)
    rules = GameRules(Board(3), 2, 5, 4)
    common = {"position": position, "rules": rules, "visited": frozenset({position})}
    with pytest.raises(TypeError, match="role"):
        LocalGameState(role="police", **common)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="position"):
        LocalGameState(
            role=Role.POLICE,
            position=(1, 1),  # type: ignore[arg-type]
            rules=rules,
            visited=frozenset({position}),
        )
    with pytest.raises(TypeError, match="rules"):
        LocalGameState(
            role=Role.POLICE,
            position=position,
            rules="rules",  # type: ignore[arg-type]
            visited=frozenset({position}),
        )
    with pytest.raises(TypeError, match="public_barriers"):
        LocalGameState(
            role=Role.POLICE,
            **common,  # type: ignore[arg-type]
            public_barriers=frozenset(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="terminal_reason"):
        LocalGameState(
            role=Role.POLICE,
            **common,  # type: ignore[arg-type]
            terminal_reason="stopped",  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="counters"):
        LocalGameState(
            role=Role.POLICE,
            **common,  # type: ignore[arg-type]
            step_number=True,
        )
    with pytest.raises(TypeError, match="visited"):
        LocalGameState(
            role=Role.POLICE,
            position=position,
            rules=rules,
            visited={position},  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="visited"):
        LocalGameState(
            role=Role.POLICE,
            position=position,
            rules=rules,
            visited=frozenset({position, "bad"}),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="visited cell"):
        LocalGameState(
            role=Role.POLICE,
            position=position,
            rules=rules,
            visited=frozenset({position, Position(3, 0)}),
        )


def test_legal_actions_include_movement_stay_and_police_barriers() -> None:
    police = _state()
    movement = tuple(action for action in police.legal_actions() if action.action_type != "BARRIER")
    barriers = tuple(action.target for action in police.legal_actions() if action.target)
    assert len(movement) == 5
    assert barriers == (
        Position(1, 1),
        Position(0, 1),
        Position(2, 1),
        Position(1, 2),
        Position(1, 0),
    )
    assert len(_state(role=Role.THIEF).legal_actions()) == 5
    assert all(
        action.action_type is not ActionType.BARRIER
        for action in _state(role=Role.THIEF).legal_actions()
    )
    assert all(
        action.action_type is not ActionType.BARRIER
        for action in _state(barriers_placed=2).legal_actions()
    )
    assert _state(terminal_reason=TerminalReason.STOPPED).legal_actions() == ()


def test_movement_and_stay_transitions_preserve_invariants() -> None:
    moved = transition(_state(), Action.move(Direction.NORTH))
    assert moved.state.position == Position(0, 1)
    assert moved.state.step_number == 1
    assert moved.state.visited == frozenset({Position(1, 1), Position(0, 1)})
    assert moved.public_events == ()

    stayed = transition(moved.state, Action.stay())
    assert stayed.state.position == moved.state.position
    assert stayed.state.step_number == 2
    assert stayed.state.visited == moved.state.visited


def test_police_barrier_is_alternative_permanent_public_action() -> None:
    state = _state()
    target = Position(1, 2)
    result = transition(state, Action.barrier(target))
    assert result.state.position == state.position
    assert result.state.barriers_placed == 1
    assert target in result.state.public_barriers
    assert result.public_events == (BarrierPlaced(Role.POLICE, 1, target),)
    assert result.public_events[0].as_dict() == {
        "event_type": "barrier_placed",
        "actor": "police",
        "step_number": 1,
        "target": [1, 2],
    }
    assert Action.move(Direction.EAST) not in result.state.legal_actions()

    self_barrier = transition(state, Action.barrier(state.position))
    assert self_barrier.state.position in self_barrier.state.public_barriers
    assert Action.move(Direction.NORTH) in self_barrier.state.legal_actions()


def test_barrier_quota_role_and_duplicate_targets_fail_closed() -> None:
    with pytest.raises(ValueError, match="not legal"):
        transition(_state(role=Role.THIEF), Action.barrier(Position(1, 1)))
    with pytest.raises(ValueError, match="not legal"):
        transition(_state(barriers_placed=2), Action.barrier(Position(1, 1)))
    existing = BarrierSet(frozenset({Position(1, 2)}))
    with pytest.raises(ValueError, match="not legal"):
        transition(_state(barriers=existing), Action.barrier(Position(1, 2)))
    with pytest.raises(ValueError, match="not legal"):
        transition(_state(), Action.barrier(Position(2, 2)))


def test_transition_sets_survival_then_step_ceiling_and_freezes_terminal() -> None:
    survival_state = _state(
        rules=GameRules(Board(3), 2, 9, 2),
        step_number=1,
    )
    survived = transition(survival_state, Action.stay()).state
    assert survived.terminal_reason is TerminalReason.SURVIVAL
    with pytest.raises(ValueError, match="terminal"):
        transition(survived, Action.stay())

    ceiling_state = _state(
        rules=GameRules(Board(3), 2, 2, 9),
        step_number=1,
    )
    assert (
        transition(ceiling_state, Action.stay()).state.terminal_reason
        is TerminalReason.STEP_CEILING
    )


def test_barrier_event_rejects_wrong_actor_and_step() -> None:
    with pytest.raises(TypeError, match="actor"):
        BarrierPlaced("police", 1, Position(0, 0))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="integer"):
        BarrierPlaced(Role.POLICE, True, Position(0, 0))
    with pytest.raises(TypeError, match="target"):
        BarrierPlaced(Role.POLICE, 1, (0, 0))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="only Police"):
        BarrierPlaced(Role.THIEF, 1, Position(0, 0))
    with pytest.raises(ValueError, match="positive"):
        BarrierPlaced(Role.POLICE, 0, Position(0, 0))


def test_thief_cannot_be_replaced_onto_barrier() -> None:
    thief = _state(role=Role.THIEF)
    with pytest.raises(ValueError, match="Thief"):
        replace(
            thief,
            public_barriers=BarrierSet(frozenset({thief.position})),
        )
