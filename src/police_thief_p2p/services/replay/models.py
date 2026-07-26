"""Immutable replay verification and navigation models."""

from dataclasses import dataclass, replace
from enum import StrEnum


class ReplayIntegrity(StrEnum):
    """Accessible replay integrity states."""

    VERIFIED_OK = "Verified OK"
    TAMPERED = "TAMPERED"


class ReplayMode(StrEnum):
    """Truth boundary selected for offline replay."""

    SINGLE_LOG = "single-log"
    OBJECTIVE = "objective-post-audit"


@dataclass(frozen=True, slots=True)
class ReplayFinding:
    """One deterministic replay validation failure."""

    order: int
    code: str
    evidence: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        """Return a safe machine-readable finding."""
        return {
            "order": self.order,
            "code": self.code,
            "evidence": self.evidence,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class ReplayFrame:
    """One verified state boundary exposed to navigation."""

    sequence: int
    actor: str
    actor_step: int
    action: str
    own_position: tuple[int, int] | None
    police_position: tuple[int, int] | None
    thief_position: tuple[int, int] | None
    public_barriers: tuple[tuple[int, int], ...]
    belief_heatmap: tuple[str, ...]
    commitment_status: str
    terminal_reason: str | None

    def as_dict(self) -> dict[str, object]:
        """Return one deterministic frame document."""
        return {
            "sequence": self.sequence,
            "actor": self.actor,
            "actor_step": self.actor_step,
            "action": self.action,
            "own_position": self.own_position,
            "police_position": self.police_position,
            "thief_position": self.thief_position,
            "public_barriers": self.public_barriers,
            "belief_heatmap": self.belief_heatmap,
            "commitment_status": self.commitment_status,
            "terminal_reason": self.terminal_reason,
        }


@dataclass(frozen=True, slots=True)
class ReplayVerification:
    """Complete immutable verification result for one sub-game."""

    game_uid: str
    sub_game_number: int
    mode: ReplayMode
    integrity: ReplayIntegrity
    verified_steps: int
    expected_steps: int
    terminal_reason: str
    police_points: int
    thief_points: int
    frames: tuple[ReplayFrame, ...]
    findings: tuple[ReplayFinding, ...]
    track_banner: str
    evidence_sha256: str

    @property
    def first_failure(self) -> ReplayFinding | None:
        """Return the first invalid step or linkage finding."""
        return self.findings[0] if self.findings else None

    @property
    def accessible_status(self) -> str:
        """Return icon plus text so color is never the only signal."""
        icon = "✓" if self.integrity is ReplayIntegrity.VERIFIED_OK else "⚠"
        return f"{icon} {self.integrity.value}"

    def as_dict(self) -> dict[str, object]:
        """Return the standalone replay audit document."""
        return {
            "schema_version": "0.2.0",
            "game_uid": self.game_uid,
            "sub_game_number": self.sub_game_number,
            "mode": self.mode.value,
            "integrity": self.integrity.value,
            "accessible_status": self.accessible_status,
            "verified_steps": self.verified_steps,
            "expected_steps": self.expected_steps,
            "terminal_reason": self.terminal_reason,
            "police_points": self.police_points,
            "thief_points": self.thief_points,
            "frames": [item.as_dict() for item in self.frames],
            "findings": [item.as_dict() for item in self.findings],
            "track_banner": self.track_banner,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True, slots=True)
class ReplayCursor:
    """Immutable bounded replay navigation state."""

    verification: ReplayVerification
    index: int = 0
    playing: bool = False

    @property
    def frame(self) -> ReplayFrame | None:
        """Return the selected frame, if verified evidence exists."""
        return self.verification.frames[self.index] if self.verification.frames else None

    def move(self, command: str, step: int | None = None) -> "ReplayCursor":
        """Apply play, pause, next, previous, restart, or go-to-step."""
        maximum = max(0, len(self.verification.frames) - 1)
        if command == "play":
            return replace(self, playing=True)
        if command == "pause":
            return replace(self, playing=False)
        if command == "next":
            return replace(self, index=min(maximum, self.index + 1))
        if command == "previous":
            return replace(self, index=max(0, self.index - 1))
        if command == "restart":
            return replace(self, index=0, playing=False)
        if command == "go-to-step" and type(step) is int and 0 <= step <= maximum:
            return replace(self, index=step)
        raise ValueError("invalid replay navigation command or step")
