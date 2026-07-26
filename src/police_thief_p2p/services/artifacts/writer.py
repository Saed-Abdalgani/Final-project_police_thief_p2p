"""Atomic schema-validating official artifact writer."""

import os
import uuid
from pathlib import Path

from police_thief_p2p.services.artifacts.common import ArtifactModel
from police_thief_p2p.services.artifacts.manifest import ArtifactReference
from police_thief_p2p.services.artifacts.naming import (
    ArtifactKind,
    ArtifactPaths,
    artifact_filename,
)
from police_thief_p2p.shared.canonical_json import canonical_json_bytes, digest_bytes
from police_thief_p2p.shared.schema_registry import validate_schema


class ArtifactWriter:
    """Validate, flush, atomically replace, and seal official artifacts."""

    __slots__ = ("_paths", "_schemas")

    def __init__(self, root: Path) -> None:
        """Create isolated official, private, and diagnostics roots."""
        self._paths = ArtifactPaths(root)
        self._schemas = {
            ArtifactKind.DECLARATION: "series_declaration.schema.json",
            ArtifactKind.CONFIG: "sub_game_config.schema.json",
            ArtifactKind.LOG: "log.schema.json",
            ArtifactKind.RESULT: "final_result.schema.json",
            ArtifactKind.MANIFEST: "artifact_manifest.schema.json",
        }

    @property
    def paths(self) -> ArtifactPaths:
        """Expose resolved classified roots."""
        return self._paths

    def write(
        self,
        kind: ArtifactKind,
        artifact: ArtifactModel,
        *,
        sub_game_number: int | None = None,
        role: str | None = None,
        config_sha256: str | None = None,
        journal_sha256: str | None = None,
        audit_sha256: str | None = None,
    ) -> ArtifactReference:
        """Accept exactly one immutable schema-valid official JSON document."""
        name = artifact_filename(kind, artifact.game_id, sub_game_number)
        document = artifact.model_dump(mode="json")
        schema_name = self._schemas[kind]
        validate_schema(document, schema_name, source=name)
        data = canonical_json_bytes(document)
        target = self._paths.resolve_official(name)
        self._atomic_immutable(target, data)
        return ArtifactReference(
            kind=kind,
            filename=name,
            schema_name=schema_name,
            sha256=digest_bytes(data),
            size_bytes=len(data),
            sub_game_number=sub_game_number,
            role=role,
            config_sha256=config_sha256,
            journal_sha256=journal_sha256,
            audit_sha256=audit_sha256,
        )

    def write_private_evidence(self, key: str, data: bytes) -> Path:
        """Persist bounded pre-audit bytes with owner-only permissions."""
        if not key.isascii() or not key.replace("-", "").isalnum() or len(key) > 64:
            raise ValueError("private evidence key is unsafe")
        if len(data) > 16_777_216:
            raise ValueError("private evidence exceeds configured size")
        target = (self._paths.private / f"{key}.json").resolve()
        if target.parent != self._paths.private:
            raise ValueError("private evidence path escapes root")
        self._atomic_replace(target, data, private=True)
        return target

    def _atomic_immutable(self, target: Path, data: bytes) -> None:
        if target.exists():
            if target.read_bytes() != data:
                raise FileExistsError("official artifact is immutable")
            return
        self._atomic_replace(target, data, private=False)

    def _atomic_replace(self, target: Path, data: bytes, *, private: bool) -> None:
        temporary = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            self._paths.apply_permissions(temporary, private=private)
            os.replace(temporary, target)
            self._paths.apply_permissions(target, private=private)
        finally:
            if temporary.exists():
                temporary.unlink()
