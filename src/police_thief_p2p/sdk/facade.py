"""Versioned application facade; the only business entry point for adapters."""

from police_thief_p2p.sdk.dto import ReadinessCheck, ReadinessReport, ReadinessStatus
from police_thief_p2p.shared.version import current_versions


class SimulationSdk:
    """Expose typed product use cases without leaking service implementations."""

    __slots__ = ()

    def check_readiness(self) -> ReadinessReport:
        """Return the M1 foundation readiness result.

        Later milestones extend this through injected readiness contributors. This
        foundation result deliberately makes no gameplay or deployment claim.
        """
        checks = (
            ReadinessCheck(
                name="sdk.import",
                passed=True,
                detail="Typed SimulationSdk foundation is importable.",
            ),
        )
        return ReadinessReport(
            status=ReadinessStatus.READY,
            versions=current_versions(),
            checks=checks,
        )
