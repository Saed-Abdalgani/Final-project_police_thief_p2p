import ast
import json
from pathlib import Path

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.cli.app import main
from police_thief_p2p.adapters.gui.palette import STATUS_STYLES, contrast_ratio
from police_thief_p2p.adapters.gui.snapshot_svg import live_view_svg, replay_svg
from police_thief_p2p.adapters.gui.view_model import LiveViewModel, safe_ui_error
from police_thief_p2p.sdk import ReplayIntegrity, ViewStatus
from police_thief_p2p.sdk.errors import InvalidInputError
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.replay import GROUPS, build_replay_fixture, build_replay_manifest
from tests.unit.test_m10_live_view import build_view

pytestmark = pytest.mark.integration


def test_manifest_linkage_precedes_replay_and_cli_exports_reports(
    tmp_path: Path,
    shared_config: SharedConfig,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "artifacts"
    manifest = build_replay_manifest(root, shared_config)
    manifest_bytes = canonical_json_bytes(manifest.model_dump(mode="json"))
    result = SimulationSdk().verify_manifest_log(
        manifest_bytes,
        root,
        sub_game_number=1,
        viewer_group=GROUPS[0],
    )
    assert result.integrity is ReplayIntegrity.VERIFIED_OK
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    json_report = tmp_path / "replay.json"
    html_report = tmp_path / "replay.html"
    assert (
        main(
            [
                "replay",
                "verify",
                "--manifest",
                str(manifest_path),
                "--artifact-root",
                str(root),
                "--group",
                GROUPS[0],
                "--sub-game",
                "1",
                "--json-report",
                str(json_report),
                "--html-report",
                str(html_report),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["integrity"] == "Verified OK"
    assert json.loads(json_report.read_bytes())["verified_steps"] == 11
    assert b"Verified OK" in html_report.read_bytes()


def test_direct_replay_rejects_mismatched_outer_log_config_linkage(
    shared_config: SharedConfig,
) -> None:
    fixture = build_replay_fixture(shared_config)
    mismatched = fixture.config.model_copy(update={"sub_game_number": 2})
    with pytest.raises(ValueError, match="log/config linkage"):
        SimulationSdk().verify_log(
            fixture.log_bytes,
            canonical_json_bytes(mismatched.model_dump(mode="json")),
            viewer_group=GROUPS[0],
        )


def test_gui_view_model_accessibility_errors_and_screenshot_privacy(
    shared_config: SharedConfig,
) -> None:
    view = build_view(shared_config, ViewStatus.THINKING)
    model = LiveViewModel.from_view(view)
    assert "not certainty" in model.belief_summary
    assert "Own position" in model.position_label
    for style in STATUS_STYLES.values():
        assert contrast_ratio(style.foreground, style.background) >= 4.5
        assert style.icon
        assert style.label
    error = safe_ui_error(InvalidInputError("Retry configuration.", correlation_id="corr-safe"))
    assert error.correlation_id == "corr-safe"
    assert "Traceback" not in error.message
    first = live_view_svg(view)
    assert first == live_view_svg(view)
    lowered = first.lower()
    for forbidden in (
        b"opponent_true_position",
        b"secret_nonce",
        b"access_token",
        b"refresh_token",
    ):
        assert forbidden not in lowered
    assert b"Opponent belief - not a true position" in first


def test_replay_screenshots_have_text_icon_color_and_first_failure(
    shared_config: SharedConfig,
) -> None:
    fixture = build_replay_fixture(shared_config)
    sdk = SimulationSdk()
    verified = sdk.verify_log(fixture.log_bytes, fixture.config_bytes, viewer_group=GROUPS[0])
    valid_svg = replay_svg(verified)
    assert "✓ Verified OK".encode() in valid_svg
    document = json.loads(fixture.log_bytes)
    document["entries"][0]["commitment_sha256"] = "f" * 64
    tampered = sdk.verify_log(
        canonical_json_bytes(document),
        fixture.config_bytes,
        viewer_group=GROUPS[0],
    )
    invalid_svg = replay_svg(tampered)
    assert "⚠ TAMPERED".encode() in invalid_svg
    assert b"First failure COMMITMENT" in invalid_svg


def test_every_gui_module_uses_sdk_instead_of_domain_or_services() -> None:
    root = Path(__file__).parents[2] / "src/police_thief_p2p/adapters/gui"
    forbidden = ("police_thief_p2p.domain", "police_thief_p2p.services")
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        ]
        assert not any(module.startswith(forbidden) for module in modules), path
