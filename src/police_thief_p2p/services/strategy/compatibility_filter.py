"""Lag-correct bounded particle filter for compatibility observations."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from police_thief_p2p.services.strategy.compatibility_evidence import FAMILIES, Particle, normalize
from police_thief_p2p.services.strategy.compatibility_models import (
    CompatibilityTurnObservation,
    OpponentFingerprint,
)
from police_thief_p2p.services.strategy.compatibility_scent import Cell, decay_only, step_update


class _ParticleFilterMixin:
    """Supply observation updates and normalized posterior diagnostics."""

    def observe(self: Any, observation: CompatibilityTurnObservation) -> OpponentFingerprint:
        """Fold one legal public observation into the lag-correct particle set."""
        if not self._particles:
            raise RuntimeError("start_subgame must be called before observe")
        if observation.step < self._step:
            raise ValueError("observations cannot move backwards")
        if observation.barrier_placed is not None and self._in_bounds(observation.barrier_placed):
            self._barriers.add(observation.barrier_placed)
            self._live_evidence.barriers += 1
        candidates: list[Particle] = []
        exact = observation.capture_claim
        for particle in self._particles:
            served = decay_only(particle.scent, self.rho, self.scent_model)
            scent_likelihood = self._scent_likelihood(served, observation.scent)
            moves = (
                [particle.position]
                if observation.barrier_placed
                else self._successors(particle.position)
            )
            if exact is not None:
                moves = [cell for cell in moves if cell == exact]
            for cell in moves:
                heading = (cell[0] - particle.position[0], cell[1] - particle.position[1])
                candidates.append(
                    Particle(
                        cell,
                        particle.position,
                        step_update(particle.scent, cell, self.size, self.rho, self.scent_model),
                        heading,
                        particle.family,
                        particle.weight
                        * scent_likelihood
                        * self._transition_likelihood(
                            particle.family, particle.position, cell, particle.heading
                        )
                        * self._hint_likelihood(observation.hint, cell),
                    )
                )
        if not candidates and exact is not None and self._passable(exact):
            prior = max(self._particles, key=lambda item: item.weight)
            candidates = [
                Particle(
                    exact,
                    prior.position,
                    step_update(prior.scent, exact, self.size, self.rho, self.scent_model),
                    (exact[0] - prior.position[0], exact[1] - prior.position[1]),
                    family,
                    self._mixture[family],
                )
                for family in FAMILIES
            ]
        self._particles = self._resample(candidates)
        peak = self._posterior_peak_cell()
        if peak is not None:
            self._update_live_evidence(self._last_inferred, peak)
            self._last_inferred = peak
        self._step = max(self._step, observation.step)
        self._update_live_mixture()
        return OpponentFingerprint(
            self._mixture,
            self._audited_subgames,
            self._audited_actions + self._live_evidence.moves,
            self._hint_reliability,
        )

    def _posterior(self: Any) -> dict[Cell, float]:
        posterior: dict[Cell, float] = {}
        for particle in self._particles:
            if particle.position not in self._barriers:
                posterior[particle.position] = (
                    posterior.get(particle.position, 0.0) + particle.weight
                )
        return normalize(posterior) if posterior else {self._opponent_start: 1.0}

    def _posterior_peak_cell(self: Any) -> Cell | None:
        posterior = self._posterior()
        return max(posterior, key=lambda cell: (posterior[cell], -cell[0], -cell[1]), default=None)

    def _resample(self: Any, particles: list[Particle]) -> list[Particle]:
        particles = [item for item in particles if item.position not in self._barriers]
        if not particles:
            scent = step_update({}, self._opponent_start, self.size, self.rho, self.scent_model)
            particles = [
                Particle(
                    self._opponent_start,
                    self._opponent_start,
                    scent,
                    (0, 0),
                    family,
                    self._mixture[family],
                )
                for family in FAMILIES
            ]
        particles.sort(
            key=lambda item: (item.weight, item.family, item.position, item.previous), reverse=True
        )
        selected = particles[: self.profile.particle_count]
        total = sum(item.weight for item in selected)
        weight = 1.0 / len(selected) if not math.isfinite(total) or total <= 0.0 else None
        for particle in selected:
            particle.weight = weight if weight is not None else particle.weight / total
        return selected

    def _scent_likelihood(
        self: Any, predicted: Mapping[Cell, float], observed: Mapping[Cell, float]
    ) -> float:
        if not observed:
            return 1.0
        cells = set(predicted) | set(observed)
        error = sum(abs(predicted.get(cell, 0.0) - observed.get(cell, 0.0)) for cell in cells)
        return max(
            1e-12, math.exp(-self.profile.observation_sharpness * error / max(1, len(cells)))
        )
