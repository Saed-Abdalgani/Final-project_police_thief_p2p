"""Legal opponent response sampling from learned normalized mixtures."""

import math

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.values import Position
from police_thief_p2p.services.ports.random_source import RandomSource


def sample_legal_target(
    board: Board,
    source: Position,
    barriers: BarrierSet,
    observer: Position,
    mixture: tuple[float, float, float, float, float],
    rng: RandomSource,
    recent: tuple[Position, ...] = (),
) -> Position:
    """Sample only N/S/E/W/STAY targets under learned bounded features."""
    if len(mixture) != 5 or abs(math.fsum(mixture) - 1.0) > 1e-9:
        raise ValueError("opponent mixture must be normalized")
    targets = (*board.neighbors(source, barriers), source)
    weights: list[float] = []
    source_distance = _manhattan(source, observer)
    for target in targets:
        delta = _manhattan(target, observer) - source_distance
        boundary = float(target.row in {0, board.size - 1} or target.col in {0, board.size - 1})
        revisit = float(target in recent)
        cycle = float(len(recent) >= 2 and target == recent[-2])
        feature = (
            mixture[0]
            + mixture[1] * max(0.0, 1.0 + delta)
            + mixture[2] * (0.5 + boundary)
            + mixture[3] * (1.5 - revisit)
            + mixture[4] * (1.5 - cycle)
        )
        weights.append(max(1e-9, feature))
    threshold = rng.random() * math.fsum(weights)
    cumulative = 0.0
    for target, weight in zip(targets, weights, strict=True):
        cumulative += weight
        if threshold <= cumulative:
            return target
    return targets[-1]


def _manhattan(left: Position, right: Position) -> int:
    return abs(left.row - right.row) + abs(left.col - right.col)
