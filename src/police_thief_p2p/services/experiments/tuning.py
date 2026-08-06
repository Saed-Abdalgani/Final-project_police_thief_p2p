"""Seeded random search with screening-based early stopping over declared spaces."""

import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from police_thief_p2p.services.experiments.spaces import Dimension, sample_point
from police_thief_p2p.services.ports.random_source import RandomSource

SCREENING_STAGE: Final = 0
FULL_STAGE: Final = 1
_MIN_HISTORY: Final = 4


@dataclass(frozen=True, slots=True)
class TrialResult:
    """One evaluated configuration's objective and hard-gate observations."""

    objective: float
    score_share: float
    reliability_pass: bool
    latency_p95_ms: float
    matches: int


type Objective = Callable[[Mapping[str, float | int], int], TrialResult]


@dataclass(frozen=True, slots=True)
class Trial:
    """A persisted attempted configuration, including stopped attempts."""

    trial_id: int
    method: str
    point: Mapping[str, float | int]
    screening: TrialResult
    full: TrialResult | None
    stop_reason: str

    @property
    def completed(self) -> bool:
        """Return whether this trial finished its full evaluation stage."""
        return self.full is not None

    @property
    def deepest(self) -> TrialResult:
        """Return the result from the deepest stage this trial reached."""
        return self.screening if self.full is None else self.full

    @property
    def objective(self) -> float:
        """Return the objective from the deepest completed stage."""
        return self.deepest.objective

    def as_document(self) -> dict[str, object]:
        """Return the serializable record of one attempted configuration."""
        deepest = self.deepest
        return {
            "trial_id": self.trial_id,
            "method": self.method,
            "point": {name: value for name, value in self.point.items()},
            "screening_objective": round(self.screening.objective, 4),
            "objective": round(deepest.objective, 4),
            "score_share_percent": round(deepest.score_share, 3),
            "latency_p95_ms": round(deepest.latency_p95_ms, 3),
            "reliability_pass": deepest.reliability_pass,
            "completed": self.completed,
            "stop_reason": self.stop_reason,
        }


@dataclass(frozen=True, slots=True)
class SearchOutcome:
    """Every attempted trial plus the deterministic selected best trial."""

    method: str
    trials: tuple[Trial, ...]

    def __post_init__(self) -> None:
        """Require at least one attempted trial."""
        if not self.trials:
            raise ValueError("search outcome requires at least one trial")

    @property
    def eligible(self) -> tuple[Trial, ...]:
        """Return completed trials that satisfy the hard reliability gate."""
        return tuple(
            item
            for item in self.trials
            if item.completed and item.full is not None and item.full.reliability_pass
        )

    @property
    def best(self) -> Trial:
        """Return the highest-objective eligible trial, or the best attempt."""
        pool = self.eligible or self.trials
        return max(pool, key=lambda item: (item.objective, -item.trial_id))

    def as_document(self) -> dict[str, object]:
        """Return the serializable search campaign record."""
        return {
            "method": self.method,
            "trials": [item.as_document() for item in self.trials],
            "attempted": len(self.trials),
            "completed": sum(item.completed for item in self.trials),
            "stopped_early": sum(not item.completed for item in self.trials),
            "best_trial_id": self.best.trial_id,
            "best_objective": round(self.best.objective, 4),
        }


def screening_threshold(history: Sequence[float]) -> float | None:
    """Return the median screening objective once enough history exists."""
    if len(history) < _MIN_HISTORY:
        return None
    return statistics.median(history)


def evaluate_trial(
    trial_id: int,
    method: str,
    point: Mapping[str, float | int],
    objective: Objective,
    history: Sequence[float],
) -> Trial:
    """Screen one configuration, then evaluate it fully unless clearly inferior."""
    screening = objective(point, SCREENING_STAGE)
    threshold = screening_threshold(history)
    if not screening.reliability_pass:
        return Trial(trial_id, method, point, screening, None, "RELIABILITY_GATE")
    if threshold is not None and screening.objective < threshold:
        return Trial(trial_id, method, point, screening, None, "BELOW_MEDIAN_SCREEN")
    return Trial(trial_id, method, point, screening, objective(point, FULL_STAGE), "COMPLETED")


def random_search(
    dimensions: Sequence[Dimension],
    objective: Objective,
    rng: RandomSource,
    *,
    trials: int,
) -> SearchOutcome:
    """Run a broad seeded random search and persist every attempted trial."""
    if trials < 1:
        raise ValueError("random search requires at least one trial")
    records: list[Trial] = []
    history: list[float] = []
    for index in range(trials):
        point = sample_point(dimensions, rng)
        record = evaluate_trial(index, "random", point, objective, history)
        history.append(record.screening.objective)
        records.append(record)
    return SearchOutcome("random", tuple(records))
