"""Faithful thief-first recovery arena and clean-room opponent families."""

from __future__ import annotations

import random
from collections.abc import Iterable
from typing import Any

from police_thief_p2p.services.experiments.compatibility_grid import cell, enclosed, other
from police_thief_p2p.services.experiments.compatibility_opponent_catalog import (
    FAMILY_IDS,
    OPPONENT_REVISIONS,
    TRAINING_FAMILIES,
)
from police_thief_p2p.services.experiments.compatibility_opponents import OpponentState
from police_thief_p2p.services.experiments.compatibility_results import (
    CompatibilityCampaignResult,
    CompatibilityFamilyMetrics,
    CompatibilityMatchOutcome,
    family_metrics,
    match_outcome,
)
from police_thief_p2p.services.experiments.compatibility_turn import ArenaState, execute_turn
from police_thief_p2p.services.strategy.compatibility import (
    CompatibilityStrategyProfile,
    CompatibilityStrategySession,
)
from police_thief_p2p.services.strategy.compatibility_scent import step_update


class CompatibilityArena:
    """Run compatibility matches with pre-emission scent and thief-first turns."""

    def __init__(
        self,
        terms: dict[str, Any],
        profile: CompatibilityStrategyProfile,
        *,
        scent_model: str = "multiplicative_kernel_v1",
    ) -> None:
        """Bind immutable terms and one candidate profile."""
        self.terms, self.profile, self.scent_model = dict(terms), profile, scent_model
        self.size = int(terms["board_size"])
        self.max_steps = int(terms["max_steps"])
        self.max_barriers = int(terms["barriers_max"])
        self.rho = float(terms["decay_per_step"])
        self.cop_start, self.thief_start = cell(terms["cop_start"]), cell(terms["thief_start"])

    def play(self, family: str, role: str, seed: int) -> CompatibilityMatchOutcome:
        """Play one deterministic audited compatibility sub-game."""
        if family not in FAMILY_IDS:
            raise ValueError(f"unknown compatibility family {family!r}")
        if role not in {"police", "thief"}:
            raise ValueError("role must be police or thief")
        session = CompatibilityStrategySession(
            self.terms, self.profile, family, seed, scent_model=self.scent_model
        )
        session.start_subgame(role, 1, family, scent_model=self.scent_model)
        state = ArenaState(
            self.cop_start,
            self.thief_start,
            set(),
            {
                token: step_update({}, start, self.size, self.rho, self.scent_model)
                for token, start in (("police", self.cop_start), ("thief", self.thief_start))
            },
        )
        opponent = OpponentState(
            family,
            other(role),
            random.Random(seed ^ 0x5A17),  # noqa: S311
        )
        records: list[dict[str, Any]] = []
        latencies: list[float] = []
        barriers_placed = useful_barriers = illegal = 0
        for step in range(1, self.max_steps + 1):
            thief_turn = execute_turn(
                self, "thief", role, step, state, session, opponent, records, latencies
            )
            illegal += thief_turn.illegal
            if thief_turn.capture:
                session.complete_audited_subgame(records, audit_passed=True)
                return match_outcome(
                    family,
                    role,
                    "capture",
                    step,
                    illegal,
                    latencies,
                    barriers_placed,
                    useful_barriers,
                )
            if step == self.max_steps:
                session.complete_audited_subgame(records, audit_passed=True)
                return match_outcome(
                    family,
                    role,
                    "survival",
                    step,
                    illegal,
                    latencies,
                    barriers_placed,
                    useful_barriers,
                )
            police_turn = execute_turn(
                self, "police", role, step, state, session, opponent, records, latencies
            )
            illegal += police_turn.illegal
            if police_turn.barrier is not None and role == "police":
                barriers_placed += 1
                useful_barriers += int(police_turn.region_reduction > 0 or police_turn.capture)
            if police_turn.capture or enclosed(state.thief, state.barriers, self.size):
                session.complete_audited_subgame(records, audit_passed=True)
                return match_outcome(
                    family,
                    role,
                    "capture",
                    step,
                    illegal,
                    latencies,
                    barriers_placed,
                    useful_barriers,
                )
        raise AssertionError("the compatibility loop must terminate")

    def evaluate(
        self, families: Iterable[str], seeds: Iterable[int]
    ) -> CompatibilityCampaignResult:
        """Evaluate both roles and aggregate independent family gates."""
        family_values, seed_values = tuple(families), tuple(seeds)
        matches = tuple(
            self.play(family, role, seed)
            for family in family_values
            for seed in seed_values
            for role in ("police", "thief")
        )
        metrics = tuple(family_metrics(family, matches) for family in family_values)
        return CompatibilityCampaignResult(self.profile, metrics, matches)


__all__ = [
    "FAMILY_IDS",
    "OPPONENT_REVISIONS",
    "TRAINING_FAMILIES",
    "CompatibilityArena",
    "CompatibilityCampaignResult",
    "CompatibilityFamilyMetrics",
    "CompatibilityMatchOutcome",
]
