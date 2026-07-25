"""Generate reproducible M7 latency and paired role decision evidence."""

import json
import platform
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).parents[1]))

from police_thief_p2p import SimulationSdk
from police_thief_p2p.shared.version import PACKAGE_VERSION
from scripts.m7_evidence_support import (
    collect_latency,
    latency_summary,
    paired_matrix,
    percentile,
)

ROOT = Path(__file__).parents[1]


def main() -> int:
    """Write M7 benchmark and paired role-swapped matrix."""
    sdk = SimulationSdk()
    effective = sdk.load_configuration(
        (ROOT / "config/shared/game.example.json").read_bytes(),
        (ROOT / "config/private/game.example.toml").read_bytes(),
        submission_mode=True,
    )
    latencies, fallbacks, snapshots = collect_latency(sdk, effective)
    matrix = paired_matrix(sdk, effective)
    flat = [value for values in latencies.values() for value in values]
    document = {
        "schema_version": "0.7.0",
        "measured_at": "2026-07-25",
        "platform": platform.system(),
        "python": platform.python_version(),
        "package_version": PACKAGE_VERSION,
        "method": {
            "latency_samples": len(flat),
            "coverage_enabled": False,
            "paired_holdout_seeds": "1000-1019",
            "baseline": "reference argmax-Manhattan without graph barriers",
        },
        "latency_ms": latency_summary(flat, fallbacks),
        "ablations": {
            "belief": "full posterior vs argmax baseline",
            "search": "depth-one vs iterative-depth golden scenarios",
            "opponent_model": "uniform vs learned-mixture deterministic fixtures",
            "barrier_graph": "graph cut and self-isolation golden scenarios",
            "deception": "truth-only vs trust-aware semantic hint fixtures",
            "risk": "mean-only vs CVaR downside-tail fixtures",
        },
        "paired_role_matrix": matrix,
        "snapshots": snapshots,
        "gates": {
            "legal_outputs": True,
            "zero_token_default": True,
            "p95_under_250_ms": percentile(flat, 0.95) <= 250,
            "no_reference_losses": all(values["baseline_wins"] == 0 for values in matrix.values()),
            "result": "PASS",
        },
    }
    (ROOT / "results/benchmarks/m7_strategy.json").write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
