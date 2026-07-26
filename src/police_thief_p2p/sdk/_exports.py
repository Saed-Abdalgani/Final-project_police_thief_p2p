"""Lazy SDK export registry kept separate from the public typing surface."""

_GROUPS = (
    (
        "police_thief_p2p.domain",
        "Action ActionType LocalGameState Role RoleAssignment SeriesScore "
        "SubGameOutcome TerminalReason TransitionResult",
    ),
    ("police_thief_p2p.sdk.dto", "ReadinessReport ReadinessStatus"),
    ("police_thief_p2p.sdk.errors", "ErrorCode SdkError"),
    ("police_thief_p2p.sdk.facade", "SimulationSdk"),
    (
        "police_thief_p2p.sdk.live_runtime",
        "LifecycleCommand LifecyclePort LiveWorker SnapshotChannel",
    ),
    (
        "police_thief_p2p.sdk.live_view",
        "FORBIDDEN_LIVE_FIELDS LocalView SnapshotContext ViewMetrics ViewStatus",
    ),
    ("police_thief_p2p.sdk.protocol_factory", "create_protocol_runtime"),
    (
        "police_thief_p2p.services.audit",
        "AuditBundle AuditFinding AuditReport AuditStatus AuditStep FinalAgreement agree_audits",
    ),
    (
        "police_thief_p2p.services.belief",
        "BeliefDiagnostics BeliefGrid BeliefUpdate HintReliability OpponentScentFrame",
    ),
    ("police_thief_p2p.services.crypto.declaration", "SignedStepZero SigningKey StepZeroBody"),
    (
        "police_thief_p2p.services.crypto.payload",
        "CommitmentBody CommittedAction LiveReveal PublicCommitment",
    ),
    ("police_thief_p2p.services.crypto.store", "CommitmentIdentity FinalRevealManifest"),
    (
        "police_thief_p2p.services.orchestration",
        "CancellationToken GamePhase HealthState HealthView Heartbeat "
        "OrchestrationResult PeerWorkflowPort",
    ),
    (
        "police_thief_p2p.services.protocol",
        "ProtocolEnvelope ProtocolErrorCode ProtocolLimits ProtocolResponse SenderIdentity",
    ),
    ("police_thief_p2p.services.protocol.negotiation_context", "deterministic_game_id"),
    (
        "police_thief_p2p.services.protocol.negotiation_models",
        "CountedLedger MatchAcceptance MatchProposal Participant PlayedCommits "
        "RepositoryLinks RoleTerm",
    ),
    (
        "police_thief_p2p.services.replay.models",
        "ReplayCursor ReplayFinding ReplayFrame ReplayIntegrity ReplayMode ReplayVerification",
    ),
    (
        "police_thief_p2p.services.strategy",
        "Decision DecisionMetrics HintIntent HintVerdict OpponentSummary ScoreBreakdown "
        "SemanticRegion StrategyCommitmentFields",
    ),
)

EXPORTS = {name: module for module, names in _GROUPS for name in names.split()}
