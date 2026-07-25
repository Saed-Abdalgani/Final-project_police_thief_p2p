"""Versioned application facade; the only business entry point for adapters."""

from police_thief_p2p.domain.engine import TransitionResult, transition
from police_thief_p2p.domain.schedule import RoleAssignment, balanced_schedule
from police_thief_p2p.domain.scoring import (
    SeriesScore,
    SubGameOutcome,
    aggregate_series,
)
from police_thief_p2p.domain.state import LocalGameState, initial_local_state
from police_thief_p2p.domain.values import Action, Role
from police_thief_p2p.sdk.belief_facade import BeliefFacade
from police_thief_p2p.sdk.crypto_facade import CryptoAuditFacade
from police_thief_p2p.sdk.dto import ReadinessCheck, ReadinessReport, ReadinessStatus
from police_thief_p2p.sdk.orchestration_facade import OrchestrationFacade
from police_thief_p2p.sdk.strategy_facade import StrategyFacade
from police_thief_p2p.services.belief import BeliefService, MixtureMotionModel, OwnScentEngine
from police_thief_p2p.services.belief.history_store import SecretScentStore
from police_thief_p2p.services.crypto.store import SealedStepStore
from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.services.protocol.envelope import ProtocolResponse
from police_thief_p2p.services.protocol.runtime import ProtocolRuntime
from police_thief_p2p.shared.config_loader import load_private_bytes, load_shared_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.effective_config import EffectiveConfig, merge_effective_config
from police_thief_p2p.shared.identifiers import GroupId
from police_thief_p2p.shared.schema_registry import contracts_are_compatible
from police_thief_p2p.shared.version import (
    PROTOCOL_VERSION,
    SCHEMA_VERSION,
    current_versions,
)


class SimulationSdk(BeliefFacade, CryptoAuditFacade, StrategyFacade, OrchestrationFacade):
    """Expose typed product use cases without leaking service implementations."""

    __slots__ = ("_belief_service", "_protocol", "_scent_engine", "_sealed_steps")

    def __init__(
        self,
        protocol: ProtocolRuntime | None = None,
        scent_history_repository: RepositoryPort | None = None,
    ) -> None:
        """Create the facade with an optional isolated peer protocol runtime."""
        self._protocol = protocol
        self._sealed_steps = SealedStepStore()
        scent_store = (
            None if scent_history_repository is None else SecretScentStore(scent_history_repository)
        )
        self._scent_engine = OwnScentEngine(store=scent_store)
        self._belief_service = BeliefService(motion_model=MixtureMotionModel())

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
        return initial_local_state(config, role)

    def legal_actions(self, state: LocalGameState) -> tuple[Action, ...]:
        """Return deterministic legal actions for one local state."""
        return state.legal_actions()

    def apply_action(self, state: LocalGameState, action: Action) -> TransitionResult:
        """Apply one deterministic domain transition."""
        return transition(state, action)

    def create_role_schedule(
        self,
        initiating_group: str,
        opponent_group: str,
    ) -> tuple[RoleAssignment, ...]:
        """Return the balanced signed default six-game schedule."""
        return balanced_schedule(initiating_group, opponent_group)

    def aggregate_series_score(
        self,
        outcomes: tuple[SubGameOutcome, ...],
        group_a: str,
        group_b: str,
    ) -> SeriesScore:
        """Aggregate six verified outcomes without losing group identity."""
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
