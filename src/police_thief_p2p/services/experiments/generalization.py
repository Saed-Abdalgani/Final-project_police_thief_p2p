"""Generalization and degraded-environment gates kept separate from campaign gates."""

from collections.abc import Sequence
from typing import Final

from police_thief_p2p.services.experiments.gate_result import GateResult
from police_thief_p2p.services.experiments.statistics import Interval

MAXIMUM_GENERALIZATION_DROP: Final = 8.0
MINIMUM_DEGRADED_SHARE: Final = 50.0


def overfitting_gate(train_share: float, validation_share: float) -> GateResult:
    """Return the train-to-validation generalization gate."""
    drop = train_share - validation_share
    return GateResult(
        "S06-GENERALIZATION",
        f"validation share within {MAXIMUM_GENERALIZATION_DROP:.0f} points of training",
        drop,
        drop <= MAXIMUM_GENERALIZATION_DROP,
    )


def robustness_gate(shares: Sequence[float]) -> GateResult:
    """Return the degraded-observation retention gate."""
    if not shares:
        raise ValueError("robustness gate requires at least one measured case")
    worst = min(shares)
    return GateResult(
        "S04-DEGRADED",
        "no degraded-observation case falls below an even split",
        worst,
        worst >= MINIMUM_DEGRADED_SHARE,
    )


def interval_beats(interval: Interval, reference: float) -> bool:
    """Return whether a paired interval strictly clears a reference value."""
    return interval.lower > reference
