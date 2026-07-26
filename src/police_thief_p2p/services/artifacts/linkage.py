"""Fail-closed verification of the complete artifact digest graph."""

import secrets
from dataclasses import dataclass

from police_thief_p2p.services.artifacts.loader import load_artifact_json
from police_thief_p2p.services.artifacts.manifest import (
    ArtifactManifest,
    ArtifactReference,
)
from police_thief_p2p.services.artifacts.naming import ArtifactKind, ArtifactPaths
from police_thief_p2p.shared.canonical_json import digest_bytes
from police_thief_p2p.shared.schema_registry import validate_schema


@dataclass(frozen=True, slots=True)
class VerifiedManifest:
    """Opaque proof that all referenced documents passed full linkage checks."""

    manifest: ArtifactManifest
    documents: dict[str, dict[str, object]]

    def result_document(self) -> dict[str, object]:
        """Return the sole verified final result document."""
        names = [
            item.filename for item in self.manifest.entries if item.kind is ArtifactKind.RESULT
        ]
        if len(names) != 1:
            raise ValueError("verified manifest requires exactly one result")
        return self.documents[names[0]]


def verify_manifest(manifest: ArtifactManifest, root: ArtifactPaths) -> VerifiedManifest:
    """Validate schemas, bytes, identity, config, commit, journal, and audit links."""
    documents: dict[str, dict[str, object]] = {}
    kinds = [item.kind for item in manifest.entries]
    if kinds.count(ArtifactKind.DECLARATION) != 1 or kinds.count(ArtifactKind.RESULT) != 1:
        raise ValueError("manifest requires one declaration and one result")
    configs = [item for item in manifest.entries if item.kind is ArtifactKind.CONFIG]
    logs = [item for item in manifest.entries if item.kind is ArtifactKind.LOG]
    if (
        len(configs) != 6
        or len(logs) != 6
        or {item.sub_game_number for item in configs} != {item.sub_game_number for item in logs}
    ):
        raise ValueError("manifest config/log cardinality mismatch")
    for reference in manifest.entries:
        data = root.resolve_official(reference.filename).read_bytes()
        if len(data) != reference.size_bytes or not secrets.compare_digest(
            digest_bytes(data), reference.sha256
        ):
            raise ValueError(f"artifact digest mismatch: {reference.filename}")
        document = load_artifact_json(data, max_bytes=reference.size_bytes)
        validate_schema(document, reference.schema_name, source=reference.filename)
        _verify_reference(manifest, reference, document)
        documents[reference.filename] = document
    _verify_graph(manifest, documents)
    return VerifiedManifest(manifest, documents)


def _verify_reference(
    manifest: ArtifactManifest,
    reference: ArtifactReference,
    document: dict[str, object],
) -> None:
    if document.get("game_id") != manifest.game_id or document.get("game_uid") != manifest.game_uid:
        raise ValueError("artifact game linkage mismatch")
    sub_game = reference.sub_game_number
    if sub_game is not None and document.get("sub_game_number") != sub_game:
        raise ValueError("artifact sub-game linkage mismatch")
    config = reference.config_sha256
    if config is not None and document.get("config_sha256") != config:
        raise ValueError("artifact config linkage mismatch")
    if config is not None and config != manifest.config_sha256:
        raise ValueError("manifest config linkage mismatch")
    for key in ("journal_sha256", "audit_sha256"):
        value = getattr(reference, key)
        if value is not None and document.get(key) != value:
            raise ValueError(f"artifact {key} linkage mismatch")


def _verify_graph(
    manifest: ArtifactManifest,
    documents: dict[str, dict[str, object]],
) -> None:
    by_kind = {
        kind: [item for item in manifest.entries if item.kind is kind] for kind in ArtifactKind
    }
    declaration_ref = by_kind[ArtifactKind.DECLARATION][0]
    result_ref = by_kind[ArtifactKind.RESULT][0]
    declaration = documents[declaration_ref.filename]
    result = documents[result_ref.filename]
    if declaration.get("config_sha256") != manifest.config_sha256:
        raise ValueError("declaration config linkage mismatch")
    if (
        result.get("declaration_file") != declaration_ref.filename
        or result.get("declaration_sha256") != declaration_ref.sha256
    ):
        raise ValueError("result declaration linkage mismatch")
    agreement = result.get("agreement")
    if (
        not isinstance(agreement, dict)
        or agreement.get("audit_manifest_sha256") != manifest.audit_manifest_sha256
    ):
        raise ValueError("result audit-manifest linkage mismatch")
    sub_games = result.get("sub_games")
    if not isinstance(sub_games, list):
        raise ValueError("result sub-game linkage is missing")
    config_refs = {item.sub_game_number: item for item in by_kind[ArtifactKind.CONFIG]}
    log_refs = {item.sub_game_number: item for item in by_kind[ArtifactKind.LOG]}
    for sub_game in sub_games:
        if not isinstance(sub_game, dict) or not isinstance(sub_game.get("sub_game_number"), int):
            raise ValueError("result sub-game linkage is invalid")
        number = sub_game["sub_game_number"]
        config_ref = config_refs.get(number)
        log_ref = log_refs.get(number)
        if config_ref is None or log_ref is None:
            raise ValueError("result references an unknown sub-game")
        config = documents[config_ref.filename]
        log = documents[log_ref.filename]
        if (
            config.get("played_commits") != manifest.played_commits
            or log.get("played_commits") != manifest.played_commits
            or log.get("journal_sha256") != manifest.journal_sha256
        ):
            raise ValueError("artifact commit or journal linkage mismatch")
        expected = (
            sub_game.get("config_file"),
            sub_game.get("config_sha256"),
            sub_game.get("log_file"),
            sub_game.get("log_sha256"),
            sub_game.get("audit_sha256"),
            sub_game.get("role_assignment"),
            sub_game.get("commits"),
        )
        actual = (
            config_ref.filename,
            config.get("config_sha256"),
            log_ref.filename,
            log_ref.sha256,
            log.get("audit_sha256"),
            config.get("role_assignment"),
            config.get("played_commits"),
        )
        if expected != actual or log.get("role_assignment") != actual[-2]:
            raise ValueError("result sub-game digest or role linkage mismatch")
