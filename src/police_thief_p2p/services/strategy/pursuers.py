"""Curated Police adversaries stressing barrier spend and corridor closure."""

from police_thief_p2p.domain.graph import articulation_points, reachable_region
from police_thief_p2p.domain.values import Action, Role
from police_thief_p2p.services.strategy.adversary_support import (
    barrier_candidates,
    best_by,
    packed_decision,
)
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.geometry import barriers_after
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.scripted import ShortestPathPoliceBrain

AGGRESSIVE_BARRIER_PROBABILITY = 0.5


class AggressiveBarrierPoliceBrain(StrategyBrain):
    """Spend the barrier quota early at random legal targets, then chase."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Place barriers at a high fixed rate while quota remains."""
        candidates = barrier_candidates(request)
        if candidates and request.rng.random() < AGGRESSIVE_BARRIER_PROBABILITY:
            chosen = candidates[request.rng.randbelow(len(candidates))]
            return packed_decision(request, chosen, reason="ADVERSARY_AGGRESSIVE_BARRIER")
        inner = ShortestPathPoliceBrain().decide(request)
        return packed_decision(
            request,
            inner.action,
            reason="ADVERSARY_AGGRESSIVE_CHASE",
            score=inner.metrics.score.total,
        )


def _believed_region(request: StrategyRequest, action: Action | None) -> float:
    board = request.state.rules.board
    barriers = request.state.public_barriers
    if action is not None:
        barriers = barriers_after(barriers, action)
    target = request.belief.most_likely()
    if target in barriers:
        return 0.0
    return float(len(reachable_region(board, target, barriers)))


class GraphCutPoliceBrain(StrategyBrain):
    """Close corridors and articulation cells before closing raw distance."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Prefer the barrier that most reduces the believed reachable region."""
        candidates = barrier_candidates(request)
        cuts = articulation_points(request.state.rules.board, request.state.public_barriers)
        baseline = _believed_region(request, None)
        ranked: list[tuple[float, int, Action]] = []
        for index, action in enumerate(candidates):
            gain = baseline - _believed_region(request, action)
            ranked.append((gain + 2.0 * float(action.target in cuts), -index, action))
        if ranked:
            score, action = best_by(ranked)
            if score > 0.0:
                return packed_decision(request, action, reason="ADVERSARY_GRAPH_CUT", score=score)
        inner = ShortestPathPoliceBrain().decide(request)
        return packed_decision(
            request,
            inner.action,
            reason="ADVERSARY_CUT_CHASE",
            score=inner.metrics.score.total,
        )
