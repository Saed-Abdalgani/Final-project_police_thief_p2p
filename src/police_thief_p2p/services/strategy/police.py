"""Advanced posterior/graph-aware Police strategy brain."""

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import (
    BehaviorMode,
    Decision,
    DecisionMetrics,
)
from police_thief_p2p.services.strategy.hints import configured_policy, realize_hint
from police_thief_p2p.services.strategy.police_features import (
    PoliceEvaluator,
    police_candidates,
)
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.search import iterative_search, stratified_samples
from police_thief_p2p.services.strategy.search_state import SearchState


class AdvancedPoliceBrain(StrategyBrain):
    """Run deadline-safe risk-sensitive search over Police graph features."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Select movement, hold, or a graph-valued legal barrier."""
        candidates = police_candidates(request)
        samples = stratified_samples(request.belief, request.config.posterior_samples, request.rng)
        state = SearchState(
            own_position=request.state.position,
            public_barriers=request.state.public_barriers,
            posterior_samples=samples,
            role=request.state.role,
            barriers_remaining=request.state.rules.max_barriers - request.state.barriers_placed,
            horizon=request.config.search_horizon,
            recent_own_cells=tuple(
                sorted(request.state.visited, key=lambda cell: (cell.row, cell.col))
            )[-8:],
            board_size=request.state.rules.board.size,
        )
        result = iterative_search(
            state,
            candidates,
            PoliceEvaluator(request),
            clock=request.clock,
            deadline=request.guard_deadline,
            cache_entries=request.config.cache_entries,
            risk_weight=request.config.police.risk,
        )
        intent = configured_policy(request.config.hints).choose(
            request.state.position,
            request.state.rules.board.size,
            trust=request.opponent.hint_trust,
            mode=BehaviorMode.MOBILITY,
        )
        metrics = DecisionMetrics(
            latency_ms=0.0,
            candidates=len(candidates),
            completed_depth=result.completed_depth,
            cache_hits=result.cache_hits,
            seed=request.config.seed,
            profile_version=request.config.profile_version,
            score=result.breakdown,
        )
        reason = (
            "POLICE_PROVEN_CAPTURE"
            if dict(result.breakdown.features)["PROVEN_CAPTURE"] > 0
            else "POLICE_RISK_SEARCH"
        )
        return Decision(
            result.action,
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
