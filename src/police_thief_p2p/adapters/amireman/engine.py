"""Sub-game engine: PeerHalf plus amireman capture/survival wire fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from police_thief_p2p.adapters.amireman.engine_helpers import now_iso, win_kind
from police_thief_p2p.adapters.amireman.half import PeerHalf
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.wire import TurnMessage

if TYPE_CHECKING:
    from police_thief_p2p.sdk import CompatibilityStrategySession


@dataclass
class IncomingOutcome:
    """Local interpretation of one received public turn."""

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
        strategy_session: CompatibilityStrategySession | None = None,
    ) -> None:
        """Create one role-specific compatibility sub-game engine."""
        self.half = PeerHalf(
            role,
            terms,
            group,
            github_commit,
            sub_game_number,
            seed,
            scent_model,
            strategy_session,
        )
        self.role = role
        self.threshold = int(terms["max_steps"])
        self.pending_response: dict[str, Any] | None = None

    @property
    def records(self) -> list[dict[str, Any]]:
        """Return this side's sealed audit records."""
        return self.half.records

    @property
    def step(self) -> int:
        """Return the number of actions emitted by this side."""
        return self.half.step

    def survived(self) -> bool:
        """Return whether the local Thief reached the survival threshold."""
        return self.role == "thief" and self.half.step >= self.threshold

    def ceiling_reached(self) -> bool:
        """Return whether the configured turn ceiling was reached."""
        return self.half.step >= self.threshold

    def take_turn(self) -> TurnMessage:
        """Compute and seal one normal outgoing turn."""
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
            timestamp=now_iso(),
            barrier_placed=out["barrier_placed"],
            capture_claim=out["claim"],
            claim_response=self.pending_response,
            win_claim=win,
        )
        self.pending_response = None
        return message

    def concede(self) -> TurnMessage:
        """Seal a final hold response after a verified capture."""
        out = self.half.hold(claim_response=self.pending_response)
        message = TurnMessage(
            step=out["step"],
            sender=out["sender"],
            commit=out["commit"],
            hint=out["hint"],
            smell_grid=out["scent"],
            timestamp=now_iso(),
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
            timestamp=now_iso(),
            barrier_placed=None,
            capture_claim=None,
            claim_response=None,
            win_claim={"type": "capture"},
        )

    def receive(self, msg: TurnMessage) -> IncomingOutcome:
        """Apply one inbound turn and classify its terminal implications."""
        legacy = {
            "step": msg.step,
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
        kind = win_kind(msg.win_claim)
        if kind == "survival":
            outcome.opponent_won = True
        elif kind in {"capture", "enclosure"}:
            if self.role == "police":
                outcome.i_won = True
            else:
                outcome.i_am_caught = True
        return outcome
