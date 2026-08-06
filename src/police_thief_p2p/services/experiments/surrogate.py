"""Gaussian-kernel surrogate with upper-confidence-bound refinement search."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from police_thief_p2p.services.experiments.spaces import Dimension, sample_point
from police_thief_p2p.services.experiments.tuning import (
    Objective,
    SearchOutcome,
    Trial,
    evaluate_trial,
)
from police_thief_p2p.services.ports.random_source import RandomSource

_BANDWIDTH: Final = 0.35
_KAPPA: Final = 1.2
_JITTER: Final = 1e-9


def _unit(dimensions: Sequence[Dimension], point: Mapping[str, float | int]) -> tuple[float, ...]:
    """Map one point into the unit cube for scale-free distances."""
    values: list[float] = []
    for item in dimensions:
        span = item.high - item.low
        raw = float(point.get(item.name, item.low))
        values.append(0.0 if span == 0.0 else (raw - item.low) / span)
    return tuple(values)


def _weight(left: Sequence[float], right: Sequence[float]) -> float:
    """Return the squared-exponential kernel weight between two unit points."""
    squared = sum((a - b) ** 2 for a, b in zip(left, right, strict=True))
    return math.exp(-squared / (2.0 * _BANDWIDTH**2))


@dataclass(frozen=True, slots=True)
class Surrogate:
    """Kernel-weighted posterior mean and spread over observed objectives."""

    points: tuple[tuple[float, ...], ...]
    objectives: tuple[float, ...]

    def __post_init__(self) -> None:
        """Require one objective per observed point."""
        if len(self.points) != len(self.objectives):
            raise ValueError("surrogate needs one objective per observed point")

    def acquisition(self, candidate: Sequence[float]) -> float:
        """Return the upper-confidence-bound score for one candidate point."""
        if not self.points:
            return 0.0
        weights = [_weight(candidate, point) for point in self.points]
        total = sum(weights) + _JITTER
        mean = sum(w * y for w, y in zip(weights, self.objectives, strict=True)) / total
        spread = sum(w * (y - mean) ** 2 for w, y in zip(weights, self.objectives, strict=True))
        deviation = math.sqrt(spread / total)
        unexplored = 1.0 - min(1.0, max(weights))
        return mean + _KAPPA * (deviation + unexplored)


def _observed(
    dimensions: Sequence[Dimension],
    trials: Sequence[Trial],
) -> Surrogate:
    """Build a surrogate from every trial that produced an objective."""
    points = tuple(_unit(dimensions, item.point) for item in trials)
    return Surrogate(points, tuple(item.objective for item in trials))


def _propose(
    dimensions: Sequence[Dimension],
    surrogate: Surrogate,
    rng: RandomSource,
    pool: int,
) -> dict[str, float | int]:
    """Return the pooled candidate maximizing the acquisition function."""
    candidates = [sample_point(dimensions, rng) for _ in range(pool)]
    scored = [
        (surrogate.acquisition(_unit(dimensions, candidate)), index)
        for index, candidate in enumerate(candidates)
    ]
    return candidates[max(scored)[1]]


def surrogate_search(
    dimensions: Sequence[Dimension],
    objective: Objective,
    rng: RandomSource,
    *,
    trials: int,
    prior: Sequence[Trial] = (),
    pool: int = 24,
    first_id: int = 0,
) -> SearchOutcome:
    """Refine the best known region using surrogate-guided candidate proposals."""
    if trials < 1:
        raise ValueError("surrogate search requires at least one trial")
    if pool < 1:
        raise ValueError("surrogate search requires a positive candidate pool")
    observed = list(prior)
    records: list[Trial] = []
    history = [item.screening.objective for item in prior]
    for offset in range(trials):
        point = _propose(dimensions, _observed(dimensions, observed), rng, pool)
        record = evaluate_trial(first_id + offset, "surrogate", point, objective, history)
        history.append(record.screening.objective)
        observed.append(record)
        records.append(record)
    return SearchOutcome("surrogate", tuple(records))
