"""Shared deterministic decision packing for experiment baseline policies."""

from police_thief_p2p.domain.values import Action, ActionType
from police_thief_p2p.services.strategy.contracts import (
    Decision,
    DecisionMetrics,
    ScoreBreakdown,
)
from police_thief_p2p.services.strategy.hint_profiles import HintProfile, profiled_intent
from police_thief_p2p.services.strategy.hints import realize_hint
from police_thief_p2p.services.strategy.request import StrategyRequest


def movement_candidates(request: StrategyRequest) -> tuple[Action, ...]:
    """Return every legal non-barrier candidate offered by the engine."""
    return tuple(
        action for action in request.legal_actions if action.action_type is not ActionType.BARRIER
    )


def barrier_candidates(request: StrategyRequest) -> tuple[Action, ...]:
    """Return every legal barrier candidate offered by the engine."""
    return tuple(
        action for action in request.legal_actions if action.action_type is ActionType.BARRIER
    )


def packed_decision(
    request: StrategyRequest,
    action: Action,
    *,
    reason: str,
    score: float = 0.0,
    profile: HintProfile = HintProfile.ALWAYS_HONEST,
) -> Decision:
    """Pack one chosen legal action with a profile-driven bounded hint."""
    intent = profiled_intent(profile, request)
    metrics = DecisionMetrics(
        latency_ms=0.0,
        candidates=len(request.legal_actions),
        completed_depth=0,
        cache_hits=0,
        seed=request.config.seed,
        profile_version=request.config.profile_version,
        score=ScoreBreakdown((("ADVERSARY", score),), score),
    )
    return Decision(
        action,
        intent,
        realize_hint(intent, request.map_area, request.hint_max_words),
        reason,
        metrics,
    )


def best_by(
    ranked: list[tuple[float, int, Action]],
) -> tuple[float, Action]:
    """Return the deterministic maximum score and action for a ranked list."""
    if not ranked:
        raise ValueError("adversary produced no ranked candidate")
    score, _, action = max(ranked, key=lambda item: (item[0], item[1]))
    return score, action
