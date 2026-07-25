"""Strict match-proposal, agreement, and league-ledger models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Annotated, Self

from pydantic import (
    Field,
    HttpUrl,
    StrictBool,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.protocol.declaration import StepZeroDeclaration
from police_thief_p2p.services.protocol.envelope import ProtocolModel
from police_thief_p2p.shared.canonical_json import canonical_json_bytes, sha256_digest
from police_thief_p2p.shared.identifiers import GameId, GameUid, GroupId

_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")


class RepositoryLinks(ProtocolModel):
    """The two standalone role repository URLs for one group."""

    police: HttpUrl
    thief: HttpUrl

    @model_validator(mode="after")
    def safe_https(self) -> Self:
        """Forbid credentials, non-HTTPS repositories, and duplicate links."""
        links = (self.police, self.thief)
        if any(url.scheme != "https" or url.username or url.password for url in links):
            raise ValueError("repository URLs must be credential-free HTTPS")
        if str(self.police) == str(self.thief):
            raise ValueError("police and thief repository URLs must differ")
        return self


class PlayedCommits(ProtocolModel):
    """Exact clean Git commits for both standalone role artifacts."""

    police: StrictStr
    thief: StrictStr

    @field_validator("police", "thief")
    @classmethod
    def exact_sha(cls, value: str) -> str:
        """Require a full lowercase 40-hex commit identifier."""
        if _COMMIT.fullmatch(value) is None:
            raise ValueError("played commit must be a full lowercase Git SHA-1")
        return value


class Participant(ProtocolModel):
    """One group's public identity, URLs, commits, and ledger declaration."""

    group_name: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    group_id: StrictStr
    members: Annotated[tuple[StrictStr, ...], Field(min_length=1, max_length=32)]
    repositories: RepositoryLinks
    commits: PlayedCommits
    public_mcp_url: HttpUrl
    role_capabilities: tuple[Role, ...]
    counted_total: Annotated[StrictInt, Field(ge=0, le=2_147_483_647)]
    counted_opponents: tuple[StrictStr, ...] = ()

    @model_validator(mode="after")
    def valid_identity_and_links(self) -> Self:
        """Validate identity, endpoint safety, roles, and ledger shape."""
        GroupId(self.group_id)
        if self.public_mcp_url.username or self.public_mcp_url.password:
            raise ValueError("public MCP URL must not contain credentials")
        if set(self.role_capabilities) != {Role.POLICE, Role.THIEF}:
            raise ValueError("both role capabilities are required")
        for opponent in self.counted_opponents:
            GroupId(opponent)
        if len(set(self.counted_opponents)) != len(self.counted_opponents):
            raise ValueError("counted opponents must be unique")
        if self.counted_total != len(self.counted_opponents):
            raise ValueError("counted total must equal the declared opponent ledger")
        return self


class RoleTerm(ProtocolModel):
    """One immutable role assignment in the negotiated six-game schedule."""

    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    police_group: StrictStr
    thief_group: StrictStr


class MatchProposal(ProtocolModel):
    """Complete fail-closed match proposal exchanged by both peers."""

    protocol_version: StrictStr
    schema_version: StrictStr
    game_id: StrictStr
    game_uid: StrictStr
    counted: StrictBool
    warmup_name: Annotated[StrictStr, Field(min_length=1, max_length=100)] | None
    participants: Annotated[tuple[Participant, Participant], Field(min_length=2, max_length=2)]
    config_raw_b64: StrictStr
    raw_config_sha256: StrictStr
    config_sha256: StrictStr
    scent_model_sha256: StrictStr
    scent_vector_version: StrictStr
    role_schedule: Annotated[tuple[RoleTerm, ...], Field(min_length=6, max_length=6)]
    declarations: Annotated[
        tuple[StepZeroDeclaration, StepZeroDeclaration], Field(min_length=2, max_length=2)
    ]
    optional_capabilities: dict[str, object] = Field(default_factory=dict)

    @field_validator("game_id")
    @classmethod
    def valid_game_id(cls, value: str) -> str:
        """Require a safe deterministic game slug."""
        return str(GameId(value))

    @field_validator("game_uid")
    @classmethod
    def valid_uid(cls, value: str) -> str:
        """Require a canonical game UUID."""
        return str(GameUid(value))

    @field_validator("raw_config_sha256", "config_sha256", "scent_model_sha256")
    @classmethod
    def digest_shape(cls, value: str) -> str:
        """Require lowercase SHA-256 digests."""
        if _DIGEST.fullmatch(value) is None:
            raise ValueError("digest must contain 64 lowercase hex characters")
        return value

    @model_validator(mode="after")
    def coherent_terms(self) -> Self:
        """Reject duplicate participants and ambiguous counted/warmup terms."""
        groups = tuple(item.group_id for item in self.participants)
        if groups[0] == groups[1]:
            raise ValueError("proposal participants must be distinct")
        if self.counted == (self.warmup_name is not None):
            raise ValueError("exactly one of counted mode or a named warmup is required")
        if tuple(item.group_id for item in self.declarations) != groups:
            raise ValueError("declarations must follow participant order")
        return self

    def digest(self) -> str:
        """Return the exact proposal digest required for acceptance."""
        return sha256_digest(self.model_dump(mode="json"))

    def canonical_bytes(self) -> bytes:
        """Return canonical proposal bytes."""
        return canonical_json_bytes(self.model_dump(mode="json"))


class MatchAcceptance(ProtocolModel):
    """Exact acceptance of a previously validated proposal."""

    proposal_digest: StrictStr
    game_id: StrictStr
    game_uid: StrictStr
    schedule_digest: StrictStr


@dataclass(frozen=True, slots=True)
class CountedLedger:
    """Immutable local source of truth for prior counted opponents."""

    opponents: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Validate every locally persisted opponent identity."""
        for opponent in self.opponents:
            GroupId(opponent)

    @property
    def total(self) -> int:
        """Return the exact number of prior distinct counted opponents."""
        return len(self.opponents)
