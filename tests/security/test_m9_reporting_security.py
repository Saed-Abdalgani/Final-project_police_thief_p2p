import copy
from pathlib import Path

import pytest

from police_thief_p2p.adapters.email import GmailSender
from police_thief_p2p.sdk.email import EmailPort
from police_thief_p2p.services.artifacts import ArtifactPaths, export_artifacts, verify_manifest
from police_thief_p2p.services.artifacts.linkage import VerifiedManifest
from police_thief_p2p.services.artifacts.loader import load_artifact_json
from police_thief_p2p.services.reporting import REQUIRED_RECIPIENT, ReportingPolicy
from tests.helpers.reporting import GAME_ID, build_artifact_fixture

pytestmark = pytest.mark.security


class Token:
    def access_token(self) -> str:
        return "never-rendered"


def test_artifact_loader_rejects_duplicates_nonfinite_depth_and_size() -> None:
    with pytest.raises(ValueError, match="invalid"):
        load_artifact_json(b'{"a":1,"a":2}')
    with pytest.raises(ValueError, match="non-finite"):
        load_artifact_json(b'{"value":NaN}')
    nested = b'{"a":' * 65 + b"0" + b"}" * 65
    with pytest.raises(ValueError, match="depth"):
        load_artifact_json(nested)
    with pytest.raises(ValueError, match="size"):
        load_artifact_json(b"{}", max_bytes=1)


def test_archive_rejects_secret_fields_and_policy_is_closed(tmp_path: Path) -> None:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    verified = verify_manifest(fixture.manifest, ArtifactPaths(tmp_path / "artifacts"))
    documents = copy.deepcopy(verified.documents)
    documents[f"result_{GAME_ID}.json"]["access_token"] = "secret"
    with pytest.raises(ValueError, match="forbidden secret"):
        export_artifacts(
            VerifiedManifest(verified.manifest, documents),
            fixture.writer.paths,
            tmp_path / "unsafe.zip",
        )
    with pytest.raises(ValueError, match="required recipient"):
        ReportingPolicy(
            tmp_path / "artifacts",
            allowlist=("safe@example.com",),
        )
    policy = ReportingPolicy(
        tmp_path / "artifacts",
        allowlist=("safe@example.com",),
        competition_mode=False,
    )
    assert policy.validate_recipient("safe@example.com") == "safe@example.com"
    assert REQUIRED_RECIPIENT not in policy.allowlist


def test_gmail_adapter_conforms_to_send_only_port_without_result_builder() -> None:
    sender = GmailSender(Token(), sender="team@example.com")
    assert isinstance(sender, EmailPort)
    source = (Path(__file__).parents[2] / "src/police_thief_p2p/adapters/email/gmail.py").read_text(
        encoding="utf-8"
    )
    assert "FinalResultArtifact" not in source
    assert "build_report" not in source
