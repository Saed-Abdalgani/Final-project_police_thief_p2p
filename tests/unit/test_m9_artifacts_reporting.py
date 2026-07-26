import copy
import os
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from police_thief_p2p.adapters.cli.app import main
from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.artifacts import (
    ArtifactKind,
    ArtifactPaths,
    SealedLogEntry,
    artifact_filename,
    export_artifacts,
    finalize_log,
    verify_manifest,
)
from police_thief_p2p.services.artifacts.linkage import VerifiedManifest
from police_thief_p2p.services.artifacts.records import RoleAssignmentRecord
from police_thief_p2p.services.reporting import (
    GMAIL_SEND_SCOPE,
    REQUIRED_RECIPIENT,
    ReportingPolicy,
    build_report,
    build_report_mime,
)
from tests.helpers.reporting import (
    AUDIT,
    COMMITS,
    CONFIG,
    GAME_ID,
    GAME_UID,
    GROUPS,
    JOURNAL,
    build_artifact_fixture,
)


def test_appendix_f_names_and_confined_classified_paths(tmp_path: Path) -> None:
    assert artifact_filename(ArtifactKind.DECLARATION, "game-1") == "declaration_game-1.json"
    assert artifact_filename(ArtifactKind.CONFIG, "game-1", 2) == "config_game-1_g02.json"
    assert artifact_filename(ArtifactKind.LOG, "game-1", 6) == "log_game-1_g06.json"
    assert artifact_filename(ArtifactKind.RESULT, "game-1") == "result_game-1.json"
    with pytest.raises(ValueError, match="lowercase ASCII"):
        artifact_filename(ArtifactKind.RESULT, "../escape")
    with pytest.raises(ValueError, match="presence"):
        artifact_filename(ArtifactKind.CONFIG, "game-1")
    with pytest.raises(ValueError, match="presence"):
        artifact_filename(ArtifactKind.RESULT, "game-1", 1)
    paths = ArtifactPaths(tmp_path / "artifacts")
    assert paths.official != paths.diagnostics != paths.private
    with pytest.raises(ValueError, match="unsafe"):
        paths.resolve_official("../result.json")
    with pytest.raises(ValueError, match="unsafe"):
        paths.resolve_official("NUL.json")


def test_atomic_writer_manifest_linkage_archive_and_immutability(tmp_path: Path) -> None:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    verified = verify_manifest(fixture.manifest, fixture.writer.paths)
    assert len(verified.documents) == 14
    manifest_path = fixture.writer.paths.resolve_official(f"manifest_{GAME_ID}.json")
    assert manifest_path.exists()
    archive = export_artifacts(verified, fixture.writer.paths, tmp_path / "export.zip")
    with zipfile.ZipFile(archive) as bundle:
        assert len(bundle.namelist()) == 15
        assert all("/" not in name and "\\" not in name for name in bundle.namelist())
    declaration = fixture.references[0]
    path = fixture.writer.paths.resolve_official(declaration.filename)
    os.chmod(path, 0o600)
    original = path.read_bytes()
    path.write_bytes(original.replace(b'"counted":true', b'"counted":false'))
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_manifest(fixture.manifest, fixture.writer.paths)


def test_private_evidence_is_bounded_and_finalization_is_pure(tmp_path: Path) -> None:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    private = fixture.writer.write_private_evidence("sealed-step", b"{}")
    assert private.parent == fixture.writer.paths.private
    with pytest.raises(ValueError, match="unsafe"):
        fixture.writer.write_private_evidence("../secret", b"{}")
    with pytest.raises(ValueError, match="exceeds"):
        fixture.writer.write_private_evidence("large", b"x" * 16_777_217)
    entries = [
        SealedLogEntry(
            sequence=2,
            step_number=1,
            phase="audit",
            actor="system",
            timestamp="2026-07-26T10:00:00Z",
            audit_status="verified",
        )
    ]
    snapshot = tuple(entries)
    with pytest.raises(ValueError, match="contiguous"):
        finalize_log(
            game_id=GAME_ID,
            game_uid=GAME_UID,
            sub_game_number=1,
            role_assignment=RoleAssignmentRecord(police=GROUPS[0], thief=GROUPS[1]),
            config_sha256=CONFIG,
            played_commits=COMMITS,
            journal_sha256=JOURNAL,
            entries=entries,
            terminal_reason="survival",
            audit_status="verified",
            audit_sha256=AUDIT,
        )
    assert tuple(entries) == snapshot


