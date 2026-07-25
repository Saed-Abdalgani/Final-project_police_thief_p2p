"""Durable idempotency identity and write-ahead records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.services.protocol.envelope import ProtocolResponse
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


class RecordState(StrEnum):
    """Durable intent lifecycle."""

    PENDING = "pending"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """Exactly-once identity scoped by game, sender, and message ID."""

    game_uid: str
    sender_group: str
    message_id: str

    def storage_key(self) -> str:
        """Return a fixed safe, non-enumerating repository key."""
        value = f"{self.game_uid}:{self.sender_group}:{self.message_id}".encode()
        return f"idempotency-{hashlib.sha256(value).hexdigest()}"


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """Persisted request digest and optional completed response."""

    request_digest: str
    state: RecordState
    response: ProtocolResponse | None = None

    def to_bytes(self) -> bytes:
        """Serialize the record canonically."""
        return canonical_json_bytes(
            {
                "request_digest": self.request_digest,
                "state": self.state.value,
                "response": (
                    self.response.model_dump(mode="json") if self.response is not None else None
                ),
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> IdempotencyRecord:
        """Parse one trusted private record with strict required fields."""
        value: Any = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("idempotency record must be an object")
        response = value.get("response")
        return cls(
            request_digest=str(value["request_digest"]),
            state=RecordState(value["state"]),
            response=ProtocolResponse.model_validate(response) if response is not None else None,
        )


class IdempotencyRepository:
    """Persist intent before mutation and replay exact completed responses."""

    __slots__ = ("_records",)

    def __init__(self, records: RepositoryPort) -> None:
        """Bind an opaque atomic byte repository."""
        self._records = records

    def inspect(self, key: IdempotencyKey, request_digest: str) -> IdempotencyRecord | None:
        """Return a same-request record or reject identity reuse."""
        data = self._records.load(key.storage_key())
        if data is None:
            return None
        record = IdempotencyRecord.from_bytes(data)
        if record.request_digest != request_digest:
            raise ProtocolFailure(
                ProtocolErrorCode.CONFLICT,
                "message ID was reused with different request bytes",
            )
        return record

    def persist_intent(self, key: IdempotencyKey, request_digest: str) -> None:
        """Write the pending request intent before its effect."""
        record = IdempotencyRecord(request_digest, RecordState.PENDING)
        self._records.save(key.storage_key(), record.to_bytes())

    def persist_result(
        self,
        key: IdempotencyKey,
        request_digest: str,
        response: ProtocolResponse,
    ) -> None:
        """Write the completed result before returning acknowledgement."""
        record = IdempotencyRecord(request_digest, RecordState.COMPLETED, response)
        self._records.save(key.storage_key(), record.to_bytes())
