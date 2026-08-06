import asyncio
import json
from pathlib import Path

import pytest

from police_thief_p2p.services.experiments.gate_result import GateResult
from police_thief_p2p.services.experiments.report import TournamentReport
from police_thief_p2p.services.experiments.resources import ResourceLedger
from police_thief_p2p.services.experiments.studies import ABLATIONS, ROBUSTNESS_CASES
from police_thief_p2p.shared.config_loader import load_private_path
from scripts import m12_campaign_support as support
from scripts.m12_rehearsal_config import private_document
from scripts.m12_rehearsal_peers import PeerRoot, free_port, prepare_peer, probe_health
from scripts.m12_rehearsal_summary import (
    ARTIFACT_FAMILIES,
    artifact_families,
    calendar_entries,
    rehearsal_gates,
    tunnel_preflight,
)
from scripts.m12_study_report import ablation_rows, robustness_rows, study_document

pytestmark = pytest.mark.integration

FAST_BUDGET = 60


@pytest.fixture(scope="module")
def report() -> TournamentReport:
    shared, strategy = support.load_configs()
    plan = support.SplitPlan.load("validation")
    spec = plan.spec(
        "support-smoke",
        opponents=plan.opponent_ids[:1],
        fixtures=plan.fixtures[:1],
        seeds=plan.seeds[:1],
        decision_budget_ms=FAST_BUDGET,
    )
    return support.build_runner(shared, strategy).run(spec)


def test_split_plans_only_admit_frozen_seeds_and_fixtures() -> None:
    plan = support.SplitPlan.load("train")
    spec = plan.spec("plan-check")
    assert spec.split == "train"
    assert spec.candidate_id == "candidate-advanced"
    assert set(spec.seeds) <= set(plan.seeds)
    with pytest.raises(ValueError, match="not frozen"):
        plan.spec("leaky", seeds=(1,))


def test_commit_sha_and_config_loading_are_available_offline() -> None:
    shared, strategy = support.load_configs()
    assert shared.board_and_agents.grid_size >= 5
    assert strategy.decision_budget_ms > 0
    assert len(support.commit_sha()) in {7, 40, len("unavailable")}


def test_evidence_writing_round_trips_and_summarises_a_report(
    tmp_path: Path,
    report: TournamentReport,
) -> None:
    summary = support.report_summary(report)
    path = tmp_path / "nested" / "evidence.json"
    support.write_evidence(path, {"summary": summary})
    restored = json.loads(path.read_text(encoding="utf-8"))
    assert restored["summary"]["campaign_id"] == "support-smoke"
    assert set(summary) >= {"match_count", "score_share_percent", "reliability"}


