"""Risk-sensitive Police policy for compatibility sessions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from police_thief_p2p.services.strategy.compatibility_evidence import weighted_lower_tail
from police_thief_p2p.services.strategy.compatibility_graph import move
from police_thief_p2p.services.strategy.compatibility_scent import Cell


class _PolicePolicyMixin:
    """Supply belief-state expectimax and graph-cut Police decisions."""

    def _decide_police(self: Any) -> tuple[str, Cell | None, str]:
        posterior = self._posterior()
        actions: list[tuple[str, Cell | None]] = [
            (action, None) for action in self._legal_moves(self._own_pos)
        ]
        if self._barriers_used < self.max_barriers:
            actions.extend(("STAY", cell) for cell in self._neighbors(self._own_pos))
        scored: list[tuple[float, str, Cell | None, str]] = []
        for action, barrier in actions:
            values: list[tuple[float, float]] = []
            for thief, probability in posterior.items():
                value = self._police_sample_value(action, barrier, thief)
                if value is None:
                    values = []
                    break
                values.append((value, probability))
            if not values:
                continue
            mean = sum(value * probability for value, probability in values)
            tail = weighted_lower_tail(values, self.profile.cvar_tail)
            score = (1.0 - self.profile.police_risk) * mean + self.profile.police_risk * tail
            reason = "belief-expectimax"
            if barrier is not None:
                captured_mass = posterior.get(barrier, 0.0)
                cut = self._expected_cut(barrier, posterior)
                if captured_mass < 0.20 and cut < 2.0:
                    continue
                reason = "posterior-capture" if captured_mass >= 0.20 else "graph-cut"
            scored.append((score, action, barrier, reason))
        if not scored:
            return "STAY", None, "safe-fallback"
        scored.sort(key=lambda item: (item[0], item[2] is None, item[1]), reverse=True)
        _, action, barrier, reason = scored[0]
        return action, barrier, reason

    def _police_sample_value(
        self: Any, action: str, barrier: Cell | None, thief: Cell
    ) -> float | None:
        profile = self.profile
        if barrier is not None:
            updated = self._barriers | {barrier}
            if barrier != thief and self._reachable(self._own_pos, updated) < 6:
                return None
            if barrier == thief:
                return float(profile.police_capture - profile.police_budget)
            old_region = self._reachable(thief, self._barriers)
            new_region = self._reachable(thief, updated)
            if new_region == 0:
                return float(profile.police_capture + profile.police_enclosure)
            distance = self._distance(self._own_pos, thief, updated)
            if distance is None:
                return None
            return float(
                profile.police_cut * (old_region - new_region)
                - profile.police_pursuit * distance
                - profile.police_budget
            )
        cop = move(self._own_pos, action)
        if cop == thief:
            return float(profile.police_capture)
        future, previous, value = thief, thief, 0.0
        for depth in range(profile.lookahead_depth):
            replies = self._legal_cells(future)
            if not replies:
                return float(profile.police_capture + profile.police_enclosure)
            future = max(
                replies,
                key=lambda cell: (
                    self._distance_or_far(cop, cell),
                    self._degree(cell),
                    -self._boundary_penalty(cell),
                ),
            )
            if future == cop:
                return float(profile.police_capture)
            distance = self._distance_or_far(cop, future)
            turn = int(
                depth == 0
                and self._last_inferred is not None
                and (future[0] - previous[0], future[1] - previous[1])
                != (previous[0] - self._last_inferred[0], previous[1] - self._last_inferred[1])
            )
            value -= profile.police_pursuit * distance / (depth + 1)
            value += profile.police_intercept * (1 - turn) / (depth + 1)
            if depth + 1 < profile.lookahead_depth:
                cop = min(
                    self._legal_cells(cop), key=lambda cell: self._distance_or_far(cell, future)
                )
                if cop == future:
                    return float(profile.police_capture / (depth + 2))
            previous = future
        if len(self._history) >= 5 and self._history[-1] in self._history[-5:-1]:
            value -= profile.police_cycle
        return value

    def _expected_cut(self: Any, barrier: Cell, posterior: Mapping[Cell, float]) -> float:
        updated = self._barriers | {barrier}
        return float(
            sum(
                probability
                * max(0, self._reachable(cell, self._barriers) - self._reachable(cell, updated))
                for cell, probability in posterior.items()
                if cell != barrier
            )
        )
