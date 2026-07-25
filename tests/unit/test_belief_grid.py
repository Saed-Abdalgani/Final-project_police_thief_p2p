import math

import pytest

from police_thief_p2p.domain import BarrierSet, Board, Position
from police_thief_p2p.services.belief.grid import BeliefGrid, reachable_cells
from police_thief_p2p.services.belief.motion import (
    MixtureMotionModel,
    MotionContext,
    UniformMotionModel,
)


def test_uniform_prior_is_normalized_reachable_and_masked() -> None:
    board = Board(7)
    barriers = BarrierSet(frozenset({Position(3, 4), Position(4, 3)}))
    reachable = reachable_cells(board, Position(3, 3), barriers)
    belief = BeliefGrid.uniform(board, barriers, reachable)
    assert math.fsum(belief.probabilities) == pytest.approx(1.0, abs=1e-12)
    assert belief.probability(Position(3, 4)) == 0
    assert belief.probability(Position(4, 3)) == 0
    assert all(math.isfinite(value) and value >= 0 for value in belief.probabilities)


def test_topology_change_remasks_and_recovers_valid_distribution() -> None:
    belief = BeliefGrid.uniform(Board(7))
    masked = frozenset(Position(row, col) for row in range(7) for col in range(7))
    with pytest.raises(ValueError, match="no reachable"):
        belief.remask(masked)
    changed = belief.remask(frozenset({Position(0, 0), Position(3, 3)}))
    assert changed.probability(Position(0, 0)) == 0
    assert math.fsum(changed.probabilities) == pytest.approx(1.0)


def test_uniform_and_mixture_motion_rows_are_stochastic_and_legal() -> None:
    board = Board(7)
    barriers = BarrierSet(frozenset({Position(2, 3)}))
    context = MotionContext(Position(0, 0), (Position(3, 2), Position(3, 3)))
    for model in (UniformMotionModel(), MixtureMotionModel()):
        transitions = model.transition(board, Position(3, 3), barriers, context)
        assert math.fsum(value for _, value in transitions) == pytest.approx(1.0)
        assert all(board.contains(cell) and cell not in barriers for cell, _ in transitions)
        assert all(value >= 0 for _, value in transitions)


def test_entropy_credible_region_and_argmax_are_deterministic() -> None:
    uniform = BeliefGrid.uniform(Board(2))
    assert uniform.entropy_bits() == pytest.approx(2.0)
    assert uniform.most_likely() == Position(0, 0)
    assert uniform.credible_region(0.5) == (Position(0, 0), Position(0, 1))
    point = BeliefGrid.from_weights(2, {Position(1, 1): 1.0})
    assert point.entropy_bits() == 0
    assert point.credible_region() == (Position(1, 1),)
    assert point.digest() == BeliefGrid.from_weights(2, {Position(1, 1): 1.0}).digest()
