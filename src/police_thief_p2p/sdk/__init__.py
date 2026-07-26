"""Typed public SDK surface, loaded lazily to keep cold readiness fast."""

# mypy: implicit_reexport = True
# ruff: noqa: F401

from importlib import import_module
from typing import TYPE_CHECKING, Any

from police_thief_p2p.sdk._exports import EXPORTS

if TYPE_CHECKING:
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
    from police_thief_p2p.sdk.live_runtime import (
        LifecycleCommand,
        LifecyclePort,
        LiveWorker,
        SnapshotChannel,
    )
    from police_thief_p2p.sdk.live_view import (
        FORBIDDEN_LIVE_FIELDS,
        LocalView,
        SnapshotContext,
        ViewMetrics,
        ViewStatus,
    )
    from police_thief_p2p.sdk.protocol_factory import create_protocol_runtime
    from police_thief_p2p.services.audit import (
        AuditBundle,
        AuditFinding,
        AuditReport,
        AuditStatus,
        AuditStep,
        FinalAgreement,
        agree_audits,
    )
    from police_thief_p2p.services.belief import (
        BeliefDiagnostics,
        BeliefGrid,
        BeliefUpdate,
        HintReliability,
        OpponentScentFrame,
    )
    from police_thief_p2p.services.crypto.declaration import (
        SignedStepZero,
        SigningKey,
        StepZeroBody,
    )
    from police_thief_p2p.services.crypto.payload import (
        CommitmentBody,
        CommittedAction,
        LiveReveal,
        PublicCommitment,
    )
    from police_thief_p2p.services.crypto.store import CommitmentIdentity, FinalRevealManifest
    from police_thief_p2p.services.orchestration import (
        CancellationToken,
        GamePhase,
        HealthState,
        HealthView,
        Heartbeat,
        OrchestrationResult,
        PeerWorkflowPort,
    )
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
    from police_thief_p2p.services.replay.models import (
        ReplayCursor,
        ReplayFinding,
        ReplayFrame,
        ReplayIntegrity,
        ReplayMode,
        ReplayVerification,
    )
    from police_thief_p2p.services.strategy import (
        Decision,
        DecisionMetrics,
        HintIntent,
        HintVerdict,
        OpponentSummary,
        ScoreBreakdown,
        SemanticRegion,
        StrategyCommitmentFields,
    )

__all__ = tuple(EXPORTS)


def __getattr__(name: str) -> Any:
    """Load one public SDK symbol on first access and cache it."""
    if (module_name := EXPORTS.get(name)) is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return deterministic eager and lazy module attributes."""
    return sorted((*globals(), *EXPORTS))