def test_verified_report_mime_policy_and_dry_run(tmp_path: Path) -> None:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    verified = verify_manifest(fixture.manifest, fixture.writer.paths)
    policy = ReportingPolicy(tmp_path / "artifacts")
    report = build_report(verified, policy, recipient=REQUIRED_RECIPIENT)
    mime = build_report_mime(report.item, sender="team@example.com")
    assert b"application/json" in mime
    assert report.item.attachment_name.encode() in mime
    assert b"authoritative" in mime
    assert b"X-Logical-Report-ID" in mime
    with pytest.raises(ValueError, match="sender"):
        build_report_mime(report.item, sender="invalid\nsender")
    corrupt_item = report.item.model_copy(update={"attachment_sha256": "0" * 64})
    with pytest.raises(ValueError, match="digest"):
        build_report_mime(corrupt_item, sender="team@example.com")
    sdk = SimulationSdk()
    loaded = sdk.load_artifact_manifest(
        fixture.writer.paths.resolve_official(f"manifest_{GAME_ID}.json").read_bytes()
    )
    prepared = sdk.prepare_report(
        loaded,
        tmp_path / "artifacts",
        recipient=REQUIRED_RECIPIENT,
        allowlist=(REQUIRED_RECIPIENT,),
    )
    assert sdk.validate_report_mime(prepared, sender="team@example.com") == mime


def test_report_fails_closed_on_digest_tokens_scopes_recipient_and_paths(
    tmp_path: Path,
) -> None:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    verified = verify_manifest(fixture.manifest, fixture.writer.paths)
    policy = ReportingPolicy(tmp_path / "artifacts")
    with pytest.raises(ValueError, match="allowlisted"):
        build_report(verified, policy, recipient="attacker@example.com")
    policy.validate_scopes((GMAIL_SEND_SCOPE,))
    with pytest.raises(ValueError, match="send-only"):
        policy.validate_scopes(("https://mail.google.com/",))
    with pytest.raises(ValueError, match="outside"):
        policy.validate_private_paths(
            tmp_path / "artifacts/credentials.json",
            tmp_path / "private/token.json",
        )
    changed = copy.deepcopy(verified.documents)
    result_name = f"result_{GAME_ID}.json"
    result = changed[result_name]
    agreement = result["agreement"]
    assert isinstance(agreement, dict)
    agreement["agreed_digest"] = "0" * 64
    tampered = VerifiedManifest(verified.manifest, changed)
    with pytest.raises(ValueError, match="digest confirmation"):
        build_report(tampered, policy, recipient=REQUIRED_RECIPIENT)
    changed = copy.deepcopy(verified.documents)
    groups = changed[result_name]["groups"]
    assert isinstance(groups, list)
    assert isinstance(groups[0], dict)
    groups[0]["tokens"] = {"input_tokens": 999, "output_tokens": 999}
    with pytest.raises(ValueError, match="token total"):
        build_report(
            VerifiedManifest(verified.manifest, changed),
            policy,
            recipient=REQUIRED_RECIPIENT,
        )


def test_artifact_models_reject_unsafe_identity_and_schema_version() -> None:
    with pytest.raises(ValidationError):
        RoleAssignmentRecord(police="../bad", thief=GROUPS[1])


def test_cli_validate_mode_changes_no_external_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    manifest = fixture.writer.paths.resolve_official(f"manifest_{GAME_ID}.json")
    assert (
        main(
            [
                "report",
                "validate",
                "--manifest",
                str(manifest),
                "--artifact-root",
                str(tmp_path / "artifacts"),
                "--sender",
                "team@example.com",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert '"external_state_changed": false' in output
    assert '"status": "VALID"' in output
