"""Nonce-sealed capture claim and response without live position disclosure."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field

from pydantic import StrictBool, StrictInt, StrictStr, model_validator

from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.protocol.envelope import ProtocolModel
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


class CaptureStatement(ProtocolModel):
    """A context-bound claim or response containing no coordinates."""

    game_uid: StrictStr
    sub_game_number: StrictInt
    step_number: StrictInt
    action_commitment_sha256: StrictStr
    kind: str
    captured: StrictBool

    @model_validator(mode="after")
    def valid_kind(self) -> CaptureStatement:
        """Restrict message purpose to the claim/response handshake."""
        if self.kind not in {"claim", "response"}:
            raise ValueError("capture statement kind is invalid")
        return self


@dataclass(frozen=True, slots=True)
class SealedCapture:
    """Public digest with private final-audit statement and nonce."""

    statement: CaptureStatement
    nonce: SecretNonce

    def digest(self) -> str:
        """Commit the statement and nonce as canonical bytes."""
        value = self.statement.model_dump(mode="json")
        value["nonce"] = self.nonce.reveal_hex()
        return hashlib.sha256(canonical_json_bytes(value)).hexdigest()

    def verify(self, digest: str) -> bool:
        """Verify in constant time."""
        return secrets.compare_digest(self.digest(), digest)


@dataclass(frozen=True, slots=True)
class CaptureExchange:
    """Final-audit view of a matched claim and response pair."""

    claim: SealedCapture
    response: SealedCapture
    claim_commitment_sha256: str = field(default="")
    response_commitment_sha256: str = field(default="")

    def __post_init__(self) -> None:
        """Require an exact context-bound claim/response pair."""
        left = self.claim.statement
        right = self.response.statement
        context = (left.game_uid, left.sub_game_number, left.step_number)
        if left.kind != "claim" or right.kind != "response":
            raise ValueError("capture exchange requires claim then response")
        if context != (right.game_uid, right.sub_game_number, right.step_number):
            raise ValueError("capture response context differs")
        if left.action_commitment_sha256 != right.action_commitment_sha256:
            raise ValueError("capture response is tied to another action")
        if not self.claim_commitment_sha256:
            object.__setattr__(self, "claim_commitment_sha256", self.claim.digest())
        if not self.response_commitment_sha256:
            object.__setattr__(self, "response_commitment_sha256", self.response.digest())

    def commitments_are_valid(self) -> bool:
        """Verify both final capture payloads against their live commitments."""
        return self.claim.verify(self.claim_commitment_sha256) and self.response.verify(
            self.response_commitment_sha256
        )
