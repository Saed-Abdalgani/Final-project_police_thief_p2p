"""Append-only canonical JSON orchestration journal with local hash chain."""

import json
from dataclasses import dataclass

from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.shared.canonical_json import canonical_json_bytes, sha256_digest

_GENESIS = "0" * 64


@dataclass(frozen=True, slots=True)
class JournalRecord:
    """One monotonic immutable orchestration event."""

    sequence: int
    event_type: str
    payload: dict[str, object]
    previous_sha256: str
    record_sha256: str

    def unsigned(self) -> dict[str, object]:
        """Return fields covered by the record hash."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "payload": self.payload,
            "previous_sha256": self.previous_sha256,
        }

    def document(self) -> dict[str, object]:
        """Return the complete persisted record."""
        return {**self.unsigned(), "record_sha256": self.record_sha256}


class OrchestrationJournal:
    """Persist and verify an append-only journal through an injected repository."""

    __slots__ = ("_key", "_records", "_repository")

    def __init__(self, repository: RepositoryPort, key: str) -> None:
        """Load and validate the selected private journal."""
        self._repository = repository
        self._key = key
        self._records = self._load()

    @property
    def records(self) -> tuple[JournalRecord, ...]:
        """Return immutable journal records."""
        return self._records

    @property
    def head_sha256(self) -> str:
        """Return current chain head or genesis."""
        return _GENESIS if not self._records else self._records[-1].record_sha256

    def append(self, event_type: str, payload: dict[str, object]) -> JournalRecord:
        """Persist a new monotonic record before returning it."""
        if not event_type or len(event_type) > 64:
            raise ValueError("journal event type is invalid")
        sequence = len(self._records) + 1
        unsigned = {
            "sequence": sequence,
            "event_type": event_type,
            "payload": payload,
            "previous_sha256": self.head_sha256,
        }
        record = JournalRecord(
            sequence=sequence,
            event_type=event_type,
            payload=payload,
            previous_sha256=self.head_sha256,
            record_sha256=sha256_digest(unsigned),
        )
        candidate = (*self._records, record)
        self._repository.save(
            self._key,
            canonical_json_bytes([item.document() for item in candidate]),
        )
        self._records = candidate
        return record

    def _load(self) -> tuple[JournalRecord, ...]:
        data = self._repository.load(self._key)
        if data is None:
            return ()
        try:
            values = json.loads(data)
            records = tuple(
                JournalRecord(
                    sequence=int(value["sequence"]),
                    event_type=str(value["event_type"]),
                    payload=dict(value["payload"]),
                    previous_sha256=str(value["previous_sha256"]),
                    record_sha256=str(value["record_sha256"]),
                )
                for value in values
            )
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError("stored orchestration journal is invalid") from exc
        self._validate(records)
        return records

    @staticmethod
    def _validate(records: tuple[JournalRecord, ...]) -> None:
        previous = _GENESIS
        for expected, record in enumerate(records, start=1):
            if (
                record.sequence != expected
                or record.previous_sha256 != previous
                or record.record_sha256 != sha256_digest(record.unsigned())
            ):
                raise ValueError("orchestration journal chain is invalid")
            previous = record.record_sha256
