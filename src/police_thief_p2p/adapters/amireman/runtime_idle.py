"""Idle-wait helpers. Turns are not resent across or within a sub-game."""

from __future__ import annotations

from typing import Any


def nudge_interval(turn_timeout: float) -> float:
    """Use a short nudge in tests; 10s on a live 180s clock."""
    if turn_timeout >= 60.0:
        return 10.0
    return max(0.05, turn_timeout / 3.0)


def announce_wait(runtime: Any, elapsed: int) -> None:
    """Log the wait only. No receive_turn retry until both sides key turns by sub-game."""
    runtime._listen(
        {
            "type": "waiting",
            "sub_game": runtime.n,
            "role": runtime.role,
            "step": runtime.engine.step,
            "seconds": elapsed,
        }
    )
