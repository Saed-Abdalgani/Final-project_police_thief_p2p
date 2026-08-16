"""One peer's sealed gameplay half for the amireman wire."""

from __future__ import annotations

import random
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import seal
from police_thief_p2p.adapters.amireman.capture import evaluate_thief_caught, thief_trapped
from police_thief_p2p.adapters.amireman.scent import (
    MULTIPLICATIVE_KERNEL_V1,
    decay_only,
    grid_in,
    grid_out,
    step_update,
)
from police_thief_p2p.adapters.amireman.strategy import apply_move, build_payload, choose_move


class PeerHalf:
    """Computes own moves, emits public turn fields, seals audit records."""

    def __init__(
        self,
        role: str,
        terms: dict[str, Any],
        group: str,
        commit: str,
        sub_game: int,
        seed: int,
        scent_model: str = MULTIPLICATIVE_KERNEL_V1,
    ) -> None:
        self.role = role
        self.size = int(terms["board_size"])
        self.rho = float(terms["decay_per_step"])
        self.max_barriers = int(terms["barriers_max"])
        self.threshold = int(terms["max_steps"])
        start = terms["cop_start"] if role == "police" else terms["thief_start"]
        opp = terms["thief_start"] if role == "police" else terms["cop_start"]
        self.pos = (int(start[0]), int(start[1]))
        self.opp_start = (int(opp[0]), int(opp[1]))
        self.barriers: set[tuple[int, int]] = set()
        self.barriers_used = 0
        self.sub_game = int(sub_game)
        self.setting = str(terms.get("setting", "Haifa"))
        self.scent_model = scent_model
        self.own_scent = step_update({}, self.pos, self.size, self.rho, self.scent_model)
        self.recv_scent: dict[tuple[int, int], float] = {}
        self.known_opp: tuple[int, int] | None = None
        self.last_target: tuple[int, int] | None = None
        self.last_move: str | None = None
        self.step = 0
        self.rng = random.Random(seed + 100 + sub_game)
        self.records: list[dict[str, Any]] = [
            _step0(group, sub_game, commit),
        ]

    def act(self, claim_response: dict | None = None) -> dict[str, Any]:
        self.step += 1
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
        self.last_move = move
        if barrier is not None:
            cell = (int(barrier[0]), int(barrier[1]))
            self.barriers.add(cell)
            self.barriers_used += 1
        else:
            self.pos = apply_move(self.pos, move)
        served = decay_only(self.own_scent, self.rho, self.scent_model)
        self.own_scent = step_update(self.own_scent, self.pos, self.size, self.rho, self.scent_model)
        claim = list(self.pos) if self.role == "police" else None
        hint = f"{self.setting} streets clear" if self.role == "police" else "moving carefully"
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

    def hold(self, claim_response: dict | None = None) -> dict[str, Any]:
        self.step += 1
        served = decay_only(self.own_scent, self.rho, self.scent_model)
        self.own_scent = step_update(self.own_scent, self.pos, self.size, self.rho, self.scent_model)
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

    def receive(self, msg: dict[str, Any]) -> bool:
        """Fold inbound public fields; return True if this Thief is caught."""
        self.recv_scent = grid_in(msg.get("scent") or msg.get("smell_grid"))
        from police_thief_p2p.adapters.amireman.capture import as_cell

        claim = msg.get("claim") if "claim" in msg else msg.get("capture_claim")
        if claim is None:
            claim = msg.get("capture_claim")
        barrier = msg.get("barrier_placed")
        barrier_cell = as_cell(barrier)
        if barrier_cell is not None:
            if (
                0 <= barrier_cell[0] < self.size
                and 0 <= barrier_cell[1] < self.size
                and barrier_cell not in self.barriers
            ):
                self.barriers.add(barrier_cell)
        if self.role == "thief":
            cop = as_cell(claim) or as_cell(msg.get("capture_claim"))
            if cop is not None:
                self.last_target = self.known_opp
                self.known_opp = cop
            elif self.recv_scent:
                peak = max(self.recv_scent.items(), key=lambda item: item[1])[0]
                if self.known_opp is None:
                    self.known_opp = peak
        if self.role == "police" and self.recv_scent:
            peak = max(self.recv_scent.items(), key=lambda item: item[1])[0]
            self.last_target = self.known_opp
            self.known_opp = peak
        if self.role != "thief":
            return False
        return evaluate_thief_caught(
            thief=self.pos,
            claim=claim,
            barrier=barrier,
            barriers=self.barriers,
            size=self.size,
        )

    def enclosed(self) -> bool:
        """True when this Thief has no orthogonal escape (STAY does not count)."""
        return self.role == "thief" and thief_trapped(self.pos, self.barriers, self.size)


def _step0(group: str, sub_game: int, commit: str) -> dict[str, Any]:
    payload = {
        "step": 0,
        "type": "system_spec",
        "group_name": group,
        "sub_game": sub_game,
        "sub_game_number": sub_game,
        "github_commit": commit,
        "code_version": "1.00",
    }
    sealed = seal(payload)
    return {"payload": payload, **sealed}
