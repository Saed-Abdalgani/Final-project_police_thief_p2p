"""Typed public SDK surface used by every application adapter."""

from police_thief_p2p.domain import (
    Action,
    ActionType,
    LocalGameState,
    Role,
    RoleAssignment,
    SeriesScore,
    SubGameOutcome,
    TerminalReason,
    TransitionResult,
)
from police_thief_p2p.sdk.dto import ReadinessReport, ReadinessStatus
from police_thief_p2p.sdk.errors import ErrorCode, SdkError
from police_thief_p2p.sdk.facade import SimulationSdk

__all__ = [
    "Action",
    "ActionType",
    "ErrorCode",
    "LocalGameState",
    "ReadinessReport",
    "ReadinessStatus",
    "Role",
    "RoleAssignment",
    "SdkError",
    "SeriesScore",
    "SimulationSdk",
    "SubGameOutcome",
    "TerminalReason",
    "TransitionResult",
]
