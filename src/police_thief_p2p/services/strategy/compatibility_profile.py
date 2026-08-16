"""Frozen bounded profile for the compatibility recovery strategy."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class CompatibilityStrategyProfile:
    """Frozen, bounded parameters used by one league-recovery campaign."""

    profile: str = "league-recovery"
    profile_version: str = "2.0.0"
    particle_count: int = 64
    observation_sharpness: float = 12.0
    opponent_decay: float = 0.90
    lookahead_depth: int = 3
    cvar_tail: float = 0.25
    near_tie_epsilon: float = 0.02
    decision_budget_ms: int = 250
    police_capture: float = 1000.0
    police_pursuit: float = 5.0
    police_intercept: float = 5.0
    police_cut: float = 8.0
    police_enclosure: float = 12.0
    police_risk: float = 0.30
    police_budget: float = 1.5
    police_cycle: float = 3.0
    thief_immediate_risk: float = 1000.0
    thief_territory: float = 1.5
    thief_routes: float = 12.0
    thief_trap: float = 100.0
    thief_scent: float = 3.0
    thief_boundary: float = 8.0
    thief_unpredictability: float = 5.0
    hint_urgency: float = 0.55
    max_consecutive_lies: int = 2

    def __post_init__(self) -> None:
        """Reject unbounded campaign parameters."""
        if not 16 <= self.particle_count <= 512:
            raise ValueError("particle_count must be in [16, 512]")
        if not 1 <= self.lookahead_depth <= 4:
            raise ValueError("lookahead_depth must be in [1, 4]")
        if not 0.05 <= self.cvar_tail <= 1.0:
            raise ValueError("cvar_tail must be in [0.05, 1]")
        if not 0.0 < self.opponent_decay <= 1.0:
            raise ValueError("opponent_decay must be in (0, 1]")
        if self.max_consecutive_lies < 1:
            raise ValueError("max_consecutive_lies must be positive")

    def digest(self) -> str:
        """Return a stable digest that binds a deployment to these weights."""
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()
