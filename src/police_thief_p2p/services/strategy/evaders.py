"""Curated Thief adversaries exposing habit, boundary, and switch weaknesses."""

from police_thief_p2p.domain.values import Action, Position, Role
from police_thief_p2p.services.strategy.adversary_support import (
    best_by,
    movement_candidates,
    packed_decision,
)
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.geometry import destination
from police_thief_p2p.services.strategy.hint_profiles import HintProfile
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.scripted import MaximumDistanceThiefBrain

SWITCH_STEP = 12


def _corner_distance(cell: Position, size: int) -> int:
    corners = (
        Position(0, 0),
        Position(0, size - 1),
        Position(size - 1, 0),
        Position(size - 1, size - 1),
    )
    return min(abs(cell.row - item.row) + abs(cell.col - item.col) for item in corners)


class CornerHuggingThiefBrain(StrategyBrain):
    """Move toward the nearest board corner regardless of remaining exits."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Minimize distance to the closest corner with deterministic ties."""
        board = request.state.rules.board
        ranked: list[tuple[float, int, Action]] = []
        for index, action in enumerate(movement_candidates(request)):
            target = destination(board, request.state.position, action)
            ranked.append((float(-_corner_distance(target, board.size)), -index, action))
        score, action = best_by(ranked)
        return packed_decision(request, action, reason="ADVERSARY_CORNER_HUG", score=score)


class BoundaryFollowingThiefBrain(StrategyBrain):
    """Prefer boundary cells and only leave them when no boundary move is legal."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Reward boundary cells and penalize immediate reversals."""
        board = request.state.rules.board
        ranked: list[tuple[float, int, Action]] = []
        for index, action in enumerate(movement_candidates(request)):
            target = destination(board, request.state.position, action)
            edge = target.row in {0, board.size - 1} or target.col in {0, board.size - 1}
            reversal = bool(request.public_history) and action == request.public_history[-1]
            ranked.append((float(edge) - 0.5 * float(reversal), -index, action))
        score, action = best_by(ranked)
        return packed_decision(request, action, reason="ADVERSARY_BOUNDARY_WALK", score=score)


class CycleThiefBrain(StrategyBrain):
    """Repeat a fixed short oscillation, producing a highly predictable path."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Replay the action from two steps ago when it is still legal."""
        candidates = movement_candidates(request)
        history = request.public_history
        chosen = candidates[request.state.step_number % len(candidates)]
        if len(history) >= 2 and history[-2] in candidates:
            chosen = history[-2]
        return packed_decision(request, chosen, reason="ADVERSARY_CYCLE")


class SwitchingThiefBrain(StrategyBrain):
    """Change from corner hugging to distance maximization at a fixed step."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Switch policy and hint honesty once the change point is reached."""
        if request.state.step_number < SWITCH_STEP:
            inner = CornerHuggingThiefBrain().decide(request)
            profile = HintProfile.ALWAYS_HONEST
        else:
            inner = MaximumDistanceThiefBrain().decide(request)
            profile = HintProfile.ALWAYS_LIE
        return packed_decision(
            request,
            inner.action,
            reason="ADVERSARY_SWITCH",
            score=inner.metrics.score.total,
            profile=profile,
        )
