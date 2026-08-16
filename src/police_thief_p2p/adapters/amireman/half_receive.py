"""Inbound observation handling for an amireman peer half."""

from __future__ import annotations

from typing import Any

from police_thief_p2p.adapters.amireman.capture import (
    as_cell,
    evaluate_thief_caught,
    thief_trapped,
)
from police_thief_p2p.adapters.amireman.scent import grid_in
from police_thief_p2p.sdk import CompatibilityTurnObservation


class PeerHalfReceiveMixin:
    """Fold lawful public observations into local strategy state."""

    role: str
    size: int
    pos: tuple[int, int]
    barriers: set[tuple[int, int]]
    recv_scent: dict[tuple[int, int], float]
    known_opp: tuple[int, int] | None
    last_target: tuple[int, int] | None
    strategy_session: Any
    step: int

    def receive(self, msg: dict[str, Any]) -> bool:
        """Fold inbound public fields; return True if this Thief is caught."""
        self.recv_scent = grid_in(msg.get("scent") or msg.get("smell_grid"))
        claim = msg.get("claim") if "claim" in msg else msg.get("capture_claim")
        if claim is None:
            claim = msg.get("capture_claim")
        barrier = msg.get("barrier_placed")
        barrier_cell = as_cell(barrier)
        if (
            barrier_cell is not None
            and 0 <= barrier_cell[0] < self.size
            and 0 <= barrier_cell[1] < self.size
            and barrier_cell not in self.barriers
        ):
            self.barriers.add(barrier_cell)
        if self.strategy_session is not None:
            self.strategy_session.observe(
                CompatibilityTurnObservation(
                    step=int(msg.get("step", self.step)),
                    scent=self.recv_scent,
                    hint=str(msg.get("hint", "")),
                    capture_claim=as_cell(claim),
                    barrier_placed=barrier_cell,
                )
            )
        if self.role == "thief":
            cop = as_cell(claim) or as_cell(msg.get("capture_claim"))
            if cop is not None:
                self.last_target, self.known_opp = self.known_opp, cop
            elif self.recv_scent and self.known_opp is None:
                self.known_opp = max(self.recv_scent.items(), key=lambda item: item[1])[0]
        if self.role == "police" and self.recv_scent:
            peak = max(self.recv_scent.items(), key=lambda item: item[1])[0]
            self.last_target, self.known_opp = self.known_opp, peak
        if self.role != "thief":
            return False
        return evaluate_thief_caught(
            thief=self.pos,
            claim=claim,
            barrier=barrier,
            barriers=self.barriers,
            size=self.size,
        )

    def enclosed(self) -> bool:
        """Return whether this Thief has no orthogonal escape."""
        return self.role == "thief" and thief_trapped(self.pos, self.barriers, self.size)