def test_load_freeze_requires_a_completed_tuning_campaign(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(support, "BENCHMARKS", tmp_path)
    with pytest.raises(FileNotFoundError, match="run_m12_tuning"):
        support.load_freeze()
    point = {"search_horizon": 3}
    (tmp_path / "m12_tuning.json").write_text(
        json.dumps(
            {
                "random_search": {"trials": [{"trial_id": 0, "point": point}]},
                "surrogate_search": {"trials": []},
                "manifest": {"candidate": {"trial_id": 0}},
            }
        ),
        encoding="utf-8",
    )
    assert support.load_freeze() == point
    (tmp_path / "m12_tuning.json").write_text(
        json.dumps(
            {
                "random_search": {"trials": []},
                "surrogate_search": {"trials": []},
                "manifest": {"candidate": {"trial_id": 7}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no trial 7"):
        support.load_freeze()


def test_study_documents_report_every_declared_ablation_and_case(
    report: TournamentReport,
) -> None:
    ablations = [(ABLATIONS[0], report), (ABLATIONS[1], report)]
    robustness = [(ROBUSTNESS_CASES[0], report)]
    share = report.score_share
    rows = ablation_rows(ablations, share)
    assert [item["study_id"] for item in rows] == ["ABL-FULL", "ABL-DEPTH"]
    assert rows[0]["share_delta"] == 0.0
    cases = robustness_rows(robustness, share)
    assert cases[0]["case_id"] == "ROB-CLEAN"
    document = study_document(
        schema_version=support.SCHEMA_VERSION,
        commit_sha="deadbeef",
        intact=share,
        intact_report=report,
        ablations=ablations,
        robustness=robustness,
        adversarial=[{"opponent_id": "BL-ADV-LIAR", "reliability_passes": True}],
        gate=GateResult("R09", "robustness holds", 1.0, True),
        resources=ResourceLedger().usage(),
    )
    assert document["split"] == "validation"
    assert document["gates"]["result"] == "PASS"  # type: ignore[index]
    assert document["adversarial_search"]["worst_case_opponent_ids"] == [  # type: ignore[index]
        "BL-ADV-LIAR"
    ]


def _peer(root: Path, name: str, port: int, opponent_port: int) -> PeerRoot:
    shared = Path(support.SHARED_CONFIG).read_bytes()
    return prepare_peer(
        name,
        root / name,
        shared,
        group="GRP00001",
        role="police",
        port=port,
        opponent_port=opponent_port,
    )


def test_rehearsal_peer_roots_stay_isolated_and_configurable(tmp_path: Path) -> None:
    left_port, right_port = free_port(), free_port()
    assert left_port != right_port
    left = _peer(tmp_path, "alpha", left_port, right_port)
    right = _peer(tmp_path, "beta", right_port, left_port)
    assert left.endpoint == f"http://127.0.0.1:{left_port}/mcp"
    assert left.artifact_root.is_dir()
    assert left.artifact_root != right.artifact_root
    private = load_private_path(left.private_path)
    assert private.network.listen_port == left_port
    assert private.paths.artifact_root.resolve() == left.artifact_root.resolve()
    assert "m12-rehearsal" in private_document("GRP00001", "police", 1, 2, tmp_path)


def test_unreachable_endpoints_never_report_a_healthy_peer() -> None:
    assert not asyncio.run(probe_health(f"http://127.0.0.1:{free_port()}/mcp", timeout_sec=0.5))


def _series(*, counted_completed: bool, digest: str) -> dict[str, object]:
    counted = [
        {
            "completed": counted_completed,
            "both_peers_agree": True,
            "agreement_status": "Verified OK",
            "manifest_sha256": f"{digest}{index}",
        }
        for index in range(6)
    ]
    return {"warmups": [{"completed": True}], "counted": counted}


def test_rehearsal_gates_fail_closed_until_every_sub_game_is_verified() -> None:
    preflight = {"bidirectional": True, "external_network_verified": False}
    artifacts = {"artifact_roots_are_disjoint": True}
    passing = rehearsal_gates(
        _series(counted_completed=True, digest="ab"), preflight, artifacts, bidirectional=True
    )
    assert passing["result"] == "PASS"
    assert passing["outstanding"]
    failing = rehearsal_gates(
        _series(counted_completed=False, digest="ab"), preflight, artifacts, bidirectional=True
    )
    assert failing["result"] == "FAIL"


def test_rehearsal_calendar_and_artifact_families_are_recorded(tmp_path: Path) -> None:
    entries = calendar_entries()
    assert [item["counted"] for item in entries] == [True, True]
    peers = {"alpha": _peer(tmp_path, "alpha", free_port(), free_port())}
    for family in ARTIFACT_FAMILIES[:2]:
        (peers["alpha"].artifact_root / family).mkdir(parents=True, exist_ok=True)
    families = artifact_families(peers)
    assert families["artifact_roots_are_disjoint"] is True
    assert families["per_peer"]["alpha"]["protocol"] is True  # type: ignore[index]
    assert families["per_peer"]["alpha"]["replay"] is False  # type: ignore[index]
    private = load_private_path(peers["alpha"].private_path)
    preflight = tunnel_preflight(peers, private)
    assert preflight["configured_provider"] == "local"
    assert preflight["external_network_verified"] is False
    assert preflight["bidirectional"] is False
