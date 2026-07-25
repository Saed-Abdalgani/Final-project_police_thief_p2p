"""Single deterministic Bayesian prediction and fusion pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.values import Position
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.belief.hint import TemplateCueParser
from police_thief_p2p.services.belief.models import (
    BeliefDiagnostics,
    BeliefUpdate,
    VerifiedScentEvidence,
)
from police_thief_p2p.services.belief.motion import (
    MotionContext,
    MotionModel,
    UniformMotionModel,
)
from police_thief_p2p.services.belief.reliability import HintReliability
from police_thief_p2p.services.ports.hint_parser import HintParserPort

_MIN_LOG_WEIGHT = 1e-300


@dataclass(frozen=True, slots=True)
class BeliefService:
    """Predict, mask, fuse scent/hint in log space, normalize, and diagnose."""

    motion_model: MotionModel = field(default_factory=UniformMotionModel)
    hint_parser: HintParserPort = field(default_factory=TemplateCueParser)
    scent_noise_floor: float = 1e-6
    hint_ratio_cap: float = 3.0
    credible_target: float = 0.9

    def __post_init__(self) -> None:
        """Validate numeric likelihood and diagnostic bounds."""
        if (
            not 0 < self.scent_noise_floor < 1
            or not 1 <= self.hint_ratio_cap <= 10
            or not 0 < self.credible_target <= 1
        ):
            raise ValueError("belief update bounds are invalid")

    def update(
        self,
        prior: BeliefGrid,
        evidence: VerifiedScentEvidence,
        *,
        barriers: BarrierSet,
        hint: str,
        observer_position: Position,
        reliability: HintReliability,
        recent_cells: tuple[Position, ...] = (),
    ) -> BeliefUpdate:
        """Run the only live belief-update pipeline."""
        frame = evidence.frame
        if frame.rows != prior.size or frame.cols != prior.size:
            raise ValueError("scent and belief dimensions differ")
        board = Board(prior.size)
        masked = prior.masked | barriers.cells
        predicted = self._predict(
            prior.remask(masked),
            board,
            barriers,
            MotionContext(observer_position, recent_cells),
        )
        scent = {(cell.row, cell.col): float(cell.decimal_value()) for cell in frame.cells}
        cue = self.hint_parser.parse(hint, prior.size)
        if len(cue.likelihoods) != prior.size * prior.size:
            raise ValueError("hint likelihood count differs from belief dimensions")
        reliability_mean = reliability.mean(cue.category, frame.step_number)
        weights: dict[Position, float] = {}
        for index, (cell, probability) in enumerate(predicted.items()):
            if cell in masked or probability <= 0:
                continue
            scent_likelihood = self.scent_noise_floor + scent.get((cell.row, cell.col), 0.0)
            raw_hint = max(
                1 / self.hint_ratio_cap, min(self.hint_ratio_cap, cue.likelihoods[index])
            )
            hint_likelihood = raw_hint**reliability_mean
            weights[cell] = math.log(max(probability, _MIN_LOG_WEIGHT))
            weights[cell] += math.log(max(scent_likelihood, _MIN_LOG_WEIGHT))
            weights[cell] += math.log(max(hint_likelihood, _MIN_LOG_WEIGHT))
        posterior, fallback = normalize_log_weights(prior.size, weights, predicted, masked)
        peak = posterior.probability(posterior.most_likely())
        region = posterior.credible_region(self.credible_target)
        diagnostics = BeliefDiagnostics(
            entropy_bits=posterior.entropy_bits(),
            peak_probability=peak,
            credible_region=tuple((cell.row, cell.col) for cell in region),
            most_likely_cell=(posterior.most_likely().row, posterior.most_likely().col),
            fallback_used=fallback,
            hint_category=cue.category,
        )
        return BeliefUpdate(posterior, diagnostics)

    def _predict(
        self,
        prior: BeliefGrid,
        board: Board,
        barriers: BarrierSet,
        context: MotionContext,
    ) -> BeliefGrid:
        weights: dict[Position, float] = {}
        for source, mass in prior.items():
            if mass <= 0 or source in barriers:
                continue
            transitions = self.motion_model.transition(board, source, barriers, context)
            if not math.isclose(math.fsum(value for _, value in transitions), 1.0, abs_tol=1e-12):
                raise ValueError("motion transition row is not stochastic")
            for target, probability in transitions:
                weights[target] = weights.get(target, 0.0) + mass * probability
        return BeliefGrid.from_weights(prior.size, weights, masked=prior.masked | barriers.cells)


def normalize_log_weights(
    size: int,
    logs: dict[Position, float],
    fallback: BeliefGrid,
    masked: frozenset[Position],
) -> tuple[BeliefGrid, bool]:
    """Normalize log weights or deterministically recover the reachable prior."""
    finite = {cell: value for cell, value in logs.items() if math.isfinite(value)}
    if not finite:
        return fallback.remask(masked), True
    maximum = max(finite.values())
    weights = {cell: math.exp(value - maximum) for cell, value in finite.items()}
    if math.fsum(weights.values()) <= 0:
        return fallback.remask(masked), True
    return BeliefGrid.from_weights(size, weights, masked=masked), False
