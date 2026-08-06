"""Advanced risk/reachability-aware Thief strategy brain."""

from police_thief_p2p.domain.graph import vertex_disjoint_escape_routes
from police_thief_p2p.domain.values import ActionType, Role
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import (
    BehaviorMode,
    Decision,
    DecisionMetrics,
)
from police_thief_p2p.services.strategy.geometry import destination
from police_thief_p2p.services.strategy.hints import configured_policy, realize_hint
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.search import iterative_search, stratified_samples
from police_thief_p2p.services.strategy.search_state import SearchState
from police_thief_p2p.services.strategy.thief_features import ThiefEvaluator


def _mode(request: StrategyRequest, action_index: int) -> BehaviorMode:
    action = request.legal_actions[action_index]
    board = request.state.rules.board
    target = destination(board, request.state.position, action)
    routes = len(vertex_disjoint_escape_routes(board, target, request.state.public_barriers))
    barriers = len(request.state.public_barriers)
    if routes <= 1 or barriers >= max(3, board.size // 2):
        return BehaviorMode.ANTI_TRAP
    if request.opponent.hint_trust >= 0.6:
        return BehaviorMode.DECEPTION
    return BehaviorMode.MOBILITY


class AdvancedThiefBrain(StrategyBrain):
    """Run deadline-safe downside-aware search over survival features."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Select a legal move/stay and a deterministic behavior mode."""
        candidates = tuple(
            action
            for action in request.legal_actions
            if action.action_type is not ActionType.BARRIER
        )
        samples = stratified_samples(request.belief, request.config.posterior_samples, request.rng)
        search_state = SearchState(
            own_position=request.state.position,
            public_barriers=request.state.public_barriers,
            posterior_samples=samples,
            role=request.state.role,
            barriers_remaining=0,
            horizon=request.config.search_horizon,
            recent_own_cells=tuple(
                sorted(request.state.visited, key=lambda cell: (cell.row, cell.col))
            )[-8:],
            board_size=request.state.rules.board.size,
        )
        evaluator = ThiefEvaluator(request)
        result = iterative_search(
            search_state,
            candidates,
            evaluator,
            clock=request.clock,
            deadline=request.guard_deadline,
            cache_entries=request.config.cache_entries,
            risk_weight=request.config.thief.risk,
            near_tie_epsilon=request.config.near_tie_epsilon,
            rng=request.rng,
        )
        mode = _mode(request, request.legal_actions.index(result.action))
        intent = configured_policy(request.config.hints).choose(
            request.state.position,
            request.state.rules.board.size,
            trust=request.opponent.hint_trust,
            mode=mode,
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
        return Decision(
            result.action,
            intent,
            realize_hint(
                intent,
                request.map_area,
                request.hint_max_words,
                request.config.hints.template_variant,
            ),
            f"THIEF_{mode.value.replace('-', '_').upper()}",
            metrics,
        )
