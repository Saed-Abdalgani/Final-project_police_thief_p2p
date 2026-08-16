"""Sub-game engine: PeerHalf plus amireman capture/survival wire fields."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from police_thief_p2p.adapters.amireman.half import PeerHalf
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.wire import TurnMessage


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _win_kind(win_claim: dict | str | None) -> str | None:
    if isinstance(win_claim, str) and win_claim:
        return win_claim
    if isinstance(win_claim, dict):
        kind = win_claim.get("type") or win_claim.get("result")
        return str(kind) if kind else None
    return None


@dataclass
class IncomingOutcome:
    i_won: bool = False
    i_am_caught: bool = False
    opponent_won: bool = False


class SubEngine:
    """One side of one sub-game against a remote opponent."""

    def __init__(
        self,
        role: str,
        terms: dict[str, Any],
        group: str,
        github_commit: str,
        sub_game_number: int,
        seed: int = 1234,
        scent_model: str = MULTIPLICATIVE_KERNEL_V1,
    ) -> None:
        self.half = PeerHalf(role, terms, group, github_commit, sub_game_number, seed, scent_model)
        self.role = role
        self.threshold = int(terms["max_steps"])
        self.pending_response: dict | None = None

    @property
    def records(self) -> list:
        return self.half.records

    @property
    def step(self) -> int:
        return self.half.step

    def survived(self) -> bool:
        return self.role == "thief" and self.half.step >= self.threshold

    def ceiling_reached(self) -> bool:
        return self.half.step >= self.threshold

    def take_turn(self) -> TurnMessage:
        out = self.half.act(claim_response=self.pending_response)
        win = None
        if self.half.enclosed():
            win = {"type": "capture"}
        elif self.survived() or self.ceiling_reached():
            win = {"type": "survival"}
        message = TurnMessage(
            step=out["step"],
            sender=out["sender"],
            commit=out["commit"],
            hint=out["hint"],
            smell_grid=out["scent"],
            timestamp=_now_iso(),
            barrier_placed=out["barrier_placed"],
            capture_claim=out["claim"],
            claim_response=self.pending_response,
            win_claim=win,
        )
        self.pending_response = None
        return message

    def concede(self) -> TurnMessage:
        out = self.half.hold(claim_response=self.pending_response)
        message = TurnMessage(
            step=out["step"],
            sender=out["sender"],
            commit=out["commit"],
            hint=out["hint"],
            smell_grid=out["scent"],
            timestamp=_now_iso(),
            barrier_placed=None,
            capture_claim=None,
            claim_response=self.pending_response,
            win_claim=None,
        )
        self.pending_response = None
        return message

    def report_enclosure(self) -> TurnMessage:
        """Thief self-report: enclosed, no orthogonal escape, STAY does not save it."""
        out = self.half.hold()
        return TurnMessage(
            step=out["step"],
            sender=out["sender"],
            commit=out["commit"],
            hint=out["hint"],
            smell_grid=out["scent"],
            timestamp=_now_iso(),
            barrier_placed=None,
            capture_claim=None,
            claim_response=None,
            win_claim={"type": "capture"},
        )

    def receive(self, msg: TurnMessage) -> IncomingOutcome:
        legacy = {
            "hint": msg.hint,
            "scent": msg.smell_grid,
            "smell_grid": msg.smell_grid,
            "claim": msg.capture_claim,
            "capture_claim": msg.capture_claim,
            "barrier_placed": msg.barrier_placed,
        }
        caught = self.half.receive(legacy)
        outcome = IncomingOutcome()
        if self.role == "police" and msg.claim_response and msg.claim_response.get("caught"):
            outcome.i_won = True
        if self.role == "thief" and msg.capture_claim is not None:
            from police_thief_p2p.adapters.amireman.capture import as_cell

            cell = as_cell(msg.capture_claim)
            self.pending_response = {
                "claim": list(cell) if cell is not None else [0, 0],
                "caught": bool(caught),
            }
            outcome.i_am_caught = bool(caught)
        kind = _win_kind(msg.win_claim)
        if kind == "survival":
            outcome.opponent_won = True
        elif kind in {"capture", "enclosure"}:
            if self.role == "police":
                outcome.i_won = True
            else:
                outcome.i_am_caught = True
        return outcome
