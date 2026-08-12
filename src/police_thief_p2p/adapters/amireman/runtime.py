"""One sub-game over the pushed-turn amireman wire."""

from __future__ import annotations

import time
from typing import Any, Callable

from police_thief_p2p.adapters.amireman.canonical import audit_records
from police_thief_p2p.adapters.amireman.delivery import EquivocationError, Inbox, ProtocolViolationError
from police_thief_p2p.adapters.amireman.engine import IncomingOutcome, SubEngine, _now_iso
from police_thief_p2p.adapters.amireman.wire import AuditPayload, TurnMessage


class SubGameRuntime:
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
        listener: Callable[[dict], None] | None = None,
    ) -> None:
        self.engine = SubEngine(role, terms, group, github_commit, sub_game_number, seed)
        self.transport = transport
        self.inbox = Inbox(window=4)
        self.role = role
        self.n = sub_game_number
        self._listen = listener or (lambda _event: None)
        self.result: tuple[str, str] | None = None
        self.started_at = _now_iso()
        self._t0 = time.monotonic()

    def run(self, turn_timeout: float = 180.0, poll: float = 0.3) -> dict[str, Any]:
        if self.role == "thief":
            self._take_turn()
        deadline = time.monotonic() + turn_timeout
        while self.result is None:
            incoming = self.transport.poll_turn(poll)
            if incoming is None:
                if time.monotonic() > deadline:
                    self.result = ("timeout", self.role)
                continue
            deadline = time.monotonic() + turn_timeout
            try:
                ready = self.inbox.offer(incoming)
            except (EquivocationError, ProtocolViolationError):
                self.result = ("technical_loss", "-")
                break
            for raw in ready:
                self._process(TurnMessage.from_wire(raw))
                if self.result is not None:
                    break
        return self._finish(turn_timeout)

    def _take_turn(self) -> None:
        message = self.engine.take_turn()
        self.transport.send_turn(message.to_wire())
        self._listen({"type": "moved", "sub_game": self.n, "step": message.step})
        if message.win_claim:
            self.result = ("survival", "thief")

    def _process(self, msg: TurnMessage) -> None:
        outcome: IncomingOutcome = self.engine.receive(msg)
        if outcome.i_won:
            self.result = ("capture", "police")
        elif outcome.opponent_won:
            self.result = ("survival", "thief")
        elif outcome.i_am_caught:
            self.transport.send_turn(self.engine.concede().to_wire())
            self.result = ("capture", "police")
        else:
            self._take_turn()

    def _verify_theirs(self, records: list) -> dict[str, Any]:
        res = audit_records(records)
        failed = list(res["failed_steps"])
        by_step = {int(r["payload"].get("step", -1)): r for r in records}
        for step, commit in self.inbox.played.items():
            rec = by_step.get(int(step))
            if rec is None or rec.get("commit") != commit:
                failed.append(int(step))
        passed = not failed
        return {
            "passed": passed,
            "log_verified": passed,
            "tampered": not passed,
            "verified_steps": max(0, len(records) - len(set(failed))),
            "failed_steps": sorted(set(failed)),
            "skipped": False,
        }

    def _exchange_audit(self, outcome: str, turn_timeout: float) -> dict[str, Any]:
        mine = AuditPayload(sender=self.role, records=self.engine.records, result_claim=outcome)
        self.transport.send_audit(mine.to_wire())
        theirs = self.transport.poll_audit(turn_timeout)
        if theirs is None:
            return {
                "passed": False,
                "log_verified": False,
                "tampered": False,
                "verified_steps": 0,
                "failed_steps": [],
                "skipped": True,
                "local_result_claim": outcome,
                "peer_result_claim": None,
                "result_agreed": False,
            }
        peer = AuditPayload.from_wire(theirs)
        audit = self._verify_theirs(peer.records)
        audit["local_result_claim"] = outcome
        audit["peer_result_claim"] = peer.result_claim
        audit["result_agreed"] = peer.result_claim == outcome
        return audit

    def _finish(self, turn_timeout: float) -> dict[str, Any]:
        outcome, winner = self.result  # type: ignore[misc]
        audit = (
            {
                "passed": False,
                "log_verified": False,
                "tampered": False,
                "verified_steps": 0,
                "failed_steps": [],
                "skipped": True,
                "local_result_claim": outcome,
                "peer_result_claim": None,
                "result_agreed": False,
            }
            if outcome == "timeout"
            else self._exchange_audit(outcome, turn_timeout)
        )
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
