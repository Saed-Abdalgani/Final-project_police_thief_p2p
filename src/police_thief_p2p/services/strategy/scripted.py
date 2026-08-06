"""Deterministic scripted pursuit and evasion benchmarks over the board graph."""

from police_thief_p2p.domain.graph import shortest_path_length
from police_thief_p2p.domain.values import Action, Role
from police_thief_p2p.services.strategy.adversary_support import (
    best_by,
    movement_candidates,
    packed_decision,
)
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.geometry import destination
from police_thief_p2p.services.strategy.request import StrategyRequest


def _graph_distances(request: StrategyRequest) -> list[tuple[float, int, Action]]:
    board = request.state.rules.board
    barriers = request.state.public_barriers
    target = request.belief.most_likely()
    unreachable = float(board.size * board.size)
    ranked: list[tuple[float, int, Action]] = []
    for index, action in enumerate(movement_candidates(request)):
        origin = destination(board, request.state.position, action)
        distance = shortest_path_length(board, origin, target, barriers)
        ranked.append((unreachable if distance is None else float(distance), -index, action))
    return ranked


class ShortestPathPoliceBrain(StrategyBrain):
    """Follow the shortest legal path toward the most likely opponent cell."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Minimize graph distance with deterministic candidate-order ties."""
        ranked = [(-value, order, action) for value, order, action in _graph_distances(request)]
        score, action = best_by(ranked)
        return packed_decision(request, action, reason="SCRIPTED_SHORTEST_PATH", score=score)


class MaximumDistanceThiefBrain(StrategyBrain):
    """Maximize legal graph distance from the most likely opponent cell."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Maximize graph distance with deterministic candidate-order ties."""
        score, action = best_by(_graph_distances(request))
        return packed_decision(request, action, reason="SCRIPTED_MAX_DISTANCE", score=score)
