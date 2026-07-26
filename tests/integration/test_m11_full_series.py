from pathlib import Path

import pytest

from police_thief_p2p.adapters.cli.app import main
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.sdk import ReplayIntegrity, SimulationSdk
from police_thief_p2p.services.orchestration.deadlines import DeadlinePolicy, Operation
from police_thief_p2p.services.orchestration.orchestrator import PeerOrchestrator
from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.reporting import REQUIRED_RECIPIENT
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from scripts.m11_soak_support import SeriesWorkflow
from tests.helpers.replay import GROUPS, build_replay_manifest
from tests.helpers.reporting import build_artifact_fixture

pytestmark = pytest.mark.integration


def test_complete_six_game_series_audit_artifacts_replay_and_report_dry_run(
    tmp_path: Path,
    shared_config: SharedConfig,
    capsys: pytest.CaptureFixture[str],
) -> None:
    replay_root = tmp_path / "replay"
    manifest = build_replay_manifest(replay_root, shared_config)
    results = SimulationSdk().verify_series_replay(
        canonical_json_bytes(manifest.model_dump(mode="json")),
        replay_root,
        viewer_group=GROUPS[0],
    )
    assert [item.sub_game_number for item in results] == list(range(1, 7))
    assert all(item.integrity is ReplayIntegrity.VERIFIED_OK for item in results)
    assert sum(item.verified_steps for item in results) == 66

    workflow = SeriesWorkflow()
    outcome = PeerOrchestrator(
        workflow,
        clock=FakeClock(),
        deadlines=DeadlinePolicy(dict.fromkeys(Operation, 2.0), 3),
    ).run_series(sub_games=6, max_steps=1)
    assert outcome.phase is GamePhase.COMPLETED
    assert workflow.reset_games == [1, 2, 3, 4, 5, 6]

    fixture = build_artifact_fixture(tmp_path / "reports")
    manifest_path = fixture.writer.paths.resolve_official(
        f"manifest_{fixture.manifest.game_id}.json"
    )
    exit_code = main(
        [
            "report",
            "validate",
            "--manifest",
            str(manifest_path),
            "--artifact-root",
            str(tmp_path / "reports"),
            "--sender",
            "team@example.com",
            "--recipient",
            REQUIRED_RECIPIENT,
        ]
    )
    assert exit_code == 0
    assert '"external_state_changed": false' in capsys.readouterr().out
