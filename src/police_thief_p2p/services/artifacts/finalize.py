"""Pure append-only-event to finalized-log derivation."""

from collections.abc import Iterable
from typing import Literal

from police_thief_p2p.services.artifacts.records import (
    RoleAssignmentRecord,
    SealedLogEntry,
    SubGameLogArtifact,
)


def finalize_log(
    *,
    game_id: str,
    game_uid: str,
    sub_game_number: int,
    role_assignment: RoleAssignmentRecord,
    config_sha256: str,
    played_commits: dict[str, str],
    journal_sha256: str,
    entries: Iterable[SealedLogEntry],
    terminal_reason: str,
    audit_status: Literal["verified", "failed"],
    audit_sha256: str,
) -> SubGameLogArtifact:
    """Derive an immutable ordered log without rewriting source evidence."""
    finalized = tuple(entries)
    expected = tuple(range(1, len(finalized) + 1))
    actual = tuple(item.sequence for item in finalized)
    if actual != expected:
        raise ValueError("log entries must have contiguous append-only sequence")
    if audit_status not in {"verified", "failed"}:
        raise ValueError("final log requires a terminal audit status")
    return SubGameLogArtifact(
        game_id=game_id,
        game_uid=game_uid,
        sub_game_number=sub_game_number,
        role_assignment=role_assignment,
        config_sha256=config_sha256,
        played_commits=played_commits,
        journal_sha256=journal_sha256,
        entries=finalized,
        terminal_reason=terminal_reason,
        audit_status=audit_status,
        audit_sha256=audit_sha256,
    )
