"""Persist-before-ack boundaries and deterministic crash injection."""

from collections.abc import Callable
from enum import StrEnum

from police_thief_p2p.services.orchestration.journal import OrchestrationJournal


class CrashPoint(StrEnum):
    """Injectable crash boundaries around durable mutation effects."""

    BEFORE_JOURNAL = "before-journal"
    AFTER_JOURNAL = "after-journal"
    BEFORE_ACK = "before-ack"
    AFTER_ACK = "after-ack"


CrashHook = Callable[[CrashPoint], None]


def persist_before_ack(
    journal: OrchestrationJournal,
    event_type: str,
    payload: dict[str, object],
    acknowledge: Callable[[], None],
    crash_hook: CrashHook | None = None,
) -> None:
    """Durably append an inbound mutation before its acknowledgement."""
    hook = (lambda _point: None) if crash_hook is None else crash_hook
    hook(CrashPoint.BEFORE_JOURNAL)
    journal.append(event_type, payload)
    hook(CrashPoint.AFTER_JOURNAL)
    hook(CrashPoint.BEFORE_ACK)
    acknowledge()
    hook(CrashPoint.AFTER_ACK)
