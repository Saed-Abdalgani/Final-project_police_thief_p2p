"""Graph-aware Police candidate pruning and risk-scored evaluation."""

import math
from dataclasses import dataclass, field
from typing import cast

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.graph import (
    articulation_points,
    connected_component,
    shortest_path_length,
    vertex_disjoint_escape_routes,
)
from police_thief_p2p.domain.values import Action, ActionType, Position
from police_thief_p2p.services.strategy.contracts import ScoreBreakdown
from police_thief_p2p.services.strategy.geometry import barriers_after, destination
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.search_state import SearchState


def police_candidates(request: StrategyRequest) -> tuple[Action, ...]:
    """Keep all movement plus barriers with corridor, frontier, or capture value."""
    board = request.state.rules.board
    credible = frozenset(request.belief.credible_region(0.9))
    articulations = (
        articulation_points(board, request.state.public_barriers)
        if request.state.public_barriers.cells
        else frozenset()
    )
    selected = []
    for action in request.legal_actions:
        if action.action_type is not ActionType.BARRIER:
            selected.append(action)
            continue
        target = cast(Position, action.target)
        mass = request.belief.probability(target)
        near_frontier = any(
            abs(cell.row - target.row) + abs(cell.col - target.col) <= 2 for cell in credible
        )
        if mass > 0 or target in articulations or near_frontier:
            selected.append(action)
    return tuple(selected)


@dataclass(slots=True)
class PoliceEvaluator:
    """Evaluate Police actions over stratified posterior/response samples."""

    request: StrategyRequest
    topology_cache: dict[tuple[Position, BarrierSet], tuple[int, int]] = field(default_factory=dict)

    def _topology(
        self,
        board: Board,
        target: Position,
        barriers: BarrierSet,
    ) -> tuple[int, int]:
        key = (target, barriers)
        if key not in self.topology_cache:
            self.topology_cache[key] = (
                len(connected_component(board, target, barriers)),
                len(vertex_disjoint_escape_routes(board, target, barriers)),
            )
        return self.topology_cache[key]

    def evaluate(
        self,
        state: SearchState,
        action: Action,
        depth: int,
    ) -> tuple[ScoreBreakdown, tuple[float, ...]]:
        """Return weighted graph features and per-sample scores."""
        board = self.request.state.rules.board
        before_barriers = self.request.state.public_barriers
        after_barriers = barriers_after(before_barriers, action)
        own = destination(board, state.own_position, action)
        weights = self.request.config.police
        totals = {
            "CAPTURE": 0.0,
            "DISTANCE": 0.0,
            "ESCAPE": 0.0,
            "CUT": 0.0,
            "INFORMATION": 0.0,
            "SELF_TRAP": 0.0,
            "BUDGET": 0.0,
            "CYCLE": 0.0,
            "PROVEN_CAPTURE": 0.0,
        }
        own_access = len(connected_component(board, own, after_barriers))
        self_trap = float(own_access <= 1)
        cycle = float(own in self.request.state.visited)
        opportunity = float(action.action_type is ActionType.BARRIER) / max(
            1, state.barriers_remaining
        )
        outcomes = []
        for target, probability in state.posterior_samples:
            if self.request.clock.monotonic() >= self.request.guard_deadline:
                raise TimeoutError("Police evaluation reached strategy guard deadline")
            projected = target
            for _ in range(depth - 1):
                projected = max(
                    (*board.neighbors(projected, after_barriers), projected),
                    key=lambda cell: (
                        abs(cell.row - own.row) + abs(cell.col - own.col),
                        cell.row,
                        cell.col,
                    ),
                )
            captured = own == projected or (
                action.action_type is ActionType.BARRIER and action.target == projected
            )
            distance = shortest_path_length(board, own, projected, after_barriers)
            distance_value = board.size**2 if distance is None else distance
            before_region, before_routes = self._topology(board, projected, before_barriers)
            after_region, after_routes = self._topology(board, projected, after_barriers)
            escape_cut = max(0, before_region - after_region)
            cut = max(0, before_routes - after_routes)
            information = 1.0 / (1.0 + distance_value)
            score = (
                weights.capture * captured
                - weights.distance * distance_value
                + weights.escape * escape_cut
                + weights.cut * cut
                + weights.information * information
                - weights.self_trap * self_trap
                - weights.budget * opportunity
                - weights.cycle * cycle
            )
            outcomes.append(score)
            for name, value in (
                ("CAPTURE", float(captured)),
                ("DISTANCE", -float(distance_value)),
                ("ESCAPE", float(escape_cut)),
                ("CUT", float(cut)),
                ("INFORMATION", information),
                ("SELF_TRAP", -self_trap),
                ("BUDGET", -opportunity),
                ("CYCLE", -cycle),
            ):
                totals[name] += probability * value
        capture_mass = math.fsum(
            probability
            for target, probability in state.posterior_samples
            if own == target or (action.target is not None and action.target == target)
        )
        if capture_mass >= 1 - 1e-12:
            totals["PROVEN_CAPTURE"] = 1_000_000.0
            outcomes = [value + 1_000_000.0 for value in outcomes]
        total = math.fsum(outcomes) / len(outcomes) + totals["PROVEN_CAPTURE"]
        return ScoreBreakdown(tuple(totals.items()), total), tuple(outcomes)
