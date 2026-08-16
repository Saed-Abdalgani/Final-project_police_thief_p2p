"""One peer's sealed gameplay half for the amireman wire."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from police_thief_p2p.adapters.amireman.canonical import seal
from police_thief_p2p.adapters.amireman.half_action import PeerHalfActionMixin
from police_thief_p2p.adapters.amireman.half_receive import PeerHalfReceiveMixin
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1, step_update

if TYPE_CHECKING:
    from police_thief_p2p.sdk import CompatibilityStrategySession


class PeerHalf(PeerHalfActionMixin, PeerHalfReceiveMixin):
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
        strategy_session: CompatibilityStrategySession | None = None,
    ) -> None:
        """Initialize one role's local public and sealed state."""
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
        self.strategy_session = strategy_session
        self.own_scent = step_update({}, self.pos, self.size, self.rho, self.scent_model)
        self.recv_scent: dict[tuple[int, int], float] = {}
        self.known_opp: tuple[int, int] | None = None
        self.last_target: tuple[int, int] | None = None
        self.last_move: str | None = None
        self.step = 0
        self.rng = random.Random(seed + 100 + sub_game)  # noqa: S311 - deterministic fallback
        self.records: list[dict[str, Any]] = [
            _step0(group, sub_game, commit),
        ]


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
