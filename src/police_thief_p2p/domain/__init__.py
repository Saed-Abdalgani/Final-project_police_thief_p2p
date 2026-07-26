"""Deterministic network-free game domain with lazy public exports."""

# mypy: implicit_reexport = True
# ruff: noqa: F401

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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

_GROUPS = (
    ("police_thief_p2p.domain.board", "BarrierSet Board"),
    ("police_thief_p2p.domain.engine", "TransitionResult transition"),
    ("police_thief_p2p.domain.events", "BarrierPlaced"),
    (
        "police_thief_p2p.domain.graph",
        "articulation_points connected_component connected_components reachable_region "
        "shortest_path_length vertex_disjoint_escape_routes",
    ),
    ("police_thief_p2p.domain.schedule", "RoleAssignment balanced_schedule"),
    (
        "police_thief_p2p.domain.scoring",
        "GroupTotal RolePoints SeriesScore SubGameOutcome aggregate_series score_terminal "
        "series_tie_awards",
    ),
    ("police_thief_p2p.domain.state", "GameRules LocalGameState initial_local_state"),
    (
        "police_thief_p2p.domain.terminal",
        "barrier_capture direct_capture enclosure_capture maximum_step_reached "
        "resolve_verified_terminal survival_reached",
    ),
    (
        "police_thief_p2p.domain.values",
        "Action ActionType Direction Position Role TerminalReason",
    ),
)
_EXPORTS = {name: module for module, names in _GROUPS for name in names.split()}
__all__ = tuple(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load one domain symbol on first access and cache it."""
    if (module_name := _EXPORTS.get(name)) is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return deterministic eager and lazy module attributes."""
    return sorted((*globals(), *_EXPORTS))
