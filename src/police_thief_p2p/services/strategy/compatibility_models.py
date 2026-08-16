"""Lawful public-observation contracts for compatibility strategy sessions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType

Cell = tuple[int, int]


def _cell(value: Cell | None, name: str) -> Cell | None:
    if value is None:
        return None
    if len(value) != 2 or any(
        isinstance(part, bool) or not isinstance(part, int) for part in value
    ):
        raise ValueError(f"{name} must be a pair of integers")
    return (value[0], value[1])


@dataclass(frozen=True, slots=True)
class CompatibilityTurnObservation:
    """One inbound turn containing only fields legally visible on the wire."""

    step: int
    scent: Mapping[Cell, float] = field(default_factory=dict)
    hint: str = ""
    capture_claim: Cell | None = None
    barrier_placed: Cell | None = None

    def __post_init__(self) -> None:
        """Copy and validate the public observation."""
        if isinstance(self.step, bool) or self.step < 0:
            raise ValueError("step must be a non-negative integer")
        if not isinstance(self.hint, str):
            raise ValueError("hint must be text")
        normalized: dict[Cell, float] = {}
        for raw_cell, raw_value in self.scent.items():
            cell = _cell(raw_cell, "scent cell")
            value = float(raw_value)
            if cell is None or not isfinite(value) or value < 0.0:
                raise ValueError("scent values must be finite and non-negative")
            normalized[cell] = value
        object.__setattr__(self, "scent", MappingProxyType(normalized))
        object.__setattr__(self, "capture_claim", _cell(self.capture_claim, "capture_claim"))
        object.__setattr__(self, "barrier_placed", _cell(self.barrier_placed, "barrier_placed"))


@dataclass(frozen=True, slots=True)
class OpponentFingerprint:
    """Audited online mixture over clean-room behavior families."""

    probabilities: Mapping[str, float]
    audited_subgames: int = 0
    observed_actions: int = 0
    hint_reliability: float = 0.5

    def __post_init__(self) -> None:
        """Normalize a validated probability distribution."""
        if self.audited_subgames < 0 or self.observed_actions < 0:
            raise ValueError("fingerprint counts cannot be negative")
        if not 0.0 <= self.hint_reliability <= 1.0:
            raise ValueError("hint_reliability must be in [0, 1]")
        probabilities = {str(name): float(value) for name, value in self.probabilities.items()}
        if not probabilities or any(
            not isfinite(value) or value < 0.0 for value in probabilities.values()
        ):
            raise ValueError("opponent probabilities must be finite and non-negative")
        total = sum(probabilities.values())
        if total <= 0.0:
            raise ValueError("opponent probabilities must have positive mass")
        normalized = {name: value / total for name, value in sorted(probabilities.items())}
        object.__setattr__(self, "probabilities", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class CompatibilityStrategyMetrics:
    """Bounded diagnostics emitted with a compatibility decision."""

    particle_count: int
    posterior_peak: float
    posterior_entropy: float
    opponent_family: str
    lookahead_depth: int
    latency_ms: float
    reason_code: str

    def __post_init__(self) -> None:
        """Validate finite metric values."""
        if self.particle_count < 0 or self.lookahead_depth < 0:
            raise ValueError("strategy counts cannot be negative")
        for name, value in (
            ("posterior_peak", self.posterior_peak),
            ("posterior_entropy", self.posterior_entropy),
            ("latency_ms", self.latency_ms),
        ):
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class CompatibilityDecision:
    """One legal action plus its bounded natural-language hint."""

    move: str
    barrier: Cell | None
    hint: str
    intent: str
    metrics: CompatibilityStrategyMetrics

    def __post_init__(self) -> None:
        """Validate the action, intent, and optional barrier."""
        if self.move not in {"N", "S", "E", "W", "STAY"}:
            raise ValueError("move must be N, S, E, W, or STAY")
        object.__setattr__(self, "barrier", _cell(self.barrier, "barrier"))
        if self.intent not in {"truth", "lie"}:
            raise ValueError("intent must be truth or lie")
        if not isinstance(self.hint, str):
            raise ValueError("hint must be text")


__all__ = [
    "CompatibilityDecision",
    "CompatibilityStrategyMetrics",
    "CompatibilityTurnObservation",
    "OpponentFingerprint",
]
