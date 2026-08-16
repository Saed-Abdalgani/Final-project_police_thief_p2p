"""Series and sub-game lifecycle state for compatibility strategy."""

from __future__ import annotations

import random
from collections.abc import Mapping
from typing import Any

from police_thief_p2p.services.strategy.compatibility_evidence import FAMILIES, Evidence, Particle
from police_thief_p2p.services.strategy.compatibility_graph import as_cell
from police_thief_p2p.services.strategy.compatibility_models import OpponentFingerprint
from police_thief_p2p.services.strategy.compatibility_profile import CompatibilityStrategyProfile
from police_thief_p2p.services.strategy.compatibility_scent import Cell, step_update


class _LifecycleMixin:
    """Own persistent audited learning and resettable board state."""

    def __init__(
        self,
        terms: Mapping[str, Any],
        profile: CompatibilityStrategyProfile,
        opponent_id: str,
        seed: int,
        *,
        scent_model: str = "multiplicative_kernel_v1",
    ) -> None:
        """Initialize private series state without opponent truth."""
        self.terms, self.profile = dict(terms), profile
        self.opponent_id, self.seed, self.scent_model = opponent_id, int(seed), scent_model
        self.size = int(terms["board_size"])
        self.rho = float(terms["decay_per_step"])
        self.max_steps = int(terms["max_steps"])
        self.max_barriers = int(terms["barriers_max"])
        self.hint_max_words = int(terms.get("hint_max_words", 15))
        self.setting = str(terms.get("setting", "city"))
        self._base_mixture = {name: 1.0 / len(FAMILIES) for name in FAMILIES}
        self._mixture = dict(self._base_mixture)
        self._audited_subgames = self._audited_actions = 0
        self._hint_reliability = 0.5
        self._rng = random.Random(self.seed)  # noqa: S311 - secret-seeded game mixing
        self._particles: list[Particle] = []
        self._role, self._sub_game = "police", 0
        self._own_pos = self._opponent_start = (0, 0)
        self._barriers: set[Cell] = set()
        self._barriers_used = self._step = self._consecutive_lies = 0
        self._history: list[Cell] = []
        self._last_move = "STAY"
        self._live_evidence = Evidence()
        self._last_inferred: Cell | None = None

    @property
    def profile_digest(self) -> str:
        """Return the frozen strategy profile digest."""
        return self.profile.digest()

    @property
    def fingerprint(self) -> OpponentFingerprint:
        """Return learning derived only from completed audited sub-games."""
        return OpponentFingerprint(
            self._base_mixture,
            self._audited_subgames,
            self._audited_actions,
            self._hint_reliability,
        )

    @property
    def particle_weights(self) -> tuple[float, ...]:
        """Expose normalized weights for diagnostics and property tests."""
        return tuple(particle.weight for particle in self._particles)

    @property
    def particle_positions(self) -> tuple[Cell, ...]:
        """Expose inferred positions for barrier-mask diagnostics."""
        return tuple(particle.position for particle in self._particles)

    def start_subgame(
        self,
        role: str,
        sub_game: int,
        opponent_id: str | None = None,
        *,
        scent_model: str | None = None,
    ) -> None:
        """Reset board state while retaining only previously audited learning."""
        if role not in {"police", "thief"}:
            raise ValueError("role must be police or thief")
        self._role, self._sub_game = role, int(sub_game)
        self.opponent_id = opponent_id or self.opponent_id
        self.scent_model = scent_model or self.scent_model
        own_key = "cop_start" if role == "police" else "thief_start"
        opponent_key = "thief_start" if role == "police" else "cop_start"
        self._own_pos = as_cell(self.terms[own_key])
        self._opponent_start = as_cell(self.terms[opponent_key])
        self._barriers.clear()
        self._barriers_used = self._step = self._consecutive_lies = 0
        self._history, self._last_move = [self._own_pos], "STAY"
        self._live_evidence = Evidence()
        self._last_inferred = self._opponent_start
        self._mixture = dict(self._base_mixture)
        scent = step_update({}, self._opponent_start, self.size, self.rho, self.scent_model)
        count = self.profile.particle_count
        self._particles = [
            Particle(
                self._opponent_start,
                self._opponent_start,
                dict(scent),
                (0, 0),
                FAMILIES[index % len(FAMILIES)],
                1.0 / count,
            )
            for index in range(count)
        ]
        self._rng.seed(self.seed ^ (self._sub_game * 0x9E3779B1))
