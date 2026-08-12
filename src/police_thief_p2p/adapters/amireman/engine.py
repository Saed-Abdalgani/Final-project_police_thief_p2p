"""Sub-game engine: PeerHalf plus amireman capture/survival wire fields."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from police_thief_p2p.adapters.amireman.half import PeerHalf
from police_thief_p2p.adapters.amireman.wire import TurnMessage


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


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
    ) -> None:
        self.half = PeerHalf(role, terms, group, github_commit, sub_game_number, seed)
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

    def take_turn(self) -> TurnMessage:
        out = self.half.act(claim_response=self.pending_response)
        win = {"type": "survival"} if self.survived() else None
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
            self.pending_response = {"claim": list(msg.capture_claim), "caught": bool(caught)}
            outcome.i_am_caught = bool(caught)
        if msg.win_claim and msg.win_claim.get("type") == "survival":
            outcome.opponent_won = True
        return outcome
