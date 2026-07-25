import time

import pytest

from police_thief_p2p.domain import (
    Action,
    Board,
    GameRules,
    LocalGameState,
    Position,
    Role,
    articulation_points,
    shortest_path_length,
    transition,
)

pytestmark = [pytest.mark.performance, pytest.mark.no_cover]


def test_minimum_board_transition_throughput_budget() -> None:
    state = LocalGameState(
        Role.THIEF,
        Position(3, 3),
        GameRules(Board(7), 14, 20_000, 20_000),
        visited=frozenset({Position(3, 3)}),
    )
    started = time.perf_counter()
    for _ in range(10_000):
        transition(state, Action.stay())
    assert time.perf_counter() - started < 3.5


def test_expanded_board_path_and_cut_helper_budget() -> None:
    board = Board(15)
    started = time.perf_counter()
    for _ in range(100):
        assert shortest_path_length(board, Position(0, 0), Position(14, 14)) == 28
    assert articulation_points(board) == frozenset()
    assert time.perf_counter() - started < 5.0
