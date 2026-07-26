"""SDK-only entry points for verified offline replay."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from police_thief_p2p.services.artifacts import ArtifactKind, ArtifactManifest
    from police_thief_p2p.services.artifacts.manifest import ArtifactReference
    from police_thief_p2p.services.replay import ReplayVerification
    from police_thief_p2p.services.replay.models import ReplayCursor


class ReplayFacade:
    """Expose schema-first replay without leaking verifier internals."""

    __slots__ = ()

    def verify_log(
        self,
        log_document: bytes,
        config_document: bytes,
        *,
        viewer_group: str,
        objective: bool = False,
    ) -> ReplayVerification:
        """Verify one bounded finalized log before any rendering."""
        from police_thief_p2p.services.replay import ReplayMode, verify_replay_log
        from police_thief_p2p.services.replay.loader import load_replay_documents

        if objective:
            raise ValueError("objective replay requires dual-log verification")
        log, config = load_replay_documents(log_document, config_document)
        return verify_replay_log(
            log,
            config,
            mode=ReplayMode.SINGLE_LOG,
            viewer_group=viewer_group,
        )

    def verify_dual_log(
        self,
        primary_log: bytes,
        primary_config: bytes,
        sibling_log: bytes,
        sibling_config: bytes,
        *,
        viewer_group: str,
    ) -> ReplayVerification:
        """Verify and link both final logs before objective truth is available."""
        from police_thief_p2p.services.replay import verify_dual_logs
        from police_thief_p2p.services.replay.loader import load_replay_documents

        left_log, left_config = load_replay_documents(primary_log, primary_config)
        right_log, right_config = load_replay_documents(sibling_log, sibling_config)
        return verify_dual_logs(
            left_log,
            left_config,
            right_log,
            right_config,
            viewer_group=viewer_group,
        )

    def verify_manifest_log(
        self,
        manifest_document: bytes,
        artifact_root: Path,
        *,
        sub_game_number: int,
        viewer_group: str,
    ) -> ReplayVerification:
        """Verify the complete series graph before selecting one replay log."""
        from police_thief_p2p.services.artifacts import ArtifactKind, ArtifactPaths
        from police_thief_p2p.services.artifacts.linkage import verify_manifest

        manifest = _load_manifest(manifest_document)
        paths = ArtifactPaths(artifact_root)
        verified = verify_manifest(manifest, paths)
        config_ref = _select(verified.manifest, ArtifactKind.CONFIG, sub_game_number)
        log_ref = _select(verified.manifest, ArtifactKind.LOG, sub_game_number)
        return self.verify_log(
            paths.resolve_official(log_ref.filename).read_bytes(),
            paths.resolve_official(config_ref.filename).read_bytes(),
            viewer_group=viewer_group,
        )

    def verify_series_replay(
        self,
        manifest_document: bytes,
        artifact_root: Path,
        *,
        viewer_group: str,
    ) -> tuple[ReplayVerification, ...]:
        """Verify all six selectable sub-games behind one linked manifest."""
        return tuple(
            self.verify_manifest_log(
                manifest_document,
                artifact_root,
                sub_game_number=number,
                viewer_group=viewer_group,
            )
            for number in range(1, 7)
        )

    def replay_cursor(self, result: ReplayVerification) -> ReplayCursor:
        """Create immutable navigation state for one verified result."""
        from police_thief_p2p.services.replay.models import ReplayCursor

        return ReplayCursor(result)

    def navigate_replay(
        self,
        cursor: ReplayCursor,
        command: str,
        *,
        step: int | None = None,
    ) -> ReplayCursor:
        """Apply one bounded replay navigation command."""
        return cursor.move(command, step)

    def export_replay(self, result: ReplayVerification) -> tuple[bytes, bytes]:
        """Return canonical JSON and standalone accessible HTML."""
        from police_thief_p2p.services.artifacts.loader import load_artifact_json
        from police_thief_p2p.services.replay import replay_html, replay_json
        from police_thief_p2p.shared.schema_registry import validate_schema

        document = replay_json(result)
        validate_schema(
            load_artifact_json(document, max_bytes=16_777_216),
            "replay_audit.schema.json",
            source="replay-export",
        )
        return document, replay_html(result)


def _load_manifest(document: bytes) -> ArtifactManifest:
    from police_thief_p2p.services.artifacts import ArtifactManifest
    from police_thief_p2p.services.artifacts.loader import load_artifact_json
    from police_thief_p2p.shared.schema_registry import validate_schema

    if len(document) > 1_048_576:
        raise ValueError("artifact manifest exceeds size limit")
    value = load_artifact_json(document, max_bytes=1_048_576)
    validate_schema(value, "artifact_manifest.schema.json", source="artifact-manifest")
    return ArtifactManifest.model_validate(value)


def _select(
    manifest: ArtifactManifest,
    kind: ArtifactKind,
    sub_game_number: int,
) -> ArtifactReference:
    matches = [
        item
        for item in manifest.entries
        if item.kind is kind and item.sub_game_number == sub_game_number
    ]
    if len(matches) != 1:
        raise ValueError("manifest replay artifact selection is ambiguous")
    return matches[0]
