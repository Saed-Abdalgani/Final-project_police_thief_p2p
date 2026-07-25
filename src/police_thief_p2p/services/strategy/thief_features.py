"""Risk, reachability, route, scent, and trap features for Thief search."""

import math
from dataclasses import dataclass

from police_thief_p2p.domain.graph import (
    shortest_path_length,
    vertex_disjoint_escape_routes,
)
from police_thief_p2p.domain.values import Action, ActionType
from police_thief_p2p.services.strategy.contracts import ScoreBreakdown
from police_thief_p2p.services.strategy.geometry import destination, reachable_within
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.search_state import SearchState


@dataclass(slots=True)
class ThiefEvaluator:
    """Evaluate legal Thief actions against sampled Police threats."""

    request: StrategyRequest

    def evaluate(
        self,
        state: SearchState,
        action: Action,
        depth: int,
    ) -> tuple[ScoreBreakdown, tuple[float, ...]]:
        """Return risk/space features and per-threat outcomes."""
        if action.action_type is ActionType.BARRIER:
            raise ValueError("Thief evaluator rejects barrier actions")
        board = self.request.state.rules.board
        barriers = self.request.state.public_barriers
        own = destination(board, state.own_position, action)
        weights = self.request.config.thief
        space = len(reachable_within(board, own, barriers, min(depth + 1, 4)))
        routes = len(vertex_disjoint_escape_routes(board, own, barriers))
        boundary = own.row in {0, board.size - 1} or own.col in {0, board.size - 1}
        exits = len(board.neighbors(own, barriers))
        corner_risk = float(boundary and exits < 3)
        revisit = float(own in self.request.state.visited)
        cycle = float(
            len(self.request.public_history) >= 2 and action == self.request.public_history[-2]
        )
        entropy = math.log2(1 + space) * (1 - revisit)
        totals = {
            "SURVIVAL": 0.0,
            "RISK_DISTANCE": 0.0,
            "SPACE": float(space),
            "ROUTES": float(routes),
            "ENTROPY": entropy,
            "TRAPS": 0.0,
            "SCENT": -revisit,
            "CORNER": -corner_risk,
            "CYCLE": -cycle,
        }
        outcomes = []
        for police, probability in state.posterior_samples:
            if self.request.clock.monotonic() >= self.request.guard_deadline:
                raise TimeoutError("Thief evaluation reached strategy guard deadline")
            projected = police
            for _ in range(depth - 1):
                projected = min(
                    (*board.neighbors(projected, barriers), projected),
                    key=lambda cell: (
                        abs(cell.row - own.row) + abs(cell.col - own.col),
                        cell.row,
                        cell.col,
                    ),
                )
            distance = shortest_path_length(board, own, projected, barriers)
            threat_distance = board.size**2 if distance is None else distance
            trapped = float(threat_distance <= 1 and routes <= 1)
            survival = float(threat_distance > 0)
            score = (
                weights.survival * survival
                + weights.risk_distance * threat_distance
                + weights.space * space
                + weights.routes * routes
                + weights.entropy * entropy
                - weights.traps * trapped
                - weights.scent * revisit
                - weights.corner * corner_risk
                - weights.cycle * cycle
            )
            outcomes.append(score)
            totals["SURVIVAL"] += probability * survival
            totals["RISK_DISTANCE"] += probability * threat_distance
            totals["TRAPS"] -= probability * trapped
        total = math.fsum(outcomes) / len(outcomes)
        return ScoreBreakdown(tuple(totals.items()), total), tuple(outcomes)
