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
from police_thief_p2p.sdk.dto import ReadinessCheck, ReadinessReport, ReadinessStatus
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


class SimulationSdk:
    """Expose typed product use cases without leaking service implementations."""

    __slots__ = ()

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
                    f"Packaged schemas match schema/protocol {SCHEMA_VERSION}."
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
