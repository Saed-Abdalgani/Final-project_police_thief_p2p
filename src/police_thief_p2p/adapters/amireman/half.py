"""One peer's sealed gameplay half for the amireman wire."""

from __future__ import annotations

import random
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import seal
from police_thief_p2p.adapters.amireman.capture import evaluate_thief_caught
from police_thief_p2p.adapters.amireman.scent import grid_in, grid_out, step_update
from police_thief_p2p.adapters.amireman.strategy import apply_move, build_payload, choose_move


class PeerHalf:
    """Computes own moves, emits public turn fields, seals audit records."""

    def __init__(self, role: str, terms: dict[str, Any], group: str, commit: str, sub_game: int, seed: int) -> None:
        self.role = role
        self.size = int(terms["board_size"])
        self.rho = float(terms["decay_per_step"])
        self.max_barriers = int(terms["barriers_max"])
        self.threshold = int(terms["max_steps"])
        start = terms["cop_start"] if role == "police" else terms["thief_start"]
        self.pos = (int(start[0]), int(start[1]))
        self.barriers: set[tuple[int, int]] = set()
        self.barriers_used = 0
        self.own_scent = step_update({}, self.pos, self.size, self.rho)
        self.recv_scent: dict[tuple[int, int], float] = {}
        self.known_opp: tuple[int, int] | None = None
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
        )
        if barrier is not None:
            cell = (int(barrier[0]), int(barrier[1]))
            self.barriers.add(cell)
            self.barriers_used += 1
        else:
            self.pos = apply_move(self.pos, move)
        self.own_scent = step_update(self.own_scent, self.pos, self.size, self.rho)
        claim = list(self.pos) if self.role == "police" else None
        hint = "Haifa streets clear" if self.role == "police" else "moving carefully"
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
        )
        sealed = seal(payload)
        self.records.append({"payload": payload, **sealed})
        return {
            "step": self.step,
            "sender": self.role,
            "commit": sealed["commit"],
            "hint": hint,
            "scent": grid_out(self.own_scent),
            "claim": claim,
            "barrier_placed": barrier,
        }

    def hold(self, claim_response: dict | None = None) -> dict[str, Any]:
        self.step += 1
        self.own_scent = step_update(self.own_scent, self.pos, self.size, self.rho)
        payload = build_payload(
            self.step,
            self.role,
            f"grid={self.size};self={list(self.pos)}",
            "STAY",
            "",
            claim_response=claim_response,
        )
        sealed = seal(payload)
        self.records.append({"payload": payload, **sealed})
        return {
            "step": self.step,
            "sender": self.role,
            "commit": sealed["commit"],
            "hint": "",
            "scent": grid_out(self.own_scent),
            "claim": None,
            "barrier_placed": None,
        }

    def receive(self, msg: dict[str, Any]) -> bool:
        """Fold inbound public fields; return True if this Thief is caught."""
        self.recv_scent = grid_in(msg.get("scent") or msg.get("smell_grid"))
        claim = msg.get("claim") if "claim" in msg else msg.get("capture_claim")
        barrier = msg.get("barrier_placed")
        if self.role == "police" and claim is None and isinstance(msg.get("capture_claim"), list):
            claim = msg.get("capture_claim")
        if isinstance(claim, list) and len(claim) == 2 and self.role == "thief":
            # Cop always claims own cell — that is where we believe the Cop is.
            self.known_opp = (int(claim[0]), int(claim[1]))
        if self.role == "police" and isinstance(msg.get("smell_grid"), dict):
            peak = max(self.recv_scent.items(), key=lambda i: i[1], default=(None, 0))[0]
            if peak is not None:
                self.known_opp = peak
        if self.role != "thief":
            return False
        if isinstance(barrier, list) and len(barrier) == 2:
            cell = (int(barrier[0]), int(barrier[1]))
            if 0 <= cell[0] < self.size and 0 <= cell[1] < self.size and cell not in self.barriers:
                self.barriers.add(cell)
        return evaluate_thief_caught(
            thief=self.pos,
            claim=claim,
            barrier=barrier,
            barriers=self.barriers,
            size=self.size,
        )


def _step0(group: str, sub_game: int, commit: str) -> dict[str, Any]:
    payload = {
        "step": 0,
        "type": "system_spec",
        "group_name": group,
        "sub_game_number": sub_game,
        "github_commit": commit,
        "code_version": "amireman-compat-0.1",
    }
    sealed = seal(payload)
    return {"payload": payload, **sealed}
