"""Amireman wire message shapes (exact official field names)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class TurnMessage:
    """One half-turn: commit on the wire; nonce withheld until audit."""

    step: int
    sender: str
    commit: str
    hint: str
    smell_grid: dict = field(default_factory=dict)
    timestamp: str = ""
    barrier_placed: list | None = None
    capture_claim: list | None = None
    claim_response: dict | None = None
    win_claim: dict | None = None

    def to_wire(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> TurnMessage:
        known = set(cls.__dataclass_fields__)
        missing = {"step", "sender", "commit"} - set(data)
        if missing:
            raise ValueError(f"turn message missing fields: {sorted(missing)}")
        return cls(**{key: value for key, value in data.items() if key in known})


@dataclass
class AuditPayload:
    """End-of-game reveal or series_consensus envelope."""

    sender: str
    records: list
    result_claim: str
    consensus_sha: str | None = None

    def to_wire(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if not (k == "consensus_sha" and v is None)}

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> AuditPayload:
        known = set(cls.__dataclass_fields__)
        payload = cls(**{key: value for key, value in data.items() if key in known})
        if payload.consensus_sha is not None and not _HEX64.match(str(payload.consensus_sha)):
            payload.consensus_sha = None
        return payload


@dataclass
class Negotiation:
    """Per-sub-game signed greeting."""

    terms: dict
    nonce: str
    signature: str
    group_id: str
    role: str | None = None
    sub_game_number: int | None = None
    identity: dict = field(default_factory=dict)
    game_uid: str | None = None

    def to_wire(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> Negotiation:
        known = set(cls.__dataclass_fields__)
        return cls(**{key: value for key, value in data.items() if key in known})
