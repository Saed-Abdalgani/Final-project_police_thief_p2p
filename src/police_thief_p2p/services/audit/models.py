"""Immutable serializable evidence and report models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.domain.values import TerminalReason
from police_thief_p2p.services.crypto.capture import CaptureExchange
from police_thief_p2p.services.crypto.declaration import SignedStepZero, SigningKey
from police_thief_p2p.services.crypto.journal import JournalEntry
from police_thief_p2p.services.crypto.payload import LiveReveal
from police_thief_p2p.services.crypto.store import FinalRevealManifest
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.scent import ScentPolicy


class AuditStatus(StrEnum):
    """Only integrity-preserving and mandatory-sanction outcomes."""

    VERIFIED_OK = "Verified OK"
    TAMPERED = "TAMPERED"


@dataclass(frozen=True, slots=True)
class AuditStep:
    """One ordered live reveal paired with its terminal nonce."""

    sequence: int
    reveal: LiveReveal
    nonce_hex: str


@dataclass(frozen=True, slots=True)
class AuditFinding:
    """Deterministic typed audit failure."""

    order: int
    code: str
    evidence: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return {
            "order": self.order,
            "code": self.code,
            "evidence": self.evidence,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class AuditBundle:
    """Complete offline evidence graph for one sub-game."""

    game_uid: str
    sub_game_number: int
    config: SharedConfig
    config_sha256: str
    scent_policy: ScentPolicy
    scent_model_sha256: str
    role_schedule_sha256: str
    expected_role_schedule_sha256: str
    step_zero: tuple[tuple[SignedStepZero, SigningKey], ...]
    steps: tuple[AuditStep, ...]
    final_manifest: FinalRevealManifest
    journal: tuple[JournalEntry, ...]
    expected_terminal: TerminalReason
    expected_police_points: int
    expected_thief_points: int
    capture_exchange: CaptureExchange | None = None


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Serializable independent audit outcome with immutable sanctions."""

    status: AuditStatus
    verified_steps: int
    expected_steps: int
    terminal_reason: str
    police_points: int
    thief_points: int
    findings: tuple[AuditFinding, ...]
    evidence_sha256: str

    @property
    def first_failure(self) -> AuditFinding | None:
        """Return the first deterministic finding."""
        return self.findings[0] if self.findings else None

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible report."""
        return {
            "status": self.status.value,
            "verified_steps": self.verified_steps,
            "expected_steps": self.expected_steps,
            "terminal_reason": self.terminal_reason,
            "police_points": self.police_points,
            "thief_points": self.thief_points,
            "findings": [finding.as_dict() for finding in self.findings],
            "evidence_sha256": self.evidence_sha256,
        }

    def digest(self) -> str:
        """Digest one independent result for mutual agreement."""
        return sha256_digest(self.as_dict())
