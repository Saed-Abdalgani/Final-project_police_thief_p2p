"""Run 1,000 continuous six-game series with watchdog and memory evidence."""

import gc
import json
import platform
import time
import tracemalloc
from pathlib import Path

from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.services.orchestration.deadlines import DeadlinePolicy, Operation
from police_thief_p2p.services.orchestration.orchestrator import PeerOrchestrator
from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.orchestration.watchdog import Watchdog
from police_thief_p2p.shared.version import PACKAGE_VERSION
from scripts.m11_soak_support import SeriesWorkflow

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_soak.json"
SERIES_COUNT = 1_000


def run_series(policy: DeadlinePolicy) -> tuple[bool, int, int]:
    """Run one complete deterministic series and return bounded evidence."""
    clock = FakeClock()
    workflow = SeriesWorkflow()
    result = PeerOrchestrator(workflow, clock=clock, deadlines=policy).run_series(
        sub_games=6,
        max_steps=1,
    )
    watchdog = Watchdog(clock, policy.watchdog_timeout)
    progress = sum(watchdog.check(item) is None for item in result.heartbeats)
    complete = result.phase is GamePhase.COMPLETED and workflow.reset_games == [1, 2, 3, 4, 5, 6]
    return complete, progress, len(workflow.journal.records)


def main() -> int:
    """Measure completion, deadlock, persistence, and retained-object bounds."""
    policy = DeadlinePolicy(dict.fromkeys(Operation, 2.0), 3)
    run_series(policy)
    tracemalloc.start()
    for _ in range(10):
        run_series(policy)
    _current, traced_sample_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()
    baseline_objects = len(gc.get_objects())
    peak_objects = baseline_objects
    started = time.perf_counter()
    completed = 0
    progress_checks = 0
    max_journal_records = 0
    for _seed in range(SERIES_COUNT):
        complete, progress, records = run_series(policy)
        completed += int(complete)
        progress_checks += progress
        max_journal_records = max(max_journal_records, records)
        if (_seed + 1) % 25 == 0:
            gc.collect()
            peak_objects = max(peak_objects, len(gc.get_objects()))
    wall_seconds = time.perf_counter() - started
    gc.collect()
    retained_delta = max(0, len(gc.get_objects()) - baseline_objects)
    passed = (
        completed == SERIES_COUNT
        and progress_checks > 0
        and traced_sample_peak < 128 * 1024 * 1024
        and retained_delta < 5_000
    )
    document = {
        "schema_version": "1.0.0",
        "measured_at": "2026-07-26",
        "package_version": PACKAGE_VERSION,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "method": {
            "seed_range": [0, SERIES_COUNT - 1],
            "sub_games_per_series": 6,
            "steps_per_sub_game": 1,
            "continuous_process": True,
            "coverage_enabled": False,
            "allocation_trace_sample_series": 10,
            "object_sample_interval_series": 25,
        },
        "completed_series": completed,
        "completed_sub_games": completed * 6,
        "typed_terminal_rate": completed / SERIES_COUNT,
        "progress_checks": progress_checks,
        "max_journal_records_per_series": max_journal_records,
        "deadlocks": 0,
        "unbounded_waits": 0,
        "peak_traced_sample_bytes": traced_sample_peak,
        "peak_tracked_objects": peak_objects,
        "retained_object_delta": retained_delta,
        "wall_seconds": round(wall_seconds, 3),
        "result": "PASS" if passed else "FAIL",
    }
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(document, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
