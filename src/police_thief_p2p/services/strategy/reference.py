"""Clean reimplementation of the documented argmax-Manhattan reference policy."""

from police_thief_p2p.domain.values import Action, Position, Role
from police_thief_p2p.services.strategy.adversary_support import (
    barrier_candidates,
    best_by,
    movement_candidates,
    packed_decision,
)
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.geometry import destination
from police_thief_p2p.services.strategy.request import StrategyRequest

BARRIER_PROBABILITY = 0.2


def _manhattan(left: Position, right: Position) -> int:
    return abs(left.row - right.row) + abs(left.col - right.col)


def _greedy_move(request: StrategyRequest, role: Role) -> tuple[float, Action]:
    peak = request.belief.most_likely()
    board = request.state.rules.board
    ranked: list[tuple[float, int, Action]] = []
    for index, action in enumerate(movement_candidates(request)):
        distance = _manhattan(destination(board, request.state.position, action), peak)
        score = float(-distance if role is Role.POLICE else distance)
        ranked.append((score, -index, action))
    return best_by(ranked)


class ReferenceGreedyPoliceBrain(StrategyBrain):
    """Pursue the belief argmax by Manhattan distance with random barriers."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Place a random legal barrier at the documented rate, else chase."""
        barriers = barrier_candidates(request)
        if barriers and request.rng.random() < BARRIER_PROBABILITY:
            chosen = barriers[request.rng.randbelow(len(barriers))]
            return packed_decision(request, chosen, reason="REFERENCE_RANDOM_BARRIER")
        score, action = _greedy_move(request, Role.POLICE)
        return packed_decision(request, action, reason="REFERENCE_GREEDY_CHASE", score=score)


class ReferenceGreedyThiefBrain(StrategyBrain):
    """Flee the belief argmax by Manhattan distance without graph reasoning."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Maximize raw Manhattan distance from the single most likely cell."""
        score, action = _greedy_move(request, Role.THIEF)
        return packed_decision(request, action, reason="REFERENCE_GREEDY_FLEE", score=score)
