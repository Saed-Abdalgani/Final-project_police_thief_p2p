"""Compact public-only planning state and role evaluator interface."""

from dataclasses import dataclass
from typing import Protocol

from police_thief_p2p.domain.board import BarrierSet
from police_thief_p2p.domain.values import Action, Position, Role
from police_thief_p2p.services.strategy.contracts import ScoreBreakdown


@dataclass(frozen=True, slots=True)
class SearchState:
    """Minimal search state containing no objective opponent truth."""

    own_position: Position
    public_barriers: BarrierSet
    posterior_samples: tuple[tuple[Position, float], ...]
    role: Role
    barriers_remaining: int
    horizon: int
    recent_own_cells: tuple[Position, ...]
    board_size: int

    def __post_init__(self) -> None:
        """Validate bounded public/search fields."""
        if self.board_size < 1 or not 1 <= self.horizon <= 8:
            raise ValueError("search dimensions are invalid")
        if self.barriers_remaining < 0 or len(self.posterior_samples) > 256:
            raise ValueError("search resources are invalid")
        if any(weight < 0 for _, weight in self.posterior_samples):
            raise ValueError("search sample weights cannot be negative")

    def cache_key(self) -> tuple[object, ...]:
        """Return a deterministic hashable public-state key."""
        barriers = tuple(
            (cell.row, cell.col)
            for cell in sorted(self.public_barriers.cells, key=lambda item: (item.row, item.col))
        )
        samples = tuple(
            (cell.row, cell.col, round(weight, 12)) for cell, weight in self.posterior_samples
        )
        return (
            self.own_position.row,
            self.own_position.col,
            barriers,
            samples,
            self.role.value,
            self.barriers_remaining,
            self.horizon,
            self.board_size,
        )


class RoleEvaluator(Protocol):
    """Score one legal root action across sampled opponent responses."""

    def evaluate(
        self,
        state: SearchState,
        action: Action,
        depth: int,
    ) -> tuple[ScoreBreakdown, tuple[float, ...]]:
        """Return aggregate features and per-sample downside outcomes."""
        ...
