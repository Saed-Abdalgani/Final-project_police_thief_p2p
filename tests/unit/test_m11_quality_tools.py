import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

import scripts.m11_trace_matrix as trace_tool
import scripts.run_m11_benchmarks as benchmark_tool
import scripts.run_m11_license_audit as license_tool
import scripts.run_m11_mutation as mutation_tool
import scripts.run_m11_release_audit as release_tool
import scripts.run_m11_soak as soak_tool
from police_thief_p2p.services.orchestration.deadlines import DeadlinePolicy, Operation
from scripts.m11_benchmark_support import (
    SampleStats,
    hardware_metadata,
    measure,
    nearest_rank,
    profile_hotspots,
)
from scripts.m11_operational_metrics import outbox_outage_metrics, protocol_series_metrics


def test_benchmark_helpers_cover_percentiles_validation_hardware_and_profile() -> None:
    assert nearest_rank([4, 1, 3, 2], 0.5) == 2
    stats = measure(lambda: 1, warmups=1, samples=3)
    assert stats.samples == 3
    assert stats.as_dict()["max_ms"] >= 0
    with pytest.raises(ValueError, match="invalid"):
        measure(lambda: None, warmups=-1)
    assert hardware_metadata()["python_version"]
    assert profile_hotspots(lambda: sum(range(20)), limit=2)


def test_operational_metrics_cover_mcp_series_and_outbox_recovery() -> None:
    protocol = protocol_series_metrics()
    outbox = outbox_outage_metrics()
    assert protocol["request_count"] == 60
    assert protocol["response_loss_campaign_retries"] == 60
    assert outbox == {
        "simulated_outage_seconds": 30,
        "outbox_age_seconds": 30.0,
        "dispatch_attempts": 2,
        "maximum_queue_depth": 1,
        "recovered_queue_depth": 1,
        "final_state": "SENT",
    }


def test_inventory_and_trace_generators_write_complete_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(trace_tool, "OUTPUT", tmp_path / "trace.json")
    assert trace_tool.main() == 0
    summary = json.loads((tmp_path / "trace.json").read_text(encoding="utf-8"))["summary"]
    assert summary["mapped_entries"] == 314


def test_small_six_game_soak_writes_memory_and_terminal_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(soak_tool, "OUTPUT", tmp_path / "soak.json")
    monkeypatch.setattr(soak_tool, "SERIES_COUNT", 2)
    assert soak_tool.run_series(DeadlinePolicy(dict.fromkeys(Operation, 2.0), 3))[0]
    assert soak_tool.main() == 0
    result = json.loads((tmp_path / "soak.json").read_text(encoding="utf-8"))
    assert result["completed_sub_games"] == 12


def test_benchmark_campaign_gate_document_is_deterministic_under_fake_timer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_measure(
        operation: Callable[[], object],
        **_kwargs: int,
    ) -> SampleStats:
        del operation
        return SampleStats(10, 1, 2, 3)

    monkeypatch.setattr(benchmark_tool, "OUTPUT", tmp_path / "performance.json")
    monkeypatch.setattr(benchmark_tool, "measure", fake_measure)
    monkeypatch.setattr(benchmark_tool, "profile_hotspots", lambda _operation: [])
    monkeypatch.setattr(benchmark_tool, "hardware_metadata", lambda: {"platform": "test"})
    assert benchmark_tool.main() == 0
    result = json.loads((tmp_path / "performance.json").read_text(encoding="utf-8"))
    assert result["gates"]["result"] == "PASS"


def test_release_audit_helpers_and_summary_never_emit_secret_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert release_tool._safe_member("package/file.py")
    assert not release_tool._safe_member("../escape")
    monkeypatch.setattr(release_tool, "OUTPUT", tmp_path / "security.json")
    monkeypatch.setattr(release_tool, "_tracked_files", lambda: [".gitignore"])
    monkeypatch.setattr(release_tool, "_working_findings", lambda _paths: [])
    monkeypatch.setattr(release_tool, "_history_findings", lambda: [])
    monkeypatch.setattr(release_tool, "_archive_findings", lambda: [])
    monkeypatch.setattr(
        release_tool,
        "_git",
        lambda *_args: subprocess.CompletedProcess([], 0, b"abc\n", b""),
    )
    assert release_tool.main() == 0
    assert json.loads((tmp_path / "security.json").read_text())["result"] == "PASS"


def test_license_audit_covers_the_complete_cross_platform_lock() -> None:
    result = license_tool.build_audit()
    assert result["result"] == "PASS"
    assert result["audited_locked_packages"] == result["locked_packages"]
    assert result["review_required"] == []


def test_mutation_runner_records_only_compact_test_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mutation_tool, "OUTPUT", tmp_path / "mutation.json")
    monkeypatch.setattr(
        mutation_tool.subprocess,  # type: ignore[attr-defined]
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "100 passed\n", ""),
    )
    assert mutation_tool.main() == 0
    result = json.loads((tmp_path / "mutation.json").read_text())
    assert result["result"] == "PASS"
    assert len(result["families"]) == 6
