"""Digest graph linking all official series artifacts."""

from typing import Annotated

from pydantic import Field, StrictInt, StrictStr, field_validator

from police_thief_p2p.services.artifacts.common import ArtifactModel, Commit, Digest
from police_thief_p2p.services.artifacts.naming import ArtifactKind
from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.identifiers import GroupId


class ArtifactReference(FrozenModel):
    """One immutable manifest edge to an official JSON document."""

    kind: ArtifactKind
    filename: StrictStr
    schema_name: StrictStr
    sha256: Digest
    size_bytes: Annotated[StrictInt, Field(ge=1, le=16_777_216)]
    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)] | None = None
    role: str | None = None
    config_sha256: Digest | None = None
    journal_sha256: Digest | None = None
    audit_sha256: Digest | None = None

    @field_validator("filename")
    @classmethod
    def plain_json_name(cls, value: str) -> str:
        """Reject paths and non-JSON manifest targets."""
        if "/" in value or "\\" in value or not value.endswith(".json"):
            raise ValueError("manifest filename must be a plain JSON name")
        return value


class ArtifactManifest(ArtifactModel):
    """Complete linkage, digest, commit, journal, and audit index."""

    config_sha256: Digest
    played_commits: dict[str, Commit]
    journal_sha256: Digest
    audit_manifest_sha256: Digest
    entries: Annotated[tuple[ArtifactReference, ...], Field(min_length=4)]

    @field_validator("played_commits")
    @classmethod
    def safe_groups(cls, value: dict[str, str]) -> dict[str, str]:
        """Validate group keys and require both participants."""
        if len(value) != 2:
            raise ValueError("manifest requires exactly two groups of commits")
        for group_id in value:
            GroupId(group_id)
        return value

    @field_validator("entries")
    @classmethod
    def unique_files(cls, value: tuple[ArtifactReference, ...]) -> tuple[ArtifactReference, ...]:
        """Reject duplicate paths in the immutable graph."""
        names = [item.filename for item in value]
        if len(names) != len(set(names)):
            raise ValueError("manifest artifact filenames must be unique")
        return value
