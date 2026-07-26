"""Fail-closed deterministic offline log verification."""

from pydantic import ValidationError

from police_thief_p2p.domain import Role
from police_thief_p2p.services.artifacts.records import (
    PlayedConfigArtifact,
    SealedLogEntry,
    SubGameLogArtifact,
)
from police_thief_p2p.services.crypto.scent_evidence import scent_model_digest
from police_thief_p2p.services.replay.models import (
    ReplayFinding,
    ReplayMode,
    ReplayVerification,
)
from police_thief_p2p.services.replay.outcome import (
    failed_result,
    finalize_result,
    scent_policy,
)
from police_thief_p2p.services.replay.reveal import ReplayReveal
from police_thief_p2p.services.replay.steps import ReplayMachine
from police_thief_p2p.shared.config_models import SharedConfig


def verify_replay_log(
    log: SubGameLogArtifact,
    config_artifact: PlayedConfigArtifact,
    *,
    mode: ReplayMode,
    viewer_group: str,
) -> ReplayVerification:
    """Recompute commitments, transitions, terminal truth, and score."""
    config, finding = _preflight(log, config_artifact, viewer_group)
    expected = _reveal_count(log)
    if finding is not None or config is None:
        return failed_result(log, mode, (), 0, expected, finding)
    viewer_role = (
        Role.POLICE if config_artifact.role_assignment.police == viewer_group else Role.THIEF
    )
    policy = scent_policy(config)
    machine = ReplayMachine(config, viewer_role, mode)
    verified = 0
    terminal_seen = False
    for expected_sequence, entry in enumerate(log.entries, start=1):
        finding = _entry_order_finding(entry, expected_sequence)
        if finding is not None:
            return failed_result(log, mode, tuple(machine.frames), verified, expected, finding)
        if entry.phase != "reveal":
            continue
        if terminal_seen:
            finding = ReplayFinding(
                1,
                "POST_TERMINAL",
                f"entry:{entry.sequence}",
                "step follows terminal",
            )
            return failed_result(log, mode, tuple(machine.frames), verified, expected, finding)
        reveal, finding = _parse_reveal(entry)
        if finding is not None or reveal is None:
            return failed_result(log, mode, tuple(machine.frames), verified, expected, finding)
        finding = machine.verify_step(
            entry,
            reveal,
            log.game_uid,
            log.sub_game_number,
            log.config_sha256,
            scent_model_digest(policy),
            policy,
        )
        if finding is not None:
            return failed_result(log, mode, tuple(machine.frames), verified, expected, finding)
        verified += 1
        terminal_seen = machine.frames[-1].terminal_reason is not None
    return finalize_result(log, mode, machine, verified, expected)


def _preflight(
    log: SubGameLogArtifact,
    artifact: PlayedConfigArtifact,
    viewer_group: str,
) -> tuple[SharedConfig | None, ReplayFinding | None]:
    try:
        config = SharedConfig.model_validate(artifact.shared_config)
    except ValidationError:
        return None, ReplayFinding(1, "CONFIG", "shared-config", "configuration is invalid")
    if config.digest() != artifact.config_sha256:
        return None, ReplayFinding(1, "CONFIG_DIGEST", "shared-config", "digest differs")
    participants = {artifact.role_assignment.police, artifact.role_assignment.thief}
    if viewer_group not in participants:
        return None, ReplayFinding(1, "VIEWER", "role-assignment", "viewer is not a participant")
    if log.audit_status != "verified" or any(
        item.audit_status != "verified" for item in log.entries
    ):
        return None, ReplayFinding(1, "AUDIT_GATE", "log", "final audit is not verified")
    return config, None


def _entry_order_finding(
    entry: SealedLogEntry,
    expected_sequence: int,
) -> ReplayFinding | None:
    if entry.sequence == expected_sequence:
        return None
    return ReplayFinding(1, "ENTRY_ORDER", f"entry:{expected_sequence}", "gap")


def _parse_reveal(
    entry: SealedLogEntry,
) -> tuple[ReplayReveal | None, ReplayFinding | None]:
    if entry.reveal is None or entry.commitment_sha256 is None:
        return None, ReplayFinding(
            1,
            "REVEAL",
            f"entry:{entry.sequence}",
            "reveal is missing",
        )
    try:
        return ReplayReveal.model_validate(entry.reveal), None
    except ValidationError:
        return None, ReplayFinding(
            1,
            "REVEAL",
            f"entry:{entry.sequence}",
            "reveal is invalid",
        )


def _reveal_count(log: SubGameLogArtifact) -> int:
    return sum(item.phase == "reveal" for item in log.entries)
