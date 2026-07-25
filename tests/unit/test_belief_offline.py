import math

import pytest

from police_thief_p2p.domain import Board, Position
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.belief.offline import calibration_metrics


def test_calibration_metrics_use_post_audit_truth_only() -> None:
    point = BeliefGrid.from_weights(2, {Position(1, 1): 1.0})
    metrics = calibration_metrics(((point, Position(1, 1)),))
    assert metrics.brier_score == 0
    assert metrics.mean_log_loss == 0
    assert metrics.top_one_accuracy == 1
    uniform = BeliefGrid.uniform(Board(2))
    uncertain = calibration_metrics(((uniform, Position(0, 0)),))
    assert uncertain.brier_score == pytest.approx(0.75)
    assert uncertain.mean_log_loss == pytest.approx(math.log(4))
    with pytest.raises(ValueError, match="audited samples"):
        calibration_metrics(())
