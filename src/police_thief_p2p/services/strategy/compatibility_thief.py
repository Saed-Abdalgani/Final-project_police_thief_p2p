"""One-turn minimax Thief policy for compatibility sessions."""

from __future__ import annotations

from typing import Any

from police_thief_p2p.services.strategy.compatibility_evidence import weighted_lower_tail
from police_thief_p2p.services.strategy.compatibility_graph import move
from police_thief_p2p.services.strategy.compatibility_scent import Cell


class _ThiefPolicyMixin:
    """Supply immediate-risk veto and mobility-aware evasion decisions."""

    def _decide_thief(self: Any) -> tuple[str, Cell | None, str]:
        posterior = self._posterior()
        support = {cell: mass for cell, mass in posterior.items() if mass >= 0.02}
        scored: list[tuple[float, str]] = []
        safe: list[tuple[float, str]] = []
        for action in self._legal_moves(self._own_pos):
            candidate = move(self._own_pos, action)
            risk_mass = 0.0
            sample_values: list[tuple[float, float]] = []
            for cop, probability in posterior.items():
                immediate = candidate in self._legal_cells(cop)
                risk_mass += probability if immediate else 0.0
                sample_values.append(
                    (self._thief_sample_value(candidate, cop, immediate), probability)
                )
            mean = sum(value * probability for value, probability in sample_values)
            worst = weighted_lower_tail(sample_values, self.profile.cvar_tail)
            item = (0.60 * worst + 0.40 * mean, action)
            scored.append(item)
            hard_threat = any(candidate in self._legal_cells(cop) for cop in support)
            if not hard_threat and risk_mass < 0.01:
                safe.append(item)
        pool = safe or scored
        if not pool:
            return "STAY", None, "forced-hold"
        best_score = max(score for score, _ in pool)
        tolerance = max(1e-9, abs(best_score) * self.profile.near_tie_epsilon)
        near = sorted(action for score, action in pool if best_score - score <= tolerance)
        return self._rng.choice(near), None, "minimax-veto" if safe else "least-risk"

    def _thief_sample_value(self: Any, candidate: Cell, cop: Cell, immediate: bool) -> float:
        profile = self.profile
        if immediate:
            return -float(profile.thief_immediate_risk)
        distance = self._distance_or_far(candidate, cop)
        territory = self._owned_territory(candidate, cop)
        routes = self._degree(candidate)
        reachable = self._reachable(candidate, self._barriers)
        boundary = self._boundary_penalty(candidate)
        visits = self._history.count(candidate)
        reversal = int(len(self._history) >= 2 and candidate == self._history[-2])
        straight = int(
            len(self._history) >= 2
            and (candidate[0] - self._own_pos[0], candidate[1] - self._own_pos[1])
            == (self._own_pos[0] - self._history[-2][0], self._own_pos[1] - self._history[-2][1])
        )
        future_worst = min(
            (
                self._distance_or_far(next_cell, police_next)
                for police_next in self._legal_cells(cop)
                for next_cell in self._legal_cells(candidate)
                if next_cell != police_next
            ),
            default=0,
        )
        return float(
            profile.thief_immediate_risk * min(1.0, distance / max(1, self.size * 2))
            + profile.thief_territory * territory
            + profile.thief_routes * routes
            + 0.25 * profile.thief_territory * reachable
            + profile.thief_routes * future_worst
            - profile.thief_trap * int(routes <= 1)
            - profile.thief_boundary * boundary
            - profile.thief_scent * visits
            - profile.thief_unpredictability * (reversal + straight)
        )

    def _owned_territory(self: Any, thief: Cell, cop: Cell) -> int:
        owned = 0
        for row in range(self.size):
            for col in range(self.size):
                cell = (row, col)
                if cell not in self._barriers and self._distance_or_far(
                    thief, cell
                ) < self._distance_or_far(cop, cell):
                    owned += 1
        return owned
