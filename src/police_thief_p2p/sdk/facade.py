"""Versioned application facade; the only business entry point for adapters."""

from police_thief_p2p.sdk.dto import ReadinessCheck, ReadinessReport, ReadinessStatus
from police_thief_p2p.shared.config_loader import load_private_bytes, load_shared_bytes
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
