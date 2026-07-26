"""Agreed final-series result and exact group accounting."""

from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, StrictInt, StrictStr, field_validator

from police_thief_p2p.services.artifacts.common import (
    ArtifactModel,
    Commit,
    Digest,
    TokenUsage,
)
from police_thief_p2p.services.artifacts.records import RoleAssignmentRecord
from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.identifiers import GroupId


class SubGameResult(FrozenModel):
    """One linked, audited sub-game outcome."""

    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    role_assignment: RoleAssignmentRecord
    terminal_reason: StrictStr
    winner: StrictStr | None
    tie: bool
    scores: dict[str, Annotated[StrictInt, Field(ge=0)]]
    tokens: dict[str, TokenUsage]
    config_sha256: Digest
    log_sha256: Digest
    audit_sha256: Digest
    commits: dict[str, Commit]
    config_file: StrictStr
    log_file: StrictStr
    audit_status: Literal["verified", "failed"]


class GroupResult(FrozenModel):
    """Series totals and repository evidence for one group."""

    group_id: StrictStr
    score: Annotated[StrictInt, Field(ge=0)]
    wins: Annotated[StrictInt, Field(ge=0, le=6)]
    ties: Annotated[StrictInt, Field(ge=0, le=6)]
    tokens: TokenUsage
    police_repository: AnyHttpUrl
    thief_repository: AnyHttpUrl
    police_commit: Commit
    thief_commit: Commit

    @field_validator("group_id")
    @classmethod
    def valid_group(cls, value: str) -> str:
        """Require a safe group identifier."""
        return str(GroupId(value))


class ResultAgreement(FrozenModel):
    """Mutual confirmation required before outbox admission."""

    status: Literal["agreed"]
    agreed_digest: Digest
    signers: Annotated[tuple[StrictStr, StrictStr], Field(min_length=2, max_length=2)]
    audit_manifest_sha256: Digest


class FinalResultArtifact(ArtifactModel):
    """One standard JSON report source with no provider state."""

    sender_group_id: StrictStr
    sub_games: Annotated[tuple[SubGameResult, ...], Field(min_length=6, max_length=6)]
    groups: Annotated[tuple[GroupResult, GroupResult], Field(min_length=2, max_length=2)]
    series_winner: StrictStr | None
    series_tie: bool
    declaration_file: StrictStr
    declaration_sha256: Digest
    agreement: ResultAgreement

    @field_validator("sender_group_id")
    @classmethod
    def valid_sender(cls, value: str) -> str:
        """Require an attributable independent sender."""
        return str(GroupId(value))
