"""Shared strict artifact model primitives."""

import re
from typing import Annotated

from pydantic import Field, StrictInt, StrictStr, field_validator

from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.identifiers import GameId, GameUid, GroupId
from police_thief_p2p.shared.version import SCHEMA_VERSION

Digest = Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
Commit = Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{40}$")]
_TIMESTAMP = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|\+00:00)$")


class ArtifactModel(FrozenModel):
    """Base for immutable schema-versioned series artifacts."""

    schema_version: StrictStr = SCHEMA_VERSION
    game_id: StrictStr
    game_uid: StrictStr

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        """Reject artifacts from unsupported schema families."""
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported artifact schema version {value}")
        return value

    @field_validator("game_id")
    @classmethod
    def valid_game_id(cls, value: str) -> str:
        """Require the Appendix F safe game slug."""
        return str(GameId(value))

    @field_validator("game_uid")
    @classmethod
    def valid_game_uid(cls, value: str) -> str:
        """Require a canonical UUID linkage identifier."""
        return str(GameUid(value))


class TokenUsage(FrozenModel):
    """Exact non-negative token accounting for one group and scope."""

    input_tokens: Annotated[StrictInt, Field(ge=0)] = 0
    output_tokens: Annotated[StrictInt, Field(ge=0)] = 0

    @property
    def total_tokens(self) -> int:
        """Return exact input plus output tokens."""
        return self.input_tokens + self.output_tokens


class GroupIdentity(FrozenModel):
    """Validated group identifier used in result records."""

    group_id: StrictStr

    @field_validator("group_id")
    @classmethod
    def valid_group(cls, value: str) -> str:
        """Reject unsafe or ambiguous group identifiers."""
        return str(GroupId(value))


def validate_timestamp(value: str) -> str:
    """Validate a timezone-explicit UTC artifact timestamp."""
    if _TIMESTAMP.fullmatch(value) is None:
        raise ValueError("timestamp must be an ISO-8601 UTC value")
    return value
