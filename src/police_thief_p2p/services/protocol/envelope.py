"""Immutable protocol envelope and response DTOs."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

from police_thief_p2p.domain.values import Role
from police_thief_p2p.shared.canonical_json import canonical_json_bytes, sha256_digest
from police_thief_p2p.shared.identifiers import CorrelationId, GameUid, GroupId, MessageId
from police_thief_p2p.shared.version import is_semantic_version

_MESSAGE_TYPE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class ProtocolModel(BaseModel):
    """Strict immutable base for wire models."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SenderIdentity(ProtocolModel):
    """Authenticated public sender identity."""

    group_id: StrictStr
    role: Role

    @field_validator("group_id")
    @classmethod
    def valid_group(cls, value: str) -> str:
        """Reject unsafe group identifiers."""
        return str(GroupId(value))


class ProtocolEnvelope(ProtocolModel):
    """Common request envelope for every session-bound tool."""

    protocol_version: StrictStr
    message_type: StrictStr
    message_id: StrictStr
    correlation_id: StrictStr
    game_uid: StrictStr
    sub_game_number: Annotated[StrictInt, Field(ge=1, le=2_147_483_647)]
    step_number: Annotated[StrictInt, Field(ge=1, le=2_147_483_647)]
    sender: SenderIdentity
    sequence: Annotated[StrictInt, Field(ge=1, le=2_147_483_647)]
    payload: dict[str, Any]

    @field_validator("protocol_version")
    @classmethod
    def semantic_protocol(cls, value: str) -> str:
        """Require a syntactically valid semantic version."""
        if not is_semantic_version(value):
            raise ValueError("protocol_version must be semantic")
        return value

    @field_validator("message_type")
    @classmethod
    def safe_message_type(cls, value: str) -> str:
        """Require a bounded lowercase tool identifier."""
        if _MESSAGE_TYPE.fullmatch(value) is None:
            raise ValueError("message_type is invalid")
        return value

    @field_validator("message_id")
    @classmethod
    def valid_message_id(cls, value: str) -> str:
        """Normalize the UUID-backed message identifier."""
        return str(MessageId(value))

    @field_validator("correlation_id")
    @classmethod
    def valid_correlation_id(cls, value: str) -> str:
        """Normalize the UUID-backed correlation identifier."""
        return str(CorrelationId(value))

    @field_validator("game_uid")
    @classmethod
    def valid_game_uid(cls, value: str) -> str:
        """Normalize the UUID-backed game identifier."""
        return str(GameUid(value))

    def canonical_bytes(self) -> bytes:
        """Return the exact deterministic request bytes used for retries."""
        return canonical_json_bytes(self.model_dump(mode="json"))

    def digest(self) -> str:
        """Return the canonical request digest."""
        return sha256_digest(self.model_dump(mode="json"))


class ProtocolResponse(ProtocolModel):
    """Safe deterministic response returned by every protocol tool."""

    ok: bool
    code: StrictStr
    message: StrictStr
    correlation_id: StrictStr | None
    payload: dict[str, Any] = Field(default_factory=dict)

    def canonical_bytes(self) -> bytes:
        """Return deterministic response bytes for durable replay."""
        return canonical_json_bytes(self.model_dump(mode="json"))
