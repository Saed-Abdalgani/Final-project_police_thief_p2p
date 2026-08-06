"""Deterministic local graph and posterior feature helpers."""

import math
from typing import cast

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.graph import distance_map
from police_thief_p2p.domain.values import Action, ActionType, Direction, Position
from police_thief_p2p.services.belief.grid import BeliefGrid


def destination(board: Board, origin: Position, action: Action) -> Position:
    """Return the own cell after a movement/stay/barrier action."""
    if action.action_type is ActionType.MOVE:
        return board.target(origin, cast(Direction, action.direction))
    return origin


def barriers_after(current: BarrierSet, action: Action) -> BarrierSet:
    """Return public topology after a candidate action."""
    if action.action_type is ActionType.BARRIER:
        return current.add(cast(Position, action.target))
    return current


def _posterior_distances(
    board: Board,
    own: Position,
    belief: BeliefGrid,
    barriers: BarrierSet,
) -> tuple[tuple[int, float], ...]:
    """Pair every supported posterior cell with its graph distance from ``own``.

    One single-source sweep answers every cell, so the cost stays linear in the board
    rather than running a separate search per posterior cell.
    """
    unreachable = board.size * board.size
    distances = distance_map(board, own, barriers)
    return tuple(
        (distances.get(cell, unreachable), probability)
        for cell, probability in belief.items()
        if probability > 0
    )


def expected_distance(
    board: Board,
    own: Position,
    belief: BeliefGrid,
    barriers: BarrierSet,
) -> float:
    """Return posterior-expected graph distance with bounded unreachable cost."""
    return math.fsum(
        probability * distance
        for distance, probability in _posterior_distances(board, own, belief, barriers)
    )


def lower_quantile_distance(
    board: Board,
    own: Position,
    belief: BeliefGrid,
    barriers: BarrierSet,
    quantile: float = 0.2,
) -> float:
    """Return a downside posterior graph-distance quantile."""
    values = sorted(_posterior_distances(board, own, belief, barriers))
    cumulative = 0.0
    for value, probability in values:
        cumulative += probability
        if cumulative >= quantile:
            return float(value)
    return float(values[-1][0])


def reachable_within(
    board: Board,
    start: Position,
    barriers: BarrierSet,
    horizon: int,
) -> frozenset[Position]:
    """Return passable cells reachable within a bounded number of moves."""
    reached = {start}
    frontier = {start}
    for _ in range(horizon):
        frontier = {
            neighbor
            for cell in frontier
            for neighbor in board.neighbors(cell, barriers)
            if neighbor not in reached
        }
        reached.update(frontier)
        if not frontier:
            break
    return frozenset(reached)


def revisit_cost(
    position: Position, history: tuple[Action, ...], state_position: Position
) -> float:
    """Approximate repetition from own visited cells and two-action cycles."""
    repeated = float(position == state_position)
    if len(history) >= 2 and history[-1] == history[-2]:
        repeated += 1.0
    return repeated
