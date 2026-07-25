import json
from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence.atomic_files import AtomicFileRepository
from police_thief_p2p.services.orchestration.checkpoint import (
    ByteSessionRepository,
    SessionCheckpoint,
    agree_recovery,
)
from police_thief_p2p.services.orchestration.journal import OrchestrationJournal
from police_thief_p2p.services.orchestration.persistence import CrashPoint, persist_before_ack
from police_thief_p2p.services.orchestration.phases import GamePhase

DIGEST = "a" * 64


def _checkpoint(session: str = "session-a") -> SessionCheckpoint:
    return SessionCheckpoint(
        session,
        DIGEST,
        GamePhase.CHECKPOINTING,
        2,
        7,
        3,
        "b" * 64,
        "c" * 64,
    )


def test_append_only_journal_persists_monotonic_chain_and_restores(tmp_path: Path) -> None:
    repository = AtomicFileRepository(tmp_path)
    journal = OrchestrationJournal(repository, "orchestration")
    first = journal.append("phase", {"phase": "ready"})
    second = journal.append("ack", {"commitment": DIGEST})
    assert first.sequence == 1
    assert second.previous_sha256 == first.record_sha256
    restored = OrchestrationJournal(repository, "orchestration")
    assert restored.records == journal.records

    path = tmp_path / "orchestration.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value[0]["payload"]["phase"] = "tampered"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="chain"):
        OrchestrationJournal(repository, "orchestration")


def test_checkpoint_repository_is_session_isolated_and_mutual(tmp_path: Path) -> None:
    store = ByteSessionRepository(AtomicFileRepository(tmp_path))
    checkpoint = _checkpoint()
    store.save_checkpoint(checkpoint)
    assert store.load_checkpoint("session-a") == checkpoint
    assert store.load_checkpoint("session-b") is None
    assert (
        agree_recovery(
            checkpoint,
            checkpoint.digest(),
            config_sha256=DIGEST,
            session_id="session-a",
        )
        == checkpoint
    )
    with pytest.raises(ValueError, match="differs"):
        agree_recovery(
            checkpoint,
            "f" * 64,
            config_sha256=DIGEST,
            session_id="session-a",
        )


@pytest.mark.parametrize("crash_at", tuple(CrashPoint))
def test_persist_before_ack_crash_boundaries_never_ack_before_journal(
    tmp_path: Path,
    crash_at: CrashPoint,
) -> None:
    journal = OrchestrationJournal(AtomicFileRepository(tmp_path / crash_at.value), "events")
    acknowledged = False
    seen: list[CrashPoint] = []

    def hook(point: CrashPoint) -> None:
        seen.append(point)
        if point is crash_at:
            raise OSError("injected crash")

    def acknowledge() -> None:
        nonlocal acknowledged
        acknowledged = True

    with pytest.raises(OSError, match="injected"):
        persist_before_ack(journal, "mutation", {"safe": True}, acknowledge, hook)
    if acknowledged:
        assert journal.records
    if crash_at in {CrashPoint.BEFORE_JOURNAL}:
        assert not journal.records
    assert seen[0] is CrashPoint.BEFORE_JOURNAL
