"""Versioned application facade; the only business entry point for adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from police_thief_p2p.sdk.belief_facade import BeliefFacade
from police_thief_p2p.sdk.crypto_facade import CryptoAuditFacade
from police_thief_p2p.sdk.dto import ReadinessCheck, ReadinessReport, ReadinessStatus
from police_thief_p2p.sdk.live_facade import LiveViewFacade
from police_thief_p2p.sdk.orchestration_facade import OrchestrationFacade
from police_thief_p2p.sdk.replay_facade import ReplayFacade
from police_thief_p2p.sdk.reporting_facade import ArtifactReportingFacade
from police_thief_p2p.sdk.simulation_facade import SimulationFacade
from police_thief_p2p.sdk.strategy_facade import StrategyFacade
from police_thief_p2p.shared.schema_catalog import contracts_are_compatible
from police_thief_p2p.shared.version import (
    PROTOCOL_VERSION,
    SCHEMA_VERSION,
    current_versions,
)

if TYPE_CHECKING:
    from police_thief_p2p.domain.engine import TransitionResult
    from police_thief_p2p.domain.schedule import RoleAssignment
    from police_thief_p2p.domain.scoring import SeriesScore, SubGameOutcome
    from police_thief_p2p.domain.state import LocalGameState
    from police_thief_p2p.domain.values import Action, Role
    from police_thief_p2p.sdk.live_runtime import LifecyclePort
    from police_thief_p2p.services.ports.repository import RepositoryPort
    from police_thief_p2p.services.protocol.envelope import ProtocolResponse
    from police_thief_p2p.services.protocol.runtime import ProtocolRuntime
    from police_thief_p2p.shared.config_models import SharedConfig
    from police_thief_p2p.shared.effective_config import EffectiveConfig


class SimulationSdk(
    BeliefFacade,
    CryptoAuditFacade,
    StrategyFacade,
    OrchestrationFacade,
    ArtifactReportingFacade,
    LiveViewFacade,
    ReplayFacade,
    SimulationFacade,
):
    """Expose typed product use cases without leaking service implementations."""

    __slots__ = tuple(
        "_belief_service _lifecycle _protocol _scent_engine "  # noqa: SIM905
        "_scent_history_repository _sealed_steps".split()
    )

    def __init__(
        self,
        protocol: ProtocolRuntime | None = None,
        scent_history_repository: RepositoryPort | None = None,
        lifecycle: LifecyclePort | None = None,
    ) -> None:
        """Create the facade with an optional isolated peer protocol runtime."""
        self._protocol = protocol
        self._lifecycle = lifecycle
        self._sealed_steps = None
        self._scent_history_repository = scent_history_repository
        self._scent_engine = None
        self._belief_service = None

    def check_readiness(self) -> ReadinessReport:
        """Return foundation and packaged contract compatibility readiness."""
        contracts_ok = contracts_are_compatible(SCHEMA_VERSION, PROTOCOL_VERSION)
        checks = (
            ReadinessCheck(
                name="sdk.import",
                passed=True,
                detail="Typed SimulationSdk foundation is importable.",
            ),
            ReadinessCheck(
                name="config.contracts",
                passed=contracts_ok,
                detail=(
                    "Packaged schemas match "
                    f"schema {SCHEMA_VERSION} and protocol {PROTOCOL_VERSION}."
                    if contracts_ok
                    else "Packaged schema compatibility mismatch."
                ),
            ),
        )
        return ReadinessReport(
            status=ReadinessStatus.READY if contracts_ok else ReadinessStatus.NOT_READY,
            versions=current_versions(),
            checks=checks,
        )

    def load_configuration(
        self,
        shared_document: bytes,
        private_document: bytes,
        *,
        shared_source: str = "game.json",
        private_source: str = "game.toml",
        submission_mode: bool = False,
    ) -> EffectiveConfig:
        """Validate and merge shared JSON and private TOML input."""
        from police_thief_p2p.shared.config_loader import load_private_bytes, load_shared_bytes
        from police_thief_p2p.shared.effective_config import merge_effective_config
        from police_thief_p2p.shared.identifiers import GroupId

        shared = load_shared_bytes(
            shared_document,
            source=shared_source,
            submission_mode=submission_mode,
        )
        private = load_private_bytes(private_document, source=private_source)
        if submission_mode:
            GroupId(private.identity.group_id, submission_mode=True)
        return merge_effective_config(shared, private)

    def create_local_game(self, config: SharedConfig, role: Role) -> LocalGameState:
        """Create a role-specific local state without opponent truth."""
        from police_thief_p2p.domain.state import initial_local_state

        return initial_local_state(config, role)

    def legal_actions(self, state: LocalGameState) -> tuple[Action, ...]:
        """Return deterministic legal actions for one local state."""
        return state.legal_actions()

    def apply_action(self, state: LocalGameState, action: Action) -> TransitionResult:
        """Apply one deterministic domain transition."""
        from police_thief_p2p.domain.engine import transition

        return transition(state, action)

    def create_role_schedule(
        self,
        initiating_group: str,
        opponent_group: str,
    ) -> tuple[RoleAssignment, ...]:
        """Return the balanced signed default six-game schedule."""
        from police_thief_p2p.domain.schedule import balanced_schedule

        return balanced_schedule(initiating_group, opponent_group)

    def aggregate_series_score(
        self,
        outcomes: tuple[SubGameOutcome, ...],
        group_a: str,
        group_b: str,
    ) -> SeriesScore:
        """Aggregate six verified outcomes without losing group identity."""
        from police_thief_p2p.domain.scoring import aggregate_series

        return aggregate_series(outcomes, group_a, group_b)

    def protocol_health(self) -> ProtocolResponse:
        """Return a state-free peer liveness response."""
        return self._require_protocol().health()

    def protocol_capabilities(self) -> ProtocolResponse:
        """Return supported protocol, schema, tools, and role versions."""
        return self._require_protocol().capabilities()

    def receive_protocol_request(self, tool: str, document: bytes) -> ProtocolResponse:
        """Execute one bounded inbound peer request through the protocol service."""
        return self._require_protocol().handle(tool, document)

    def protocol_pipeline_trace(self) -> tuple[str, ...]:
        """Return stage-order evidence for the most recent request."""
        return self._require_protocol().last_pipeline_trace

    def _require_protocol(self) -> ProtocolRuntime:
        if self._protocol is None:
            raise RuntimeError("protocol runtime is not configured")
        return self._protocol
