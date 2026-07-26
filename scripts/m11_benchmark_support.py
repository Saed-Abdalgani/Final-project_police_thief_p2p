"""Reusable warmup, percentile, hardware, and profiling helpers for M11."""

import cProfile
import pstats
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, cast

from police_thief_p2p.adapters.system.system_info import PlatformSystemInfoProbe


@dataclass(frozen=True, slots=True)
class SampleStats:
    """Stable millisecond summary for one benchmark case."""

    samples: int
    p50_ms: float
    p95_ms: float
    max_ms: float

    def as_dict(self) -> dict[str, int | float]:
        """Return JSON-safe rounded metrics."""
        return {
            "samples": self.samples,
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "max_ms": round(self.max_ms, 3),
        }


def nearest_rank(values: list[float], fraction: float) -> float:
    """Return a deterministic nearest-rank percentile."""
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * fraction + 0.9999) - 1))
    return ordered[index]


def measure[T](
    operation: Callable[[], T],
    *,
    warmups: int = 2,
    samples: int = 20,
) -> SampleStats:
    """Warm one operation and measure p50, p95, and maximum latency."""
    if warmups < 0 or samples < 1:
        raise ValueError("benchmark warmups/samples are invalid")
    for _ in range(warmups):
        operation()
    values = []
    for _ in range(samples):
        started = time.perf_counter()
        operation()
        values.append((time.perf_counter() - started) * 1_000)
    return SampleStats(samples, nearest_rank(values, 0.5), nearest_rank(values, 0.95), max(values))


def hardware_metadata() -> dict[str, object]:
    """Return the project-standard non-secret host declaration."""
    return asdict(PlatformSystemInfoProbe().collect())


def profile_hotspots(operation: Callable[[], object], limit: int = 8) -> list[dict[str, object]]:
    """Return top cumulative CPU functions for one representative operation."""
    profiler = cProfile.Profile()
    profiler.enable()
    operation()
    profiler.disable()
    rows = sorted(
        cast(Any, pstats.Stats(profiler)).stats.items(),
        key=lambda item: item[1][3],
        reverse=True,
    )
    return [
        {
            "function": f"{key[0]}:{key[1]}:{key[2]}",
            "calls": value[1],
            "cumulative_seconds": round(value[3], 6),
        }
        for key, value in rows[:limit]
    ]
