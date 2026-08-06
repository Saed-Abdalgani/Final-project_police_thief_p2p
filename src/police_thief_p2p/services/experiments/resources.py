"""Host, cost, and resource accounting captured for every experiment campaign."""

import os
import platform
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from police_thief_p2p.services.experiments.memory_probe import peak_rss_mb


def host_facts() -> dict[str, object]:
    """Return the host and interpreter facts recorded beside every campaign."""
    return {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
    }


@dataclass(frozen=True, slots=True)
class ResourceUsage:
    """Immutable per-campaign resource and cost measurement."""

    wall_time_sec: float
    peak_rss_mb: float
    calls: int
    payload_bytes: int
    prompt_tokens: int
    completion_tokens: int
    max_call_latency_ms: float

    def as_document(self) -> dict[str, object]:
        """Return the serializable resource record required by the manifest."""
        return {
            "host": host_facts(),
            "wall_time_sec": round(self.wall_time_sec, 3),
            "peak_rss_mb": round(self.peak_rss_mb, 3),
            "calls": self.calls,
            "payload_bytes": self.payload_bytes,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "max_call_latency_ms": round(self.max_call_latency_ms, 3),
        }


@dataclass(slots=True)
class ResourceLedger:
    """Mutable accumulator for one campaign's runtime, traffic, and token cost."""

    calls: int = 0
    payload_bytes: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    wall_time_sec: float = 0.0
    peak_rss_mb: float = 0.0

    def record_call(self, payload_bytes: int, latency_ms: float) -> None:
        """Record one external or simulated call with its size and latency."""
        if payload_bytes < 0 or latency_ms < 0.0:
            raise ValueError("recorded call sizes and latencies must be non-negative")
        self.calls += 1
        self.payload_bytes += payload_bytes
        self.latencies_ms.append(latency_ms)

    def record_tokens(self, prompt: int, completion: int) -> None:
        """Record billed language-model tokens for cost accounting."""
        if prompt < 0 or completion < 0:
            raise ValueError("token counts must be non-negative")
        self.prompt_tokens += prompt
        self.completion_tokens += completion

    def usage(self) -> ResourceUsage:
        """Return the immutable measurement accumulated so far."""
        return ResourceUsage(
            wall_time_sec=self.wall_time_sec,
            peak_rss_mb=self.peak_rss_mb,
            calls=self.calls,
            payload_bytes=self.payload_bytes,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            max_call_latency_ms=max(self.latencies_ms, default=0.0),
        )


@contextmanager
def measure() -> Iterator[ResourceLedger]:
    """Measure wall time and peak resident memory around one campaign body."""
    ledger = ResourceLedger()
    started = time.perf_counter()
    try:
        yield ledger
    finally:
        ledger.wall_time_sec = time.perf_counter() - started
        ledger.peak_rss_mb = peak_rss_mb()
