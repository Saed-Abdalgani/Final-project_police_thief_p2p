"""Safe immutable data-transfer objects returned by the public SDK."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict

from police_thief_p2p.shared.version import VersionInfo


class ReadinessStatus(StrEnum):
    """Foundation readiness states, distinct from final release readiness."""

    READY = "READY"
    DEGRADED = "DEGRADED"
    NOT_READY = "NOT_READY"


class ReadinessCheckDict(TypedDict):
    """Serialized readiness-check shape."""

    name: str
    passed: bool
    detail: str


class ReadinessReportDict(TypedDict):
    """Serialized readiness-report shape."""

    status: str
    package_version: str
    protocol_version: str
    schema_version: str
    checks: list[ReadinessCheckDict]


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    """One safe, non-secret installation/readiness observation."""

    name: str
    passed: bool
    detail: str

    def as_dict(self) -> ReadinessCheckDict:
        """Return a JSON-compatible representation."""
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    """Typed readiness result from the SDK facade."""

    status: ReadinessStatus
    versions: VersionInfo
    checks: tuple[ReadinessCheck, ...]

    @property
    def is_ready(self) -> bool:
        """Return whether all foundation readiness checks passed."""
        return self.status is ReadinessStatus.READY and all(check.passed for check in self.checks)

    def as_dict(self) -> ReadinessReportDict:
        """Return a deterministic JSON-compatible representation."""
        return {
            "status": self.status.value,
            "package_version": self.versions.package,
            "protocol_version": self.versions.protocol,
            "schema_version": self.versions.schema,
            "checks": [check.as_dict() for check in self.checks],
        }
