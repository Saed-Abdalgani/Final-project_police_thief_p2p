"""Replay result construction after deterministic verification."""

from police_thief_p2p.domain import TerminalReason
from police_thief_p2p.domain.scoring import score_terminal
from police_thief_p2p.services.artifacts.records import SubGameLogArtifact
from police_thief_p2p.services.replay.models import (
    ReplayFinding,
    ReplayFrame,
    ReplayIntegrity,
    ReplayMode,
    ReplayVerification,
)
from police_thief_p2p.services.replay.steps import ReplayMachine
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.scent import ScentPolicy


def finalize_result(
    log: SubGameLogArtifact,
    mode: ReplayMode,
    machine: ReplayMachine,
    verified: int,
    expected: int,
) -> ReplayVerification:
    """Validate terminal truth and fixed score after all steps."""
    terminal = machine.frames[-1].terminal_reason if machine.frames else None
    try:
        reason = TerminalReason(terminal) if terminal is not None else None
    except ValueError:
        reason = None
    if reason is None or reason.value != log.terminal_reason:
        finding = ReplayFinding(1, "TERMINAL", "result", "terminal truth differs")
        return failed_result(log, mode, tuple(machine.frames), verified, expected, finding)
    points = score_terminal(reason, machine.config.scoring)
    return ReplayVerification(
        game_uid=log.game_uid,
        sub_game_number=log.sub_game_number,
        mode=mode,
        integrity=ReplayIntegrity.VERIFIED_OK,
        verified_steps=verified,
        expected_steps=expected,
        terminal_reason=reason.value,
        police_points=points.police,
        thief_points=points.thief,
        frames=tuple(machine.frames),
        findings=(),
        track_banner=(
            "Objective post-audit tracks verified."
            if mode is ReplayMode.OBJECTIVE
            else "Sibling track unavailable; local track and belief shown."
        ),
        evidence_sha256=evidence_digest(log),
    )


def failed_result(
    log: SubGameLogArtifact,
    mode: ReplayMode,
    frames: tuple[ReplayFrame, ...],
    verified: int,
    expected: int,
    finding: ReplayFinding | None,
) -> ReplayVerification:
    """Build the stable mandatory tamper result."""
    safe_finding = finding or ReplayFinding(1, "INTERNAL", "replay", "verification failed")
    return ReplayVerification(
        log.game_uid,
        log.sub_game_number,
        mode,
        ReplayIntegrity.TAMPERED,
        verified,
        expected,
        "tamper",
        0,
        0,
        frames,
        (safe_finding,),
        "Verification stopped at first invalid step.",
        evidence_digest(log),
    )


def scent_policy(config: SharedConfig) -> ScentPolicy:
    """Reconstruct the exact signed scent policy from configuration."""
    scent = config.pheromones
    return ScentPolicy(
        center_intensity=scent.pheromone_center_intensity,
        decay=scent.pheromone_decay,
        decimal_places=scent.rounding.decimal_places,
        rounding=scent.rounding.mode,
    )


def evidence_digest(log: SubGameLogArtifact) -> str:
    """Digest replay-relevant immutable log linkage."""
    return sha256_digest(
        {
            "game_uid": log.game_uid,
            "sub_game_number": log.sub_game_number,
            "config_sha256": log.config_sha256,
            "journal_sha256": log.journal_sha256,
            "audit_sha256": log.audit_sha256,
            "commitments": [item.commitment_sha256 for item in log.entries],
        }
    )
