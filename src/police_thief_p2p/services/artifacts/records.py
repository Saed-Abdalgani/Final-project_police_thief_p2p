"""Exact played configuration and sealed finalized-log artifacts."""

from typing import Annotated, Literal

from pydantic import Field, StrictInt, StrictStr, field_validator

from police_thief_p2p.services.artifacts.common import (
    ArtifactModel,
    Commit,
    Digest,
    TokenUsage,
    validate_timestamp,
)
from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.identifiers import GroupId


class RoleAssignmentRecord(FrozenModel):
    """Exact group-to-role assignment for a sub-game."""

    police: StrictStr
    thief: StrictStr

    @field_validator("police", "thief")
    @classmethod
    def valid_group(cls, value: str) -> str:
        """Require a safe group identifier."""
        return str(GroupId(value))


class AgreementRecord(FrozenModel):
    """Identities and time associated with config agreement."""

    signers: Annotated[tuple[StrictStr, StrictStr], Field(min_length=2, max_length=2)]
    agreed_at: StrictStr
    agreement_sha256: Digest

    @field_validator("agreed_at")
    @classmethod
    def timestamp(cls, value: str) -> str:
        """Require a portable UTC timestamp."""
        return validate_timestamp(value)


class PlayedConfigArtifact(ArtifactModel):
    """Exact shared configuration played in one sub-game."""

    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    role_assignment: RoleAssignmentRecord
    config_sha256: Digest
    raw_config_sha256: Digest
    played_commits: dict[str, Commit]
    agreement: AgreementRecord
    shared_config: dict[str, object]


class SealedLogEntry(FrozenModel):
    """One immutable public event enriched after terminal audit."""

    sequence: Annotated[StrictInt, Field(ge=1)]
    step_number: Annotated[StrictInt, Field(ge=1)]
    phase: Literal["commit", "acknowledge", "reveal", "terminal", "audit"]
    actor: Literal["police", "thief", "system"]
    timestamp: StrictStr
    commitment_sha256: Digest | None = None
    reveal: dict[str, object] | None = None
    public_effects: dict[str, object] = Field(default_factory=dict)
    metrics: dict[str, TokenUsage] = Field(default_factory=dict)
    audit_status: Literal["pending", "verified", "failed"]

    @field_validator("timestamp")
    @classmethod
    def valid_time(cls, value: str) -> str:
        """Require a portable UTC timestamp."""
        return validate_timestamp(value)


class SubGameLogArtifact(ArtifactModel):
    """Ordered finalized evidence for one audited sub-game."""

    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    role_assignment: RoleAssignmentRecord
    config_sha256: Digest
    played_commits: dict[str, Commit]
    journal_sha256: Digest
    entries: tuple[SealedLogEntry, ...]
    terminal_reason: StrictStr
    audit_status: Literal["verified", "failed"]
    audit_sha256: Digest
