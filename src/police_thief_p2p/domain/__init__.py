"""Deterministic network-free game domain."""

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.engine import TransitionResult, transition
from police_thief_p2p.domain.events import BarrierPlaced
from police_thief_p2p.domain.graph import (
    articulation_points,
    connected_component,
    connected_components,
    reachable_region,
    shortest_path_length,
    vertex_disjoint_escape_routes,
)
from police_thief_p2p.domain.schedule import RoleAssignment, balanced_schedule
from police_thief_p2p.domain.scoring import (
    GroupTotal,
    RolePoints,
    SeriesScore,
    SubGameOutcome,
    aggregate_series,
    score_terminal,
    series_tie_awards,
)
from police_thief_p2p.domain.state import GameRules, LocalGameState, initial_local_state
from police_thief_p2p.domain.terminal import (
    barrier_capture,
    direct_capture,
    enclosure_capture,
    maximum_step_reached,
    resolve_verified_terminal,
    survival_reached,
)
from police_thief_p2p.domain.values import (
    Action,
    ActionType,
    Direction,
    Position,
    Role,
    TerminalReason,
)

__all__ = [
    "Action",
    "ActionType",
    "BarrierPlaced",
    "BarrierSet",
    "Board",
    "Direction",
    "GameRules",
    "GroupTotal",
    "LocalGameState",
    "Position",
    "Role",
    "RoleAssignment",
    "RolePoints",
    "SeriesScore",
    "SubGameOutcome",
    "TerminalReason",
    "TransitionResult",
    "aggregate_series",
    "articulation_points",
    "balanced_schedule",
    "barrier_capture",
    "connected_component",
    "connected_components",
    "direct_capture",
    "enclosure_capture",
    "initial_local_state",
    "maximum_step_reached",
    "reachable_region",
    "resolve_verified_terminal",
    "score_terminal",
    "series_tie_awards",
    "shortest_path_length",
    "survival_reached",
    "transition",
    "vertex_disjoint_escape_routes",
]
