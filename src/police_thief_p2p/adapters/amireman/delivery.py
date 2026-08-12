"""Exactly-once ordered delivery over an at-least-once push transport."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class EquivocationError(Exception):
    """Second different commit for a step already played."""


class ProtocolViolationError(Exception):
    """Arrival past the reorder window."""


def delivery_decision(state: dict[str, Any], arrival: dict[str, Any]) -> str:
    """Return absorb | discard | equivocation | apply | buffer | violation."""
    played, step, commit = state["played"], arrival["step"], arrival["commit"]
    if str(step) in played or step in played:
        seen = played.get(str(step), played.get(step))
        return "absorb" if seen == commit else "equivocation"
    if step == state["next"]:
        return "apply"
    if step < state["next"]:
        return "discard"
    if step - state["next"] <= state["window"]:
        return "buffer"
    return "violation"


@dataclass
class Inbox:
    """Ordered, exactly-once processing keyed on commit."""

    window: int = 4
    next_step: int = 1
    played: dict = field(default_factory=dict)
    buffered: dict = field(default_factory=dict)
    absorbed: int = 0

    def _state(self) -> dict[str, Any]:
        return {
            "played": {str(key): value for key, value in self.played.items()},
            "window": self.window,
            "next": self.next_step,
        }

    def offer(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        """Take one inbound message; return ready messages in step order."""
        arrival = {"step": int(message["step"]), "commit": message["commit"]}
        decision = delivery_decision(self._state(), arrival)
        if decision in ("absorb", "discard"):
            self.absorbed += 1
            return []
        if decision == "equivocation":
            raise EquivocationError(f"equivocation at step {arrival['step']}")
        if decision == "violation":
            raise ProtocolViolationError(f"step {arrival['step']} past reorder window")
        if decision == "buffer":
            self.buffered[arrival["step"]] = message
            return []
        ready = [message]
        self.played[arrival["step"]] = arrival["commit"]
        self.next_step = arrival["step"] + 1
        while self.next_step in self.buffered:
            nxt = self.buffered.pop(self.next_step)
            self.played[self.next_step] = nxt["commit"]
            ready.append(nxt)
            self.next_step += 1
        return ready
