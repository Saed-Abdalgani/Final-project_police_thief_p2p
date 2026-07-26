"""SDK artifact verification and safe report dry-run use cases."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from police_thief_p2p.services.artifacts import ArtifactManifest, ArtifactWriter
    from police_thief_p2p.services.reporting import PreparedReport


class ArtifactReportingFacade:
    """Expose artifact/reporting use cases without provider authority."""

    def artifact_writer(self, root: Path) -> ArtifactWriter:
        """Create a classified atomic artifact writer."""
        from police_thief_p2p.services.artifacts import ArtifactWriter

        return ArtifactWriter(root)

    def load_artifact_manifest(self, document: bytes) -> ArtifactManifest:
        """Load one bounded immutable artifact manifest."""
        from police_thief_p2p.services.artifacts import ArtifactManifest
        from police_thief_p2p.services.artifacts.loader import load_artifact_json
        from police_thief_p2p.shared.schema_registry import validate_schema

        if len(document) > 1_048_576:
            raise ValueError("artifact manifest exceeds size limit")
        value = load_artifact_json(document, max_bytes=1_048_576)
        validate_schema(value, "artifact_manifest.schema.json", source="artifact-manifest")
        return ArtifactManifest.model_validate(value)

    def prepare_report(
        self,
        manifest: ArtifactManifest,
        artifact_root: Path,
        *,
        recipient: str,
        allowlist: tuple[str, ...],
        competition_mode: bool = True,
    ) -> PreparedReport:
        """Verify the full digest graph before constructing report bytes."""
        from police_thief_p2p.services.artifacts import ArtifactPaths, verify_manifest
        from police_thief_p2p.services.reporting.policy import ReportingPolicy
        from police_thief_p2p.services.reporting.report import build_report

        paths = ArtifactPaths(artifact_root)
        verified = verify_manifest(manifest, paths)
        policy = ReportingPolicy(
            artifact_root,
            allowlist=allowlist,
            competition_mode=competition_mode,
        )
        return build_report(verified, policy, recipient=recipient)

    def validate_report_mime(self, report: PreparedReport, *, sender: str) -> bytes:
        """Dry-run MIME construction with no outbox or external side effect."""
        from police_thief_p2p.services.reporting.mime import build_report_mime

        return build_report_mime(report.item, sender=sender)
