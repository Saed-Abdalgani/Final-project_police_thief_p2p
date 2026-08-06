"""Deterministic posterior-aware legal baseline and emergency fallback."""

from police_thief_p2p.domain.values import Action, ActionType, Role
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import (
    BehaviorMode,
    Decision,
    DecisionMetrics,
    ScoreBreakdown,
)
from police_thief_p2p.services.strategy.geometry import (
    barriers_after,
    destination,
    expected_distance,
    lower_quantile_distance,
)
from police_thief_p2p.services.strategy.hints import configured_policy, realize_hint
from police_thief_p2p.services.strategy.request import StrategyRequest


def _decision(request: StrategyRequest, action: Action, score: float, reason: str) -> Decision:
    intent = configured_policy(request.config.hints).choose(
        request.state.position,
        request.state.rules.board.size,
        trust=request.opponent.hint_trust,
        mode=BehaviorMode.MOBILITY,
    )
    metrics = DecisionMetrics(
        latency_ms=0.0,
        candidates=len(request.legal_actions),
        completed_depth=0,
        cache_hits=0,
        seed=request.config.seed,
        profile_version=request.config.profile_version,
        score=ScoreBreakdown((("BASELINE", score),), score),
    )
    return Decision(
        action,
        intent,
        realize_hint(
            intent,
            request.map_area,
            request.hint_max_words,
            request.config.hints.template_variant,
        ),
        reason,
        metrics,
    )


class PoliceBaselineBrain(StrategyBrain):
    """Minimize posterior-expected graph distance without argmax collapse."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Select the safest movement/stay candidate with cycle penalties."""
        state = request.state
        board = state.rules.board
        movements = tuple(
            action
            for action in request.legal_actions
            if action.action_type is not ActionType.BARRIER
        )
        scores = []
        for index, action in enumerate(movements):
            target = destination(board, state.position, action)
            distance = expected_distance(
                board,
                target,
                request.belief,
                barriers_after(state.public_barriers, action),
            )
            revisit = 1.0 if target in state.visited else 0.0
            cycle = (
                1.0
                if len(request.public_history) >= 2 and action == request.public_history[-2]
                else 0.0
            )
            scores.append((-distance - revisit - cycle, -index, action))
        score, _, action = max(scores, key=lambda item: (item[0], item[1]))
        return _decision(request, action, score, "POLICE_EXPECTED_DISTANCE")


class ThiefBaselineBrain(StrategyBrain):
    """Maximize the downside distance quantile across the full posterior."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Select a legal non-barrier action with revisit/cycle penalties."""
        state = request.state
        board = state.rules.board
        scores = []
        for index, action in enumerate(request.legal_actions):
            if action.action_type is ActionType.BARRIER:
                continue
            target = destination(board, state.position, action)
            distance = lower_quantile_distance(board, target, request.belief, state.public_barriers)
            revisit = 1.0 if target in state.visited else 0.0
            cycle = (
                1.0
                if len(request.public_history) >= 2 and action == request.public_history[-2]
                else 0.0
            )
            scores.append((distance - revisit - cycle, -index, action))
        score, _, action = max(scores, key=lambda item: (item[0], item[1]))
        return _decision(request, action, score, "THIEF_RISK_QUANTILE")


def fallback_decision(request: StrategyRequest, reason: str) -> Decision:
    """Return a deterministic legal role baseline after any strategy failure."""
    brain: StrategyBrain = (
        PoliceBaselineBrain() if request.state.role is Role.POLICE else ThiefBaselineBrain()
    )
    decision = brain.decide(request)
    return Decision(
        decision.action,
        decision.hint_intent,
        decision.hint,
        reason,
        decision.metrics,
        fallback_used=True,
    )
