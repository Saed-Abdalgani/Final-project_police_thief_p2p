"""Mutual-audit support for an amireman sub-game runtime."""

from __future__ import annotations

import time
from typing import Any, cast

from police_thief_p2p.adapters.amireman.canonical import audit_records
from police_thief_p2p.adapters.amireman.delivery import Inbox
from police_thief_p2p.adapters.amireman.runtime_audit_verify import worked_example
from police_thief_p2p.adapters.amireman.wire import AuditPayload, is_series_consensus


class SubGameAuditMixin:
    """Exchange and validate per-game audit payloads."""

    transport: Any
    inbox: Inbox
    engine: Any
    role: str
    n: int
    result: tuple[str, str] | None
    deferred_consensus: dict[str, Any] | None
    _peer_audit: dict[str, Any] | None
    peer_records: list[dict[str, Any]]

    def _declared_subgame(self, peer: AuditPayload) -> int | None:
        declared = peer.sub_game_number if peer.sub_game_number is not None else peer.sub_game
        return int(declared) if declared is not None else None

    def _apply_peer_audit(self, peer: AuditPayload) -> None:
        claim = (peer.result_claim or "").strip().lower()
        if claim in {"capture", "enclosure"}:
            self.result = ("capture", "police")
        elif claim == "survival":
            self.result = ("survival", "thief")
        elif claim == "technical_loss":
            self.result = ("technical_loss", "-")
        elif claim == "timeout":
            self.result = ("timeout", self.role)
        elif self.engine.ceiling_reached():
            self.result = ("survival", "thief")
        else:
            self.result = ("capture", "police")

    def _absorb_audits(self) -> None:
        """Accept an audit when the opponent has already closed this game."""
        while True:
            theirs = self.transport.poll_audit(0.0)
            if theirs is None:
                return
            if is_series_consensus(theirs):
                self.deferred_consensus = theirs
                continue
            peer = AuditPayload.from_wire(theirs)
            declared = self._declared_subgame(peer)
            if declared != self.n:
                continue
            self._peer_audit = theirs
            if self.result is None:
                self._apply_peer_audit(peer)
            return

    def _records_for_this_game(self, records: list[Any]) -> list[Any]:
        """Keep this game's tagged records and untagged compatibility records."""
        tagged, untagged = [], []
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

    def _verify_theirs(self, records: list[Any]) -> dict[str, Any]:
        scoped = self._records_for_this_game(records)
        failed = list(audit_records(scoped)["failed_steps"])
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
            "example": None if passed else worked_example(by_step, unique),
        }

    def _poll_subgame_audit(self, turn_timeout: float) -> dict[str, Any] | None:
        if self._peer_audit is not None:
            theirs, self._peer_audit = self._peer_audit, None
            return theirs
        deadline = time.monotonic() + turn_timeout
        while time.monotonic() < deadline:
            theirs = self.transport.poll_audit(deadline - time.monotonic())
            if theirs is None:
                return None
            if is_series_consensus(theirs):
                self.deferred_consensus = theirs
                continue
            peer = AuditPayload.from_wire(theirs)
            declared = self._declared_subgame(peer)
            if declared is None or declared == self.n:
                return cast(dict[str, Any], theirs)
        return None

    def _exchange_audit(self, outcome: str, turn_timeout: float) -> dict[str, Any]:
        mine = AuditPayload(
            sender=self.role,
            records=[
                rec
                for rec in self.engine.records
                if int((rec.get("payload") or {}).get("step", 0)) >= 1
            ],
            result_claim=outcome,
            sub_game=self.n,
            sub_game_number=self.n,
        )
        self.transport.send_audit(mine.to_wire())
        theirs = self._poll_subgame_audit(turn_timeout)
        if theirs is None:
            return _skipped_audit(outcome)
        peer = AuditPayload.from_wire(theirs)
        self.peer_records = self._records_for_this_game(peer.records)
        audit = self._verify_theirs(peer.records)
        audit.update(
            local_result_claim=outcome,
            peer_result_claim=peer.result_claim,
            result_agreed=peer.result_claim == outcome,
        )
        return audit


def _skipped_audit(outcome: str) -> dict[str, Any]:
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
