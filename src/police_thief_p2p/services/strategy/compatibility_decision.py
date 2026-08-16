"""Decision orchestration and bounded metrics for compatibility strategy."""

from __future__ import annotations

import math
import time
from typing import Any

from police_thief_p2p.services.strategy.compatibility_graph import move
from police_thief_p2p.services.strategy.compatibility_models import (
    CompatibilityDecision,
    CompatibilityStrategyMetrics,
)
from police_thief_p2p.services.strategy.compatibility_scent import Cell


class _DecisionMixin:
    """Dispatch role policy, update local state, and emit diagnostics."""

    def decide(
        self: Any,
        *,
        position: Cell | None = None,
        barriers: set[Cell] | None = None,
        barriers_used: int | None = None,
        step: int | None = None,
    ) -> CompatibilityDecision:
        """Choose a legal risk-sensitive action and a parser-safe coarse hint."""
        if not self._particles:
            raise RuntimeError("start_subgame must be called before decide")
        started = time.perf_counter()
        if position is not None:
            self._own_pos = (int(position[0]), int(position[1]))
        if barriers is not None:
            self._barriers = set(barriers)
        if barriers_used is not None:
            self._barriers_used = int(barriers_used)
        if step is not None:
            self._step = int(step)
        if self._role == "police":
            action, barrier, reason = self._decide_police()
        else:
            action, barrier, reason = self._decide_thief()
        hint_position = self._own_pos if barrier is not None else move(self._own_pos, action)
        hint, intent = self._choose_hint(hint_position)
        if barrier is not None:
            self._barriers.add(barrier)
            self._barriers_used += 1
            action = "STAY"
        else:
            self._own_pos = move(self._own_pos, action)
        self._history.append(self._own_pos)
        self._last_move = action
        posterior = self._posterior()
        metrics = CompatibilityStrategyMetrics(
            len(self._particles),
            max(posterior.values(), default=0.0),
            -sum(value * math.log(value) for value in posterior.values() if value > 0.0),
            max(self._mixture, key=self._mixture.get),
            self.profile.lookahead_depth,
            (time.perf_counter() - started) * 1000.0,
            reason,
        )
        return CompatibilityDecision(action, barrier, hint, intent, metrics)
