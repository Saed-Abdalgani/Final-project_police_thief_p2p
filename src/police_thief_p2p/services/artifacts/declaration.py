"""Series declaration artifact assembled from negotiated public evidence."""

from typing import Annotated, Literal

from pydantic import (
    AnyHttpUrl,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from police_thief_p2p.services.artifacts.common import (
    ArtifactModel,
    Commit,
    Digest,
    validate_timestamp,
)
from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.identifiers import GroupId
from police_thief_p2p.shared.version import PROTOCOL_VERSION


class DeclarationGroup(FrozenModel):
    """One group's public identity, repositories, Step-0, and budget."""

    group_id: StrictStr
    group_name: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    members: Annotated[tuple[StrictStr, ...], Field(min_length=1, max_length=32)]
    public_mcp_url: AnyHttpUrl
    police_repository: AnyHttpUrl
    thief_repository: AnyHttpUrl
    police_commit: Commit
    thief_commit: Commit
    step_zero_sha256: Digest
    hardware_sha256: Digest
    model_provider: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    model_name: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    token_budget: Annotated[StrictInt, Field(ge=0)]
    counted_total: Annotated[StrictInt, Field(ge=0)]

    @field_validator("group_id")
    @classmethod
    def valid_group(cls, value: str) -> str:
        """Require a safe group identity."""
        return str(GroupId(value))


class SeriesDeclaration(ArtifactModel):
    """One mutually acknowledged declaration for the whole series."""

    protocol_version: Literal["0.7.0"] = PROTOCOL_VERSION
    timezone: Annotated[StrictStr, Field(min_length=1, max_length=100)]
    counted: StrictBool
    mode: Literal["counted", "warmup"]
    groups: Annotated[tuple[DeclarationGroup, DeclarationGroup], Field(min_length=2, max_length=2)]
    series_size: Literal[6] = 6
    planned_start: StrictStr
    planned_end: StrictStr
    config_sha256: Digest
    scent_model_sha256: Digest
    schedule_sha256: Digest
    acknowledgment_sha256: Digest

    @field_validator("planned_start", "planned_end")
    @classmethod
    def timestamp(cls, value: str) -> str:
        """Require portable UTC timestamps."""
        return validate_timestamp(value)

    @field_validator("groups")
    @classmethod
    def distinct_groups(
        cls, value: tuple[DeclarationGroup, DeclarationGroup]
    ) -> tuple[DeclarationGroup, DeclarationGroup]:
        """Require exactly two distinct negotiated groups."""
        if value[0].group_id == value[1].group_id:
            raise ValueError("declaration groups must be distinct")
        return value

    @model_validator(mode="after")
    def coherent_mode(self) -> "SeriesDeclaration":
        """Keep counted boolean and public mode byte-identical in meaning."""
        if self.counted != (self.mode == "counted"):
            raise ValueError("declaration counted flag and mode disagree")
        return self
