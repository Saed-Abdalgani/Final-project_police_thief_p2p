"""One sub-game over the pushed-turn amireman wire."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import audit_records, canonical, commit_of
from police_thief_p2p.adapters.amireman.delivery import (
    EquivocationError,
    Inbox,
    ProtocolViolationError,
)
from police_thief_p2p.adapters.amireman.engine import IncomingOutcome, SubEngine, _now_iso
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.wire import AuditPayload, TurnMessage, is_series_consensus


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
        scent_model: str = MULTIPLICATIVE_KERNEL_V1,
    ) -> None:
        self.engine = SubEngine(
            role, terms, group, github_commit, sub_game_number, seed, scent_model=scent_model
        )
        self.transport = transport
        self.inbox = Inbox(window=4)
        self.role = role
        self.n = sub_game_number
        self._listen = listener or (lambda _event: None)
        self.result: tuple[str, str] | None = None
        self.started_at = _now_iso()
        self._t0 = time.monotonic()
        self.deferred_consensus: dict[str, Any] | None = None

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

    def _records_for_this_game(self, records: list) -> list:
        """Keep this sub-game's tagged records plus records that omit a tag.

        Reference-v3 / SMNGRP05 only stamp ``sub_game_number`` on step 0. Step
        payloads have none. ``tagged or untagged`` then kept step 0 and dropped
        every live step, so an honest log looked fully tampered.
        """
        tagged = []
        untagged = []
        for rec in records:
            payload = rec.get("payload") if isinstance(rec, dict) else None
            if not isinstance(payload, dict):
                untagged.append(rec)
                continue
            declared = payload.get("sub_game_number", payload.get("sub_game"))
            if declared is None:
                untagged.append(rec)
            elif int(declared) == self.n:
                tagged.append(rec)
        return tagged + untagged

    def _verify_theirs(self, records: list) -> dict[str, Any]:
        scoped = self._records_for_this_game(records)
        res = audit_records(scoped)
        failed = list(res["failed_steps"])
        by_step = {
            int(r["payload"].get("step", -1)): r
            for r in scoped
            if isinstance(r, dict) and isinstance(r.get("payload"), dict)
        }
        for step, commit in self.inbox.played.items():
            rec = by_step.get(int(step))
            if rec is None or rec.get("commit") != commit:
                failed.append(int(step))
        unique = sorted(set(failed))
        passed = not unique
        return {
            "passed": passed,
            "log_verified": passed,
            "tampered": not passed,
            "verified_steps": max(0, len(scoped) - len(unique)),
            "failed_steps": unique,
            "skipped": False,
            "example": None if passed else _worked_example(by_step, unique),
        }

    def _poll_subgame_audit(self, turn_timeout: float) -> dict[str, Any] | None:
        deadline = time.monotonic() + turn_timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            theirs = self.transport.poll_audit(remaining)
            if theirs is None:
                continue
            if is_series_consensus(theirs):
                self.deferred_consensus = theirs
                continue
            peer = AuditPayload.from_wire(theirs)
            declared = peer.sub_game_number if peer.sub_game_number is not None else peer.sub_game
            if declared is not None and int(declared) != self.n:
                continue
            return theirs

    def _exchange_audit(self, outcome: str, turn_timeout: float) -> dict[str, Any]:
        mine = AuditPayload(
            sender=self.role,
            records=self.engine.records,
            result_claim=outcome,
            sub_game=self.n,
            sub_game_number=self.n,
        )
        self.transport.send_audit(mine.to_wire())
        theirs = self._poll_subgame_audit(turn_timeout)
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
                "example": None,
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
                "example": None,
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


def _worked_example(by_step: dict[int, dict], failed: list[int]) -> dict[str, Any] | None:
    """One failed record as received, plus the digest we computed over it."""
    for step in failed:
        rec = by_step.get(int(step))
        if not isinstance(rec, dict) or not isinstance(rec.get("payload"), dict):
            continue
        payload = rec["payload"]
        nonce = str(rec.get("nonce", ""))
        declared = str(rec.get("commit", ""))
        computed = commit_of(payload, nonce) if nonce else ""
        return {
            "step": int(step),
            "payload": payload,
            "nonce": nonce,
            "commit": declared,
            "computed": computed,
            "preimage": f"{canonical(payload)}|{nonce}",
            "scheme": (
                'sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, '
                'separators=(",", ":")) + "|" + nonce)'
            ),
        }
    return None
