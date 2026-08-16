"""One sub-game over the pushed-turn amireman wire."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from police_thief_p2p.adapters.amireman.delivery import (
    EquivocationError,
    Inbox,
    ProtocolViolationError,
)
from police_thief_p2p.adapters.amireman.engine import SubEngine
from police_thief_p2p.adapters.amireman.engine_helpers import now_iso, win_kind
from police_thief_p2p.adapters.amireman.runtime_audit import SubGameAuditMixin
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.wire import TurnMessage

if TYPE_CHECKING:
    from police_thief_p2p.sdk import CompatibilityStrategySession


class SubGameRuntime(SubGameAuditMixin):
    """Runs one sub-game against a remote opponent."""

    def __init__(
        self,
        role: str,
        terms: dict[str, Any],
        transport: Any,
        group: str,
        github_commit: str,
        sub_game_number: int,
        seed: int = 1234,
        listener: Callable[[dict[str, Any]], None] | None = None,
        scent_model: str = MULTIPLICATIVE_KERNEL_V1,
        strategy_session: CompatibilityStrategySession | None = None,
    ) -> None:
        """Bind one sub-game engine to its pushed-turn transport."""
        self.engine = SubEngine(
            role,
            terms,
            group,
            github_commit,
            sub_game_number,
            seed,
            scent_model=scent_model,
            strategy_session=strategy_session,
        )
        self.transport = transport
        self.inbox = Inbox(window=4)
        self.role = role
        self.n = sub_game_number
        self._listen = listener or (lambda _event: None)
        self.result: tuple[str, str] | None = None
        self.started_at = now_iso()
        self._t0 = time.monotonic()
        self.deferred_consensus: dict[str, Any] | None = None
        self._peer_audit: dict[str, Any] | None = None
        self.peer_records: list[dict[str, Any]] = []

    def run(self, turn_timeout: float = 180.0, poll: float = 0.3) -> dict[str, Any]:
        """Run turns and the mutual audit to a terminal summary."""
        if self.role == "thief":
            self._take_turn()
        deadline = time.monotonic() + turn_timeout
        last_notice = time.monotonic()
        while True:
            if bool(self.result):
                break
            incoming = self.transport.poll_turn(poll)
            self._absorb_audits()
            if bool(self.result):
                break
            if incoming is None:
                now = time.monotonic()
                if now - last_notice >= 10.0:
                    self._listen(
                        {
                            "type": "waiting",
                            "sub_game": self.n,
                            "role": self.role,
                            "step": self.engine.step,
                            "seconds": int(now - (deadline - turn_timeout)),
                        }
                    )
                    last_notice = now
                if now > deadline:
                    self.result = ("timeout", self.role)
                continue
            deadline = time.monotonic() + turn_timeout
            last_notice = time.monotonic()
            try:
                ready = self.inbox.offer(incoming)
            except (EquivocationError, ProtocolViolationError):
                self.result = ("technical_loss", "-")
                break
            for raw in ready:
                self._process(TurnMessage.from_wire(raw))
                if bool(self.result):
                    break
        outcome = self.result[0] if self.result is not None else "timeout"
        self._listen(
            {
                "type": "ended",
                "sub_game": self.n,
                "role": self.role,
                "result": outcome,
                "step": self.engine.step,
            }
        )
        return self._finish(turn_timeout)

    def _take_turn(self) -> None:
        message = self.engine.take_turn()
        self.transport.send_turn(message.to_wire())
        self._listen({"type": "moved", "sub_game": self.n, "step": message.step})
        kind = win_kind(message.win_claim)
        if kind == "survival":
            self.result = ("survival", "thief")
        elif kind in {"capture", "enclosure"}:
            self.result = ("capture", "police")

    def _process(self, msg: TurnMessage) -> None:
        outcome = self.engine.receive(msg)
        if outcome.i_won:
            self.result = ("capture", "police")
        elif outcome.opponent_won:
            self.result = ("survival", "thief")
        elif outcome.i_am_caught:
            self.transport.send_turn(self.engine.concede().to_wire())
            self.result = ("capture", "police")
        elif self.role == "thief" and self.engine.half.enclosed():
            self.transport.send_turn(self.engine.report_enclosure().to_wire())
            self.result = ("capture", "police")
        else:
            self._take_turn()

    def _finish(self, turn_timeout: float) -> dict[str, Any]:
        outcome, winner = self.result  # type: ignore[misc]
        # A timeout used to skip audit entirely, leaving their reveal in the
        # inbox so the next sub-game waited a full turn_timeout for a move
        # that had already been replaced by that leftover audit.
        wait = min(2.0, turn_timeout) if outcome == "timeout" else turn_timeout
        audit = self._exchange_audit(outcome, wait)
        while self.transport.poll_turn(0.0) is not None:
            pass
        steps = self.engine.threshold if outcome == "survival" else self.engine.step
        return {
            "sub_game_number": self.n,
            "role": self.role,
            "result": outcome,
            "winner": winner,
            "steps": steps,
            "records": self.engine.records,
            "audit": audit,
            "started_at": self.started_at,
            "duration_seconds": time.monotonic() - self._t0,
            "tokens_total": 0,
        }
