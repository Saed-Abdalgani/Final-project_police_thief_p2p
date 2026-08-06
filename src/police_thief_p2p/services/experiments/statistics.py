"""Deterministic bootstrap intervals and Bradley-Terry secondary ranking."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from police_thief_p2p.services.ports.random_source import RandomSource

DEFAULT_RESAMPLES = 2_000
_ELO_SCALE = 400.0
_BT_ITERATIONS = 200
_BT_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class Interval:
    """Point estimate with a percentile bootstrap confidence interval."""

    mean: float
    lower: float
    upper: float
    samples: int
    confidence: float

    def as_document(self) -> dict[str, object]:
        """Return the serializable rounded interval."""
        return {
            "mean": round(self.mean, 4),
            "lower": round(self.lower, 4),
            "upper": round(self.upper, 4),
            "samples": self.samples,
            "confidence": self.confidence,
        }


def percentile(values: Sequence[float], fraction: float) -> float:
    """Return a deterministic nearest-rank percentile."""
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("percentile fraction must be in [0, 1]")
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def bootstrap_interval(
    values: Sequence[float],
    rng: RandomSource,
    *,
    resamples: int = DEFAULT_RESAMPLES,
    confidence: float = 0.95,
) -> Interval:
    """Return the percentile bootstrap interval for a sample mean."""
    if not values:
        raise ValueError("bootstrap requires at least one observation")
    if resamples < 1 or not 0.5 <= confidence < 1.0:
        raise ValueError("bootstrap parameters are outside the supported range")
    count = len(values)
    means = []
    for _ in range(resamples):
        total = math.fsum(values[rng.randbelow(count)] for _ in range(count))
        means.append(total / count)
    tail = (1.0 - confidence) / 2.0
    low, high = min(values), max(values)
    return Interval(
        mean=math.fsum(values) / count,
        lower=min(max(percentile(means, tail), low), high),
        upper=max(min(percentile(means, 1.0 - tail), high), low),
        samples=count,
        confidence=confidence,
    )


def paired_difference_interval(
    candidate: Sequence[float],
    baseline: Sequence[float],
    rng: RandomSource,
    *,
    resamples: int = DEFAULT_RESAMPLES,
) -> Interval:
    """Return the bootstrap interval for paired candidate-minus-baseline deltas."""
    if len(candidate) != len(baseline):
        raise ValueError("paired comparison requires equal-length samples")
    deltas = [left - right for left, right in zip(candidate, baseline, strict=True)]
    return bootstrap_interval(deltas, rng, resamples=resamples)


def bradley_terry_strengths(
    wins: Mapping[tuple[str, str], int],
    competitors: Sequence[str],
) -> dict[str, float]:
    """Fit log-scale Bradley-Terry strengths from pairwise win counts."""
    if not competitors:
        raise ValueError("ranking requires at least one competitor")
    strengths = dict.fromkeys(competitors, 1.0)
    for _ in range(_BT_ITERATIONS):
        shift = 0.0
        for name in competitors:
            numerator = math.fsum(count for (left, _), count in wins.items() if left == name)
            denominator = math.fsum(
                (count + wins.get((other, name), 0)) / (strengths[name] + strengths[other])
                for (left, other), count in wins.items()
                if left == name and other != name
            )
            if numerator <= 0 or denominator <= 0:
                continue
            updated = numerator / denominator
            shift = max(shift, abs(updated - strengths[name]))
            strengths[name] = updated
        if shift < _BT_TOLERANCE:
            break
    geometric = math.fsum(math.log(max(value, 1e-12)) for value in strengths.values())
    offset = geometric / len(strengths)
    return {name: math.log(max(value, 1e-12)) - offset for name, value in strengths.items()}


def elo_ratings(
    wins: Mapping[tuple[str, str], int],
    competitors: Sequence[str],
    *,
    anchor: float = 1_500.0,
) -> dict[str, float]:
    """Convert Bradley-Terry strengths into anchored Elo-scale ratings."""
    scale = _ELO_SCALE / math.log(10.0)
    return {
        name: round(anchor + scale * strength, 2)
        for name, strength in bradley_terry_strengths(wins, competitors).items()
    }
