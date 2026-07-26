import json
from dataclasses import replace
from pathlib import Path

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.gui.snapshot_svg import live_view_svg
from police_thief_p2p.adapters.gui.view_model import safe_ui_error
from police_thief_p2p.sdk import FORBIDDEN_LIVE_FIELDS, ReplayFinding
from police_thief_p2p.services.replay.loader import MAX_REPLAY_BYTES
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.replay import GROUPS, build_replay_fixture, build_replay_manifest
from tests.unit.test_m10_live_view import build_view

pytestmark = pytest.mark.security


@pytest.mark.parametrize(
    ("document", "message"),
    [
        (b"\xff", "artifact JSON is invalid"),
        (
            b'{"schema_version":"0.2.0","schema_version":"0.2.0"}',
            "artifact JSON is invalid",
        ),
        (("{" + '"x":{' * 65 + '"v":0' + "}" * 66).encode(), "depth limit"),
        (b"{" + b" " * MAX_REPLAY_BYTES + b"}", "size limit"),
    ],
    ids=("invalid-utf8", "duplicate-keys", "deep-tree", "oversized"),
)
def test_replay_rejects_invalid_encoding_duplicate_deep_and_oversized_json(
    shared_config: SharedConfig,
    document: bytes,
    message: str,
) -> None:
    fixture = build_replay_fixture(shared_config)
    with pytest.raises(ValueError, match=message):
        SimulationSdk().verify_log(
            document,
            fixture.config_bytes,
            viewer_group=GROUPS[0],
        )


def test_manifest_digest_and_identifier_tampering_fail_before_render(
    tmp_path: Path,
    shared_config: SharedConfig,
) -> None:
    manifest = build_replay_manifest(tmp_path / "artifacts", shared_config)
    document = manifest.model_dump(mode="json")
    document["entries"][0]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        SimulationSdk().verify_manifest_log(
            canonical_json_bytes(document),
            tmp_path / "artifacts",
            sub_game_number=1,
            viewer_group=GROUPS[0],
        )
    fixture = build_replay_fixture(shared_config)
    log = json.loads(fixture.log_bytes)
    log["game_uid"] = "not-a-uuid"
    with pytest.raises(ValueError, match="schema"):
        SimulationSdk().verify_log(
            canonical_json_bytes(log),
            fixture.config_bytes,
            viewer_group=GROUPS[0],
        )


def test_screenshots_and_generic_errors_do_not_leak_truth_or_secrets(
    shared_config: SharedConfig,
) -> None:
    screenshot = live_view_svg(build_view(shared_config)).decode().casefold()
    assert all(field not in screenshot for field in FORBIDDEN_LIVE_FIELDS)
    error = safe_ui_error(RuntimeError("Traceback token=private secret_nonce=abc"))
    assert error.message == "The operation could not complete. Retry or export diagnostics."
    assert "private" not in error.message
    assert "traceback" not in error.message.casefold()


def test_human_replay_export_escapes_untrusted_finding_text(
    shared_config: SharedConfig,
) -> None:
    fixture = build_replay_fixture(shared_config)
    result = SimulationSdk().verify_log(
        fixture.log_bytes,
        fixture.config_bytes,
        viewer_group=GROUPS[0],
    )
    poisoned = replace(
        result,
        findings=(ReplayFinding(1, "TEST", "fixture", "<script>alert('secret')</script>"),),
    )
    _, html = SimulationSdk().export_replay(poisoned)
    assert b"<script>" not in html
    assert b"&lt;script&gt;" in html
