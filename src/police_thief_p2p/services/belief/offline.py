"""Post-audit-only calibration against revealed opponent truth."""

import math
from dataclasses import dataclass

from police_thief_p2p.domain.values import Position
from police_thief_p2p.services.belief.grid import BeliefGrid


@dataclass(frozen=True, slots=True)
class CalibrationMetrics:
    """Offline Brier, log-loss, and top-one accuracy."""

    brier_score: float
    mean_log_loss: float
    top_one_accuracy: float


def calibration_metrics(
    audited: tuple[tuple[BeliefGrid, Position], ...],
) -> CalibrationMetrics:
    """Measure forecasts only after final audit reveals the true path."""
    if not audited:
        raise ValueError("calibration requires audited samples")
    brier = []
    losses = []
    correct = 0
    for belief, revealed_position in audited:
        if (
            not 0 <= revealed_position.row < belief.size
            or not 0 <= revealed_position.col < belief.size
        ):
            raise ValueError("audited position is outside belief board")
        brier.append(
            math.fsum(
                (probability - float(cell == revealed_position)) ** 2
                for cell, probability in belief.items()
            )
        )
        truth_probability = max(1e-300, belief.probability(revealed_position))
        losses.append(-math.log(truth_probability))
        correct += belief.most_likely() == revealed_position
    count = len(audited)
    return CalibrationMetrics(
        math.fsum(brier) / count,
        math.fsum(losses) / count,
        correct / count,
    )
