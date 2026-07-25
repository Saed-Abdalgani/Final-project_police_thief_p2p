from dataclasses import FrozenInstanceError

import pytest

from police_thief_p2p.domain import (
    Action,
    ActionType,
    BarrierSet,
    Board,
    Direction,
    Position,
    Role,
)
from police_thief_p2p.shared.coordinates import CoordinateTransform, OriginCorner


def test_position_is_immutable_hashable_and_bounds_independent() -> None:
    left = Position(-1, 99)
    assert left == Position(-1, 99)
    assert hash(left) == hash(Position(-1, 99))
    assert {left, Position(-1, 99)} == {left}
    with pytest.raises(FrozenInstanceError):
        left.row = 0  # type: ignore[misc]
    for invalid in ((True, 0), (0, 1.5)):
        with pytest.raises(TypeError, match="integers"):
            Position(*invalid)


def test_direction_contains_only_cardinal_values() -> None:
    assert tuple(direction.value for direction in Direction) == ("N", "S", "E", "W")
    for invalid in ("NE", "STAY", "north", ""):
        with pytest.raises(ValueError, match="not a valid Direction"):
            Direction(invalid)


def test_role_opponent_is_symmetric() -> None:
    assert Role.POLICE.opponent is Role.THIEF
    assert Role.THIEF.opponent is Role.POLICE
    assert Role.POLICE.opponent.opponent is Role.POLICE


@pytest.mark.parametrize(
    ("origin", "expected"),
    [
        (OriginCorner.TOP_LEFT, Position(1, 2)),
        (OriginCorner.TOP_RIGHT, Position(1, 4)),
        (OriginCorner.BOTTOM_LEFT, Position(5, 2)),
        (OriginCorner.BOTTOM_RIGHT, Position(5, 4)),
    ],
)
@pytest.mark.parametrize("start_index", [0, 1])
def test_coordinate_normalization_golden_matrix(
    origin: OriginCorner,
    expected: Position,
    start_index: int,
) -> None:
    transform = CoordinateTransform(7, origin, start_index)
    external = (1 + start_index, 2 + start_index)
    assert transform.to_canonical(external) == expected
    assert transform.from_canonical(expected) == external


def test_action_factories_and_invalid_field_combinations() -> None:
    assert Action.move(Direction.NORTH) == Action(ActionType.MOVE, Direction.NORTH)
    assert Action.stay() == Action(ActionType.STAY)
    assert Action.barrier(Position(1, 2)) == Action(ActionType.BARRIER, target=Position(1, 2))
    invalid = (
        (ActionType.MOVE, None, None),
        (ActionType.MOVE, Direction.NORTH, Position(0, 0)),
        (ActionType.STAY, Direction.NORTH, None),
        (ActionType.STAY, None, Position(0, 0)),
        (ActionType.BARRIER, None, None),
        (ActionType.BARRIER, Direction.NORTH, Position(0, 0)),
    )
    for action_type, direction, target in invalid:
        with pytest.raises(ValueError, match="invalid fields"):
            Action(action_type, direction, target)
    with pytest.raises(TypeError, match="action_type"):
        Action("MOVE", Direction.NORTH)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="direction"):
        Action(ActionType.MOVE, "N")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="target"):
        Action(ActionType.BARRIER, target=(0, 0))  # type: ignore[arg-type]


def test_board_bounds_cells_and_cardinal_neighbors() -> None:
    board = Board(3)
    assert len(tuple(board.cells())) == 9
    assert next(board.cells()) == Position(0, 0)
    assert tuple(board.cells())[-1] == Position(2, 2)
    assert len(board.neighbors(Position(0, 0))) == 2
    assert len(board.neighbors(Position(0, 1))) == 3
    assert len(board.neighbors(Position(1, 1))) == 4
    assert not board.contains(Position(-1, 0))
    assert not board.contains(Position(3, 0))
    with pytest.raises(TypeError, match="integer"):
        Board(True)
    with pytest.raises(ValueError, match="positive"):
        Board(0)
    with pytest.raises(ValueError, match="outside"):
        board.neighbors(Position(3, 0))


def test_barrier_set_is_permanent_and_duplicate_add_is_idempotent() -> None:
    position = Position(1, 1)
    empty = BarrierSet()
    added = empty.add(position)
    assert len(empty) == 0
    assert position in added
    assert added.add(position) is added
    assert not hasattr(added, "remove")
    with pytest.raises(TypeError, match="frozenset"):
        BarrierSet({position})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Position"):
        BarrierSet(frozenset({1}))  # type: ignore[arg-type]


def test_legal_movement_filters_edges_and_barriers_but_keeps_stay() -> None:
    board = Board(3)
    barriers = BarrierSet(frozenset({Position(1, 0)}))
    actions = board.legal_movement_actions(Position(0, 0), barriers)
    assert actions == (Action.move(Direction.EAST), Action.stay())
    assert board.move(Position(0, 0), Direction.EAST, barriers) == Position(0, 1)
    with pytest.raises(ValueError, match="leaves"):
        board.move(Position(0, 0), Direction.NORTH)
    with pytest.raises(ValueError, match="barrier"):
        board.move(Position(0, 0), Direction.SOUTH, barriers)
    with pytest.raises(ValueError, match="origin"):
        board.move(Position(-1, 0), Direction.SOUTH)
    with pytest.raises(ValueError, match="outside"):
        board.legal_movement_actions(Position(-1, 0))


def test_action_between_rejects_diagonal_jump_bounds_and_barrier() -> None:
    board = Board(4)
    assert board.action_between(Position(1, 1), Position(1, 1)) == Action.stay()
    assert board.action_between(Position(1, 1), Position(1, 2)) == Action.move(Direction.EAST)
    for target in (Position(2, 2), Position(1, 3)):
        with pytest.raises(ValueError, match="exactly one orthogonal"):
            board.action_between(Position(1, 1), target)
    with pytest.raises(ValueError, match="outside"):
        board.action_between(Position(-1, 0), Position(-1, 0))
    with pytest.raises(ValueError, match="barrier"):
        board.action_between(
            Position(1, 1),
            Position(1, 2),
            BarrierSet(frozenset({Position(1, 2)})),
        )


def test_barrier_candidates_are_current_then_cardinal_and_skip_existing() -> None:
    board = Board(3)
    targets = board.barrier_candidates(Position(0, 0))
    assert targets == (Position(0, 0), Position(1, 0), Position(0, 1))
    barriers = BarrierSet(frozenset({Position(0, 0), Position(1, 0)}))
    assert board.barrier_candidates(Position(0, 0), barriers) == (Position(0, 1),)
    with pytest.raises(ValueError, match="outside"):
        board.barrier_candidates(Position(3, 0))
