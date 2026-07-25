"""Versioned immutable commitment and reveal payloads."""

from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from typing import Annotated, Literal, Self

from pydantic import Field, StrictInt, StrictStr, model_validator

from police_thief_p2p.domain.values import Action, ActionType, Direction, Role
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.protocol.envelope import ProtocolModel
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.identifiers import GameUid

_DIGEST = re.compile(r"^[a-f0-9]{64}$")


class CommittedAction(ProtocolModel):
    """Canonical action representation independent of Python object layout."""

    action_type: ActionType
    direction: Direction | None = None
    target: tuple[StrictInt, StrictInt] | None = None

    @model_validator(mode="after")
    def valid_shape(self) -> Self:
        """Require exactly the fields belonging to MOVE, STAY, or BARRIER."""
        valid = {
            ActionType.MOVE: self.direction is not None and self.target is None,
            ActionType.STAY: self.direction is None and self.target is None,
            ActionType.BARRIER: self.direction is None and self.target is not None,
        }
        if not valid[self.action_type]:
            raise ValueError("committed action fields are inconsistent")
        return self

    @classmethod
    def from_domain(cls, action: Action) -> CommittedAction:
        """Convert one validated domain action to canonical wire shape."""
        target = None
        if action.target is not None:
            target = (action.target.row, action.target.col)
        return cls(
            action_type=action.action_type,
            direction=action.direction,
            target=target,
        )


class PublicEffect(ProtocolModel):
    """Outcome-relevant public effect sealed with one step."""

    effect_type: Literal["barrier_placed"]
    target: tuple[StrictInt, StrictInt]


class CommitmentBody(ProtocolModel):
    """Every public and private outcome-relevant field except the nonce."""

    commitment_version: Literal["1.1.0"] = "1.1.0"
    game_uid: StrictStr
    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    step_number: Annotated[StrictInt, Field(ge=1, le=2_147_483_647)]
    actor: Role
    pre_action_state_digest: StrictStr
    action: CommittedAction
    hint: Annotated[StrictStr, Field(max_length=2_000)]
    verdict: Literal["truth", "lie"]
    hint_semantic_intent: Literal[
        "north", "south", "east", "west", "center", "edge", "corner", "neutral"
    ]
    public_effects: tuple[PublicEffect, ...] = ()
    token_count: Annotated[StrictInt, Field(ge=0)]
    model_provider: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    model_name: Annotated[StrictStr, Field(min_length=1, max_length=200)]
    config_sha256: StrictStr
    protocol_version: StrictStr
    scent_model_sha256: StrictStr
    scent_frame_sha256: StrictStr

    @model_validator(mode="after")
    def valid_identity_and_digests(self) -> Self:
        """Validate the game UUID and every bound SHA-256 field."""
        GameUid(self.game_uid)
        for value in (
            self.pre_action_state_digest,
            self.config_sha256,
            self.scent_model_sha256,
            self.scent_frame_sha256,
        ):
            if _DIGEST.fullmatch(value) is None:
                raise ValueError("commitment digest field is invalid")
        return self


@dataclass(frozen=True, slots=True)
class CommitmentPayload:
    """A complete local sealed payload including its opaque nonce."""

    body: CommitmentBody
    nonce: SecretNonce

    def __post_init__(self) -> None:
        """Require typed immutable body and secret nonce."""
        if not isinstance(self.body, CommitmentBody):
            raise TypeError("commitment body is invalid")
        if not isinstance(self.nonce, SecretNonce):
            raise TypeError("commitment nonce is invalid")

    def canonical_bytes(self) -> bytes:
        """Return platform-independent signed bytes including the nonce."""
        value = self.body.model_dump(mode="json")
        value["nonce"] = self.nonce.reveal_hex()
        return canonical_json_bytes(value)

    def digest(self) -> str:
        """Return the public lowercase SHA-256 commitment."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


class PublicCommitment(ProtocolModel):
    """Commit-phase DTO containing identity and digest only."""

    game_uid: StrictStr
    sub_game_number: StrictInt
    step_number: StrictInt
    actor: Role
    commitment_sha256: StrictStr


class LiveReveal(ProtocolModel):
    """Post-ack reveal containing the body and deliberately no nonce field."""

    body: CommitmentBody
    commitment_sha256: StrictStr


def verify_commitment(payload: CommitmentPayload, expected_digest: str) -> bool:
    """Compare the recomputed digest in constant time."""
    return secrets.compare_digest(payload.digest(), expected_digest)
