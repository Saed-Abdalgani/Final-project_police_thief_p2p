"""Typed durable checkpoints and mutual recovery agreement."""

import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.shared.canonical_json import canonical_json_bytes, sha256_digest


@dataclass(frozen=True, slots=True)
class SessionCheckpoint:
    """Last mutually acknowledged, config/session-bound safe recovery state."""

    session_id: str
    config_sha256: str
    phase: GamePhase
    sub_game_number: int
    step_number: int
    journal_sequence: int
    journal_head_sha256: str
    last_acknowledged_commitment: str

    def document(self) -> dict[str, object]:
        """Return the canonical redacted checkpoint document."""
        return {
            "session_id": self.session_id,
            "config_sha256": self.config_sha256,
            "phase": self.phase.value,
            "sub_game_number": self.sub_game_number,
            "step_number": self.step_number,
            "journal_sequence": self.journal_sequence,
            "journal_head_sha256": self.journal_head_sha256,
            "last_acknowledged_commitment": self.last_acknowledged_commitment,
        }

    def digest(self) -> str:
        """Return exact canonical checkpoint identity."""
        return sha256_digest(self.document())


@runtime_checkable
class SessionStateRepositoryPort(Protocol):
    """Durably load/save one typed session checkpoint."""

    def load_checkpoint(self, session_id: str) -> SessionCheckpoint | None:
        """Load one checkpoint or return none."""
        ...

    def save_checkpoint(self, checkpoint: SessionCheckpoint) -> None:
        """Atomically persist one checkpoint."""
        ...


class ByteSessionRepository:
    """Typed checkpoint codec over the generic atomic byte repository."""

    __slots__ = ("_repository",)

    def __init__(self, repository: RepositoryPort) -> None:
        """Create a typed codec over private durable bytes."""
        self._repository = repository

    def load_checkpoint(self, session_id: str) -> SessionCheckpoint | None:
        """Decode and validate one exact session-bound checkpoint."""
        data = self._repository.load(self._key(session_id))
        if data is None:
            return None
        try:
            value = json.loads(data)
            checkpoint = SessionCheckpoint(
                session_id=str(value["session_id"]),
                config_sha256=str(value["config_sha256"]),
                phase=GamePhase(str(value["phase"])),
                sub_game_number=int(value["sub_game_number"]),
                step_number=int(value["step_number"]),
                journal_sequence=int(value["journal_sequence"]),
                journal_head_sha256=str(value["journal_head_sha256"]),
                last_acknowledged_commitment=str(value["last_acknowledged_commitment"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("stored session checkpoint is invalid") from exc
        if checkpoint.session_id != session_id:
            raise ValueError("stored checkpoint session differs")
        return checkpoint

    def save_checkpoint(self, checkpoint: SessionCheckpoint) -> None:
        """Persist canonical checkpoint bytes."""
        self._repository.save(
            self._key(checkpoint.session_id),
            canonical_json_bytes(checkpoint.document()),
        )

    @staticmethod
    def _key(session_id: str) -> str:
        digest = sha256_digest({"session_id": session_id})
        return f"session-{digest[:32]}"


def agree_recovery(
    local: SessionCheckpoint,
    remote_digest: str,
    *,
    config_sha256: str,
    session_id: str,
) -> SessionCheckpoint:
    """Resume only an exact mutual checkpoint; never invent or roll back state."""
    if local.config_sha256 != config_sha256 or local.session_id != session_id:
        raise ValueError("local recovery checkpoint context differs")
    if local.digest() != remote_digest:
        raise ValueError("peer recovery checkpoint differs")
    return local
