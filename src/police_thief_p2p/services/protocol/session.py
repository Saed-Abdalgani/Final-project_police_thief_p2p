"""Durable protocol session snapshots and in-memory registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.services.protocol.envelope import ProtocolResponse
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure
from police_thief_p2p.services.protocol.negotiation_models import MatchProposal
from police_thief_p2p.services.protocol.phases import ProtocolPhase
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


@dataclass(slots=True)
class ProtocolSession:
    """One peer's local protocol truth and durable effect receipts."""

    game_uid: str
    local_group: str
    remote_group: str
    proposal: MatchProposal
    phase: ProtocolPhase = ProtocolPhase.NEGOTIATING
    next_sequences: dict[str, int] = field(default_factory=dict)
    effects: dict[str, ProtocolResponse] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        """Serialize a deterministic restart snapshot."""
        return canonical_json_bytes(
            {
                "game_uid": self.game_uid,
                "local_group": self.local_group,
                "remote_group": self.remote_group,
                "proposal": self.proposal.model_dump(mode="json"),
                "phase": self.phase.value,
                "next_sequences": self.next_sequences,
                "effects": {
                    key: value.model_dump(mode="json")
                    for key, value in sorted(self.effects.items())
                },
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> ProtocolSession:
        """Restore one trusted private session snapshot."""
        value: Any = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("session snapshot must be an object")
        return cls(
            game_uid=str(value["game_uid"]),
            local_group=str(value["local_group"]),
            remote_group=str(value["remote_group"]),
            proposal=MatchProposal.model_validate(value["proposal"]),
            phase=ProtocolPhase(value["phase"]),
            next_sequences={str(key): int(item) for key, item in value["next_sequences"].items()},
            effects={
                str(key): ProtocolResponse.model_validate(item)
                for key, item in value["effects"].items()
            },
        )


class SessionRegistry:
    """In-memory registry backed by isolated durable snapshots."""

    __slots__ = ("_local_group", "_max_cached_sessions", "_records", "_sessions")

    def __init__(
        self,
        local_group: str,
        records: RepositoryPort,
        max_cached_sessions: int = 32,
    ) -> None:
        """Bind one local identity and private record repository."""
        if type(max_cached_sessions) is not int or max_cached_sessions < 1:
            raise ValueError("session cache limit must be a positive integer")
        self._local_group = local_group
        self._records = records
        self._max_cached_sessions = max_cached_sessions
        self._sessions: dict[str, ProtocolSession] = {}

    def create(self, proposal: MatchProposal, remote_group: str) -> ProtocolSession:
        """Create and persist a previously unknown negotiated session."""
        if self.get_optional(proposal.game_uid) is not None:
            raise ProtocolFailure(ProtocolErrorCode.CONFLICT, "session already exists")
        session = ProtocolSession(
            proposal.game_uid,
            self._local_group,
            remote_group,
            proposal,
            next_sequences={remote_group: 1},
        )
        self.persist(session)
        return session

    def get(self, game_uid: str) -> ProtocolSession:
        """Return a known session without exposing registry contents."""
        session = self.get_optional(game_uid)
        if session is None:
            raise ProtocolFailure(ProtocolErrorCode.UNKNOWN_SESSION, "unknown game session")
        return session

    def get_optional(self, game_uid: str) -> ProtocolSession | None:
        """Return a memory or durable session when present."""
        if game_uid in self._sessions:
            return self._sessions[game_uid]
        data = self._records.load(f"session-{game_uid}")
        if data is None:
            return None
        session = ProtocolSession.from_bytes(data)
        self._cache(session)
        return session

    def persist(self, session: ProtocolSession) -> None:
        """Persist before publishing the updated in-memory view."""
        self._records.save(f"session-{session.game_uid}", session.to_bytes())
        self._cache(session)

    @property
    def cached_session_count(self) -> int:
        """Return bounded in-memory session retention for diagnostics."""
        return len(self._sessions)

    def _cache(self, session: ProtocolSession) -> None:
        if (
            session.game_uid not in self._sessions
            and len(self._sessions) >= self._max_cached_sessions
        ):
            self._sessions.pop(next(iter(self._sessions)))
        self._sessions[session.game_uid] = session
