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
from police_thief_p2p.sdk.protocol_factory import create_protocol_runtime
from police_thief_p2p.services.protocol import (
    ProtocolEnvelope,
    ProtocolErrorCode,
    ProtocolLimits,
    ProtocolResponse,
    SenderIdentity,
)
from police_thief_p2p.services.protocol.negotiation_context import deterministic_game_id
from police_thief_p2p.services.protocol.negotiation_models import (
    CountedLedger,
    MatchAcceptance,
    MatchProposal,
    Participant,
    PlayedCommits,
    RepositoryLinks,
    RoleTerm,
)

__all__ = [
    "Action",
    "ActionType",
    "CountedLedger",
    "ErrorCode",
    "LocalGameState",
    "MatchAcceptance",
    "MatchProposal",
    "Participant",
    "PlayedCommits",
    "ProtocolEnvelope",
    "ProtocolErrorCode",
    "ProtocolLimits",
    "ProtocolResponse",
    "ReadinessReport",
    "ReadinessStatus",
    "RepositoryLinks",
    "Role",
    "RoleAssignment",
    "RoleTerm",
    "SdkError",
    "SenderIdentity",
    "SeriesScore",
    "SimulationSdk",
    "SubGameOutcome",
    "TerminalReason",
    "TransitionResult",
    "create_protocol_runtime",
    "deterministic_game_id",
]
