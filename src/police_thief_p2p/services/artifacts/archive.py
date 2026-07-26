"""Credential-free export of one verified official artifact set."""

import zipfile
from pathlib import Path

from police_thief_p2p.services.artifacts.linkage import VerifiedManifest
from police_thief_p2p.services.artifacts.naming import (
    ArtifactKind,
    ArtifactPaths,
    artifact_filename,
)
from police_thief_p2p.shared.canonical_json import canonical_json_bytes

_FORBIDDEN_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "client_secret",
        "credentials",
        "oauth_token",
        "private_toml",
        "refresh_token",
        "token_json",
    }
)


def export_artifacts(
    verified: VerifiedManifest,
    paths: ArtifactPaths,
    destination: Path,
) -> Path:
    """Create a deterministic ZIP containing only verified official evidence."""
    target = destination.resolve()
    if target.suffix.lower() != ".zip":
        raise ValueError("artifact export must use a .zip destination")
    target.parent.mkdir(parents=True, exist_ok=True)
    for document in verified.documents.values():
        _reject_secrets(document)
    manifest_name = artifact_filename(
        ArtifactKind.MANIFEST,
        verified.manifest.game_id,
    )
    manifest_bytes = canonical_json_bytes(verified.manifest.model_dump(mode="json"))
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_zip(archive, manifest_name, manifest_bytes)
        for name in sorted(verified.documents):
            _write_zip(archive, name, paths.resolve_official(name).read_bytes())
    return target


def _reject_secrets(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in _FORBIDDEN_KEYS:
                raise ValueError("artifact export contains a forbidden secret field")
            _reject_secrets(item)
    elif isinstance(value, list):
        for item in value:
            _reject_secrets(item)


def _write_zip(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.external_attr = 0o100444 << 16
    archive.writestr(info, data)
