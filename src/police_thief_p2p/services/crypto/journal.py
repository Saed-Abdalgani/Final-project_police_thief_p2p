"""Immutable hash-chained local event journal."""

from dataclasses import dataclass

from police_thief_p2p.shared.canonical_json import sha256_digest

GENESIS_DIGEST = "0" * 64


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """One canonical event linked to the exact previous entry."""

    index: int
    event_type: str
    payload_sha256: str
    previous_sha256: str
    entry_sha256: str

    @classmethod
    def create(
        cls,
        index: int,
        event_type: str,
        payload: object,
        previous_sha256: str,
    ) -> "JournalEntry":
        """Create a linked entry from canonical payload evidence."""
        payload_digest = sha256_digest(payload)
        entry_digest = sha256_digest(
            {
                "index": index,
                "event_type": event_type,
                "payload_sha256": payload_digest,
                "previous_sha256": previous_sha256,
            }
        )
        return cls(index, event_type, payload_digest, previous_sha256, entry_digest)


class EventJournal:
    """Append-only journal with deterministic offline verification."""

    __slots__ = ("_entries",)

    def __init__(self) -> None:
        """Create an empty chain rooted at the fixed genesis digest."""
        self._entries: list[JournalEntry] = []

    def append(self, event_type: str, payload: object) -> JournalEntry:
        """Append one immutable event."""
        previous = self._entries[-1].entry_sha256 if self._entries else GENESIS_DIGEST
        entry = JournalEntry.create(len(self._entries) + 1, event_type, payload, previous)
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> tuple[JournalEntry, ...]:
        """Return an immutable snapshot."""
        return tuple(self._entries)


def verify_journal(entries: tuple[JournalEntry, ...]) -> bool:
    """Detect removal, reordering, modification, or broken linkage."""
    previous = GENESIS_DIGEST
    for index, entry in enumerate(entries, start=1):
        expected = sha256_digest(
            {
                "index": index,
                "event_type": entry.event_type,
                "payload_sha256": entry.payload_sha256,
                "previous_sha256": previous,
            }
        )
        if (
            entry.index != index
            or entry.previous_sha256 != previous
            or entry.entry_sha256 != expected
        ):
            return False
        previous = entry.entry_sha256
    return True
