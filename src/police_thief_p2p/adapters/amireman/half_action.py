"""Outbound action construction for an amireman peer half."""

from __future__ import annotations

import random
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import seal
from police_thief_p2p.adapters.amireman.scent import decay_only, grid_out, step_update
from police_thief_p2p.adapters.amireman.strategy import apply_move, build_payload, choose_move


class PeerHalfActionMixin:
    """Choose, apply, and seal legal compatibility actions."""

    role: str
    pos: tuple[int, int]
    barriers: set[tuple[int, int]]
    size: int
    recv_scent: dict[tuple[int, int], float]
    known_opp: tuple[int, int] | None
    rng: random.Random
    barriers_used: int
    max_barriers: int
    last_target: tuple[int, int] | None
    step: int
    threshold: int
    opp_start: tuple[int, int]
    sub_game: int
    last_move: str | None
    setting: str
    scent_model: str
    rho: float
    own_scent: dict[tuple[int, int], float]
    strategy_session: Any
    records: list[dict[str, Any]]

    def act(self, claim_response: dict[str, Any] | None = None) -> dict[str, Any]:
        """Choose, apply, and seal one strategy action."""
        self.step += 1
        if self.strategy_session is None:
            move, barrier = choose_move(
                role=self.role,
                pos=self.pos,
                barriers=self.barriers,
                size=self.size,
                scent=self.recv_scent,
                known_opp=self.known_opp,
                rng=self.rng,
                barriers_used=self.barriers_used,
                barriers_max=self.max_barriers,
                last_target=self.last_target,
                step=self.step,
                max_steps=self.threshold,
                opp_start=self.opp_start,
                sub_game=self.sub_game,
                last_move=self.last_move,
            )
            hint = f"{self.setting} streets clear" if self.role == "police" else "moving carefully"
            intent = "truth"
        else:
            decision = self.strategy_session.decide(
                position=self.pos,
                barriers=set(self.barriers),
                barriers_used=self.barriers_used,
                step=self.step,
            )
            move = decision.move
            barrier = list(decision.barrier) if decision.barrier is not None else None
            hint, intent = decision.hint, decision.intent
        self.last_move = move
        if barrier is not None:
            cell = (int(barrier[0]), int(barrier[1]))
            self.barriers.add(cell)
            self.barriers_used += 1
        else:
            self.pos = apply_move(self.pos, move)
        served = decay_only(self.own_scent, self.rho, self.scent_model)
        self.own_scent = step_update(
            self.own_scent, self.pos, self.size, self.rho, self.scent_model
        )
        claim = list(self.pos) if self.role == "police" else None
        wire_move = "STAY" if move == "STAY" or barrier is not None else move
        payload = build_payload(
            self.step,
            self.role,
            f"grid={self.size};self={list(self.pos)}",
            wire_move,
            hint,
            barrier=barrier,
            capture_claim=claim,
            claim_response=claim_response,
            sub_game=self.sub_game,
            intent=intent,
        )
        sealed = seal(payload)
        self.records.append({"payload": payload, **sealed})
        return {
            "step": self.step,
            "sender": self.role,
            "commit": sealed["commit"],
            "hint": hint,
            "scent": grid_out(served),
            "claim": claim,
            "barrier_placed": barrier,
        }

    def hold(self, claim_response: dict[str, Any] | None = None) -> dict[str, Any]:
        """Seal a protocol-required terminal STAY response."""
        self.step += 1
        served = decay_only(self.own_scent, self.rho, self.scent_model)
        self.own_scent = step_update(
            self.own_scent, self.pos, self.size, self.rho, self.scent_model
        )
        payload = build_payload(
            self.step,
            self.role,
            f"grid={self.size};self={list(self.pos)}",
            "STAY",
            "",
            claim_response=claim_response,
            sub_game=self.sub_game,
        )
        sealed = seal(payload)
        self.records.append({"payload": payload, **sealed})
        return {
            "step": self.step,
            "sender": self.role,
            "commit": sealed["commit"],
            "hint": "",
            "scent": grid_out(served),
            "claim": None,
            "barrier_placed": None,
        }
