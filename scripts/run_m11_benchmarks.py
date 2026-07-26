"""Run the repeatable M11 release-candidate performance campaign."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.domain import Action, Board, GameRules, LocalGameState, Position, Role
from police_thief_p2p.domain.engine import transition
from police_thief_p2p.domain.graph import articulation_points, shortest_path_length
from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.shared.canonical_json import canonical_json_bytes, sha256_digest
from police_thief_p2p.shared.config_loader import load_shared_path
from police_thief_p2p.shared.version import PACKAGE_VERSION
from scripts.m11_benchmark_support import hardware_metadata, measure, profile_hotspots
from scripts.m11_operational_metrics import outbox_outage_metrics, protocol_series_metrics
from tests.helpers.replay import GROUPS, build_replay_manifest

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_performance.json"


def _cold_readiness() -> None:
    subprocess.run(  # noqa: S603 - fixed interpreter and source string.
        [
            sys.executable,
            "-c",
            "from police_thief_p2p import SimulationSdk;"
            "assert SimulationSdk().check_readiness().is_ready",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=10,
    )


def _domain_case() -> None:
    board = Board(15)
    rules = GameRules(board, 30, 70, 70)
    state = LocalGameState(
        Role.THIEF,
        Position(7, 7),
        rules,
        visited=frozenset({Position(7, 7)}),
    )
    transition(state, Action.stay())
    shortest_path_length(board, Position(0, 0), Position(14, 14))
    articulation_points(board)


def _artifact_case(repository: AtomicFileRepository, counter: list[int]) -> None:
    counter[0] += 1
    document = canonical_json_bytes({"sequence": counter[0], "values": list(range(100))})
    sha256_digest({"document": document.hex()})
    repository.save(f"benchmark-{counter[0]}", document)


def main() -> int:
    """Measure cold start, domain, replay, artifact, and inherited strategy/belief gates."""
    config = load_shared_path(ROOT / "config/shared/game.example.json")
    with tempfile.TemporaryDirectory(prefix="m11-benchmark-") as directory:
        temporary = Path(directory)
        manifest = build_replay_manifest(temporary / "artifacts", config)
        manifest_bytes = canonical_json_bytes(manifest.model_dump(mode="json"))
        replay = lambda: SimulationSdk().verify_series_replay(  # noqa: E731
            manifest_bytes,
            temporary / "artifacts",
            viewer_group=GROUPS[0],
        )
        repository = AtomicFileRepository(temporary / "writes")
        counter = [0]
        sdk_cold = measure(_cold_readiness, warmups=1, samples=10).as_dict()
        domain = measure(_domain_case).as_dict()
        replay_stats = measure(replay, warmups=1, samples=10).as_dict()
        artifact = measure(lambda: _artifact_case(repository, counter)).as_dict()
        protocol_metrics = protocol_series_metrics()
        outbox_metrics = outbox_outage_metrics()
        measurements = {
            "sdk_cold_readiness": sdk_cold,
            "domain_15x15_transition_graph": domain,
            "six_log_replay": replay_stats,
            "artifact_digest_atomic_write": artifact,
            "mcp_completed_series": protocol_metrics,
            "outbox_outage_recovery": outbox_metrics,
        }
        hotspots = profile_hotspots(replay)
    belief = json.loads((ROOT / "results/benchmarks/m6_belief.json").read_text(encoding="utf-8"))
    strategy = json.loads(
        (ROOT / "results/benchmarks/m7_strategy.json").read_text(encoding="utf-8")
    )
    request_count = protocol_metrics["request_count"]
    gates = {
        "sdk_cold_p95_under_3000_ms": sdk_cold["p95_ms"] < 3_000,
        "domain_p95_under_250_ms": domain["p95_ms"] < 250,
        "replay_p95_under_2000_ms": replay_stats["p95_ms"] < 2_000,
        "artifact_p95_under_100_ms": artifact["p95_ms"] < 100,
        "belief_campaign_pass": belief["gates"]["result"] == "PASS",
        "strategy_campaign_pass": strategy["gates"]["result"] == "PASS",
        "template_tokens_exactly_zero": strategy["gates"]["zero_token_default"] is True,
        "mcp_series_observed": isinstance(request_count, int) and request_count > 0,
        "outbox_recovery_observed": str(outbox_metrics["final_state"]) == "SENT",
    }
    document = {
        "schema_version": "1.0.0",
        "measured_at": "2026-07-26",
        "package_version": PACKAGE_VERSION,
        "method": {
            "clock": "time.perf_counter",
            "warmups": "1-2",
            "samples": "10-20",
            "statistic": "nearest-rank p50/p95 and maximum",
            "coverage_enabled": False,
        },
        "hardware": hardware_metadata(),
        "measurements": measurements,
        "profile_hotspots": hotspots,
        "inherited_evidence": {
            "belief": "results/benchmarks/m6_belief.json",
            "strategy": "results/benchmarks/m7_strategy.json",
        },
        "gates": {**gates, "result": "PASS" if all(gates.values()) else "FAIL"},
    }
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(document["gates"], sort_keys=True))
    return 0 if document["gates"]["result"] == "PASS" else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
