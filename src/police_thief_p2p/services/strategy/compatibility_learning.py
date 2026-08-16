"""Audit-gated cross-game opponent learning and private snapshots."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Any, cast

from police_thief_p2p.services.strategy.compatibility_evidence import (
    FAMILIES,
    Evidence,
    add_evidence,
    evidence_mixture,
    normalize,
)
from police_thief_p2p.services.strategy.compatibility_models import OpponentFingerprint
from police_thief_p2p.services.strategy.compatibility_scent import Cell

STATE_CELL = re.compile(r"self=\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]")


class _LearningMixin:
    """Supply public live classification and post-audit exact updates."""

    def complete_audited_subgame(
        self: Any,
        records: Sequence[Mapping[str, Any]],
        *,
        audit_passed: bool,
    ) -> OpponentFingerprint:
        """Learn exact behavior only after the peer's sealed record passes audit."""
        if not audit_passed:
            return cast("OpponentFingerprint", self.fingerprint)
        evidence = Evidence()
        positions: list[Cell] = []
        hints = truth_hints = 0
        for record in records:
            payload = record.get("payload")
            if not isinstance(payload, Mapping) or int(payload.get("step", 0)) <= 0:
                continue
            match = STATE_CELL.search(str(payload.get("state", "")))
            if match is not None:
                positions.append((int(match.group(1)), int(match.group(2))))
            evidence.barriers += int(payload.get("barrier_placed") is not None)
            if str(payload.get("hint", "")).strip():
                hints += 1
                truth_hints += int(payload.get("intent", "truth") == "truth")
        for previous, current in pairwise(positions):
            add_evidence(evidence, previous, current, self.size)
        audited_mix = evidence_mixture(evidence)
        decay = self.profile.opponent_decay
        self._base_mixture = normalize(
            {
                family: decay * self._base_mixture[family] + (1.0 - decay) * audited_mix[family]
                for family in FAMILIES
            }
        )
        self._mixture = dict(self._base_mixture)
        self._audited_subgames += 1
        self._audited_actions += evidence.moves
        if hints:
            observed = truth_hints / hints
            self._hint_reliability = decay * self._hint_reliability + (1.0 - decay) * observed
        return cast("OpponentFingerprint", self.fingerprint)

    def training_snapshot(self: Any) -> dict[str, Any]:
        """Return replay metadata suitable only for a post-series local sidecar."""
        fingerprint = self.fingerprint
        return {
            "strategy_seed": self.seed,
            "profile": self.profile.profile,
            "profile_version": self.profile.profile_version,
            "profile_digest": self.profile_digest,
            "opponent_id": self.opponent_id,
            "audited_subgames": fingerprint.audited_subgames,
            "observed_actions": fingerprint.observed_actions,
            "opponent_mixture": dict(fingerprint.probabilities),
            "hint_reliability": fingerprint.hint_reliability,
        }

    def _update_live_evidence(self: Any, previous: Cell | None, current: Cell) -> None:
        if previous is not None:
            add_evidence(self._live_evidence, previous, current, self.size)
        self._live_evidence.position_counts[current] += 1

    def _update_live_mixture(self: Any) -> None:
        evidence_mix = evidence_mixture(self._live_evidence)
        strength = min(0.35, self._live_evidence.moves / 40.0)
        self._mixture = normalize(
            {
                family: (1.0 - strength) * self._base_mixture[family]
                + strength * evidence_mix[family]
                for family in FAMILIES
            }
        )
