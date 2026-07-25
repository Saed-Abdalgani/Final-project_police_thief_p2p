"""Immutable public contracts for deadline-safe strategy decisions."""

import math
import re
from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.domain.values import Action

_REASON = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


class HintVerdict(StrEnum):
    """Truth status sealed with the natural-language hint."""

    TRUTH = "truth"
    LIE = "lie"


class SemanticRegion(StrEnum):
    """Coarse non-coordinate spatial intent used by hint realization."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    CENTER = "center"
    EDGE = "edge"
    CORNER = "corner"
    NEUTRAL = "neutral"


class BehaviorMode(StrEnum):
    """Prevalidated Thief behavior modes."""

    MOBILITY = "mobility"
    DECEPTION = "deception"
    ESCAPE = "escape"
    ANTI_TRAP = "anti-trap"


@dataclass(frozen=True, slots=True)
class HintIntent:
    """Movement-independent semantic hint plan."""

    verdict: HintVerdict
    region: SemanticRegion


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    """Finite ordered feature values with an aggregate score."""

    features: tuple[tuple[str, float], ...]
    total: float

    def __post_init__(self) -> None:
        """Reject duplicate, unsafe, or non-finite telemetry."""
        names = [name for name, _ in self.features]
        if len(names) != len(set(names)) or any(not _REASON.fullmatch(name) for name in names):
            raise ValueError("score feature names must be unique safe codes")
        values = (self.total, *(value for _, value in self.features))
        if any(not math.isfinite(value) for value in values):
            raise ValueError("strategy score breakdown must be finite")


@dataclass(frozen=True, slots=True)
class DecisionMetrics:
    """Safe reproducibility and search telemetry."""

    latency_ms: float
    candidates: int
    completed_depth: int
    cache_hits: int
    seed: int
    profile_version: str
    score: ScoreBreakdown

    def __post_init__(self) -> None:
        """Validate bounded counters and finite latency."""
        if not math.isfinite(self.latency_ms) or self.latency_ms < 0:
            raise ValueError("strategy latency must be finite and non-negative")
        if min(self.candidates, self.completed_depth, self.cache_hits, self.seed) < 0:
            raise ValueError("strategy metric counters must be non-negative")
        if not self.profile_version:
            raise ValueError("strategy profile version is required")


@dataclass(frozen=True, slots=True)
class Decision:
    """One guarded action, hint plan, explanation, and safe metrics."""

    action: Action
    hint_intent: HintIntent
    hint: str
    reason_code: str
    metrics: DecisionMetrics
    fallback_used: bool = False

    def __post_init__(self) -> None:
        """Enforce typed, concise, redaction-friendly output."""
        if not isinstance(self.action, Action):
            raise TypeError("decision action must be a domain Action")
        if not isinstance(self.hint_intent, HintIntent):
            raise TypeError("decision hint_intent must be typed")
        if _REASON.fullmatch(self.reason_code) is None:
            raise ValueError("strategy reason code is invalid")
        if not self.hint or len(self.hint) > 2_000:
            raise ValueError("strategy hint must be non-empty and bounded")

    def telemetry(self) -> dict[str, object]:
        """Return safe telemetry without hint content or private state."""
        return {
            "latency_ms": round(self.metrics.latency_ms, 3),
            "candidates": self.metrics.candidates,
            "depth": self.metrics.completed_depth,
            "cache_hits": self.metrics.cache_hits,
            "reason_code": self.reason_code,
            "fallback": self.fallback_used,
            "score_total": round(self.metrics.score.total, 6),
            "profile_version": self.metrics.profile_version,
            "seed": self.metrics.seed,
        }
