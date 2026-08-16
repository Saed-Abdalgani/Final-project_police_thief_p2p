"""Amireman wire message shapes (exact official field names)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
TURN_KEYS: tuple[str, ...] = (
    "step",
    "sender",
    "hint",
    "smell_grid",
    "commit",
    "timestamp",
    "barrier_placed",
    "capture_claim",
    "claim_response",
    "win_claim",
)


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
        """Serialize the fixed turn schema."""
        raw = asdict(self)
        return {key: raw[key] for key in TURN_KEYS}

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> TurnMessage:
        """Validate and parse one fixed-schema turn."""
        known = set(cls.__dataclass_fields__)
        missing = {"step", "sender", "commit"} - set(data)
        if missing:
            raise ValueError(f"turn message missing fields: {sorted(missing)}")
        filtered = {key: value for key, value in data.items() if key in known}
        if filtered.get("hint") is None:
            filtered["hint"] = ""
        if filtered.get("smell_grid") is None:
            filtered["smell_grid"] = {}
        return cls(**filtered)


CONSENSUS_TAG = "series_consensus"


def is_series_consensus(data: dict[str, Any] | AuditPayload) -> bool:
    """True for the end-of-series digest envelope, not a per-sub-game reveal."""
    if isinstance(data, AuditPayload):
        claim, sha, records = data.result_claim, data.consensus_sha, data.records
    else:
        claim, sha, records = (
            data.get("result_claim"),
            data.get("consensus_sha"),
            data.get("records"),
        )
    if claim == CONSENSUS_TAG:
        return True
    return bool(sha) and records == []


@dataclass
class AuditPayload:
    """End-of-game reveal or series_consensus envelope."""

    sender: str
    records: list
    result_claim: str
    consensus_sha: str | None = None
    sub_game: int | None = None
    sub_game_number: int | None = None

    def to_wire(self) -> dict[str, Any]:
        """Serialize non-null audit fields."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> AuditPayload:
        """Parse and normalize an audit or consensus payload."""
        known = set(cls.__dataclass_fields__)
        payload = cls(**{key: value for key, value in data.items() if key in known})
        if payload.consensus_sha is not None and not _HEX64.match(str(payload.consensus_sha)):
            payload.consensus_sha = None
        for key in ("sub_game", "sub_game_number"):
            value = getattr(payload, key)
            if value is not None:
                setattr(payload, key, int(value))
        if payload.sub_game is None:
            payload.sub_game = payload.sub_game_number
        if payload.sub_game_number is None:
            payload.sub_game_number = payload.sub_game
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
    config_sha256: str | None = None
    scent_model_sha256: str | None = None
    code_version: str | None = None
    first_mover: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Serialize non-null negotiation fields."""
        return {key: value for key, value in asdict(self).items() if value is not None}

    @classmethod
    def from_wire(cls, data: dict[str, Any]) -> Negotiation:
        """Parse known negotiation fields while ignoring extensions."""
        known = set(cls.__dataclass_fields__)
        return cls(**{key: value for key, value in data.items() if key in known})
