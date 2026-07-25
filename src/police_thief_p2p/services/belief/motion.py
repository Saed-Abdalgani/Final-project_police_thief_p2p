"""Injectable legal opponent transition kernels."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.values import Position


@dataclass(frozen=True, slots=True)
class MotionContext:
    """Only legal local/public features used by an opponent model."""

    observer_position: Position
    recent_cells: tuple[Position, ...] = ()


class MotionModel(Protocol):
    """Map a possible source cell to a row-stochastic legal distribution."""

    def transition(
        self,
        board: Board,
        source: Position,
        barriers: BarrierSet,
        context: MotionContext,
    ) -> tuple[tuple[Position, float], ...]:
        """Return legal target probabilities summing to one."""
        ...


@dataclass(frozen=True, slots=True)
class UniformMotionModel:
    """Uniform baseline over N/S/E/W/STAY legal targets."""

    def transition(
        self,
        board: Board,
        source: Position,
        barriers: BarrierSet,
        context: MotionContext,
    ) -> tuple[tuple[Position, float], ...]:
        """Return an exact row-stochastic legal baseline."""
        del context
        targets = (*board.neighbors(source, barriers), source)
        probability = 1.0 / len(targets)
        return tuple((target, probability) for target in targets)


@dataclass(frozen=True, slots=True)
class MixtureMotionModel:
    """Bounded chase/evade, boundary, revisit, and two-cycle features."""

    chase: float = 0.2
    evade: float = 0.8
    boundary: float = 0.15
    revisit: float = 0.2
    cycle: float = 0.25

    def __post_init__(self) -> None:
        """Validate bounded finite mixture weights."""
        if any(
            not math.isfinite(value) or not 0 <= value <= 2
            for value in (self.chase, self.evade, self.boundary, self.revisit, self.cycle)
        ):
            raise ValueError("motion feature weights must be finite and bounded")

    def transition(
        self,
        board: Board,
        source: Position,
        barriers: BarrierSet,
        context: MotionContext,
    ) -> tuple[tuple[Position, float], ...]:
        """Score legal targets then normalize deterministically."""
        targets = (*board.neighbors(source, barriers), source)
        source_distance = _distance(source, context.observer_position)
        weights = []
        for target in targets:
            delta = _distance(target, context.observer_position) - source_distance
            edge = target.row in {0, board.size - 1} or target.col in {0, board.size - 1}
            revisit = target in context.recent_cells
            two_cycle = len(context.recent_cells) >= 2 and target == context.recent_cells[-2]
            score = (
                self.evade * delta
                - self.chase * delta
                - self.boundary * edge
                - self.revisit * revisit
                - self.cycle * two_cycle
            )
            weights.append(math.exp(max(-20.0, min(20.0, score))))
        total = math.fsum(weights)
        return tuple(
            (target, weight / total) for target, weight in zip(targets, weights, strict=True)
        )


def _distance(left: Position, right: Position) -> int:
    return abs(left.row - right.row) + abs(left.col - right.col)
