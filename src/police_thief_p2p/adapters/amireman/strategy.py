"""Compatibility wrapper for stateful pursuit/evasion strategy."""

from __future__ import annotations

import random
from typing import Any

from police_thief_p2p.adapters.amireman.police_policy import choose_police
from police_thief_p2p.adapters.amireman.strategy_grid import Cell, apply_move, legal_moves


def choose_move(
    *,
    role: str,
    pos: Cell,
    barriers: set[Cell],
    size: int,
    scent: dict[Cell, float],
    known_opp: Cell | None,
    rng: random.Random,
    barriers_used: int,
    barriers_max: int,
    last_target: Cell | None = None,
    step: int = 0,
    max_steps: int = 35,
    opp_start: Cell | None = None,
    sub_game: int = 1,
    last_move: str | None = None,
) -> tuple[str, list[int] | None]:
    """Preserve the original stateless entry point during session migration."""
    del rng
    if role == "thief":
        from police_thief_p2p.adapters.amireman.thief_policy import choose_thief

        return (
            choose_thief(
                pos=pos,
                barriers=barriers,
                size=size,
                scent=scent,
                known_opp=known_opp,
                last_target=last_target,
                opp_start=opp_start,
                last_move=last_move,
                step=step,
                barriers_used=barriers_used,
                barriers_max=barriers_max,
                sub_game=sub_game,
            ),
            None,
        )
    return choose_police(
        pos,
        barriers,
        size,
        scent,
        known_opp,
        last_target,
        opp_start,
        barriers_used,
        barriers_max,
        step,
        max_steps,
    )


def build_payload(
    step: int,
    role: str,
    state: str,
    move: str,
    hint: str,
    *,
    barrier: list[Any] | None = None,
    capture_claim: list[Any] | None = None,
    claim_response: dict[str, Any] | None = None,
    sub_game: int | None = None,
    intent: str = "truth",
) -> dict[str, Any]:
    """Build the sealed audit payload using official field conventions."""
    if intent not in {"truth", "lie"}:
        raise ValueError("intent must be truth or lie")
    payload: dict[str, Any] = {
        "step": step,
        "role": role,
        "state": state,
        "move": move if move == "STAY" or move.startswith("MOVE:") else f"MOVE:{move}",
        "intent": intent,
        "hint": hint,
    }
    if sub_game is not None:
        payload["sub_game"] = payload["sub_game_number"] = int(sub_game)
    if barrier is not None:
        payload["barrier_placed"] = list(barrier)
    if capture_claim is not None:
        payload["capture_claim"] = list(capture_claim)
    if claim_response is not None:
        payload["claim_response"] = dict(claim_response)
    return payload


__all__ = ["apply_move", "build_payload", "choose_move", "legal_moves"]
