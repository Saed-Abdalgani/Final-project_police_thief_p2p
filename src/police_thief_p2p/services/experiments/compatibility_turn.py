"""One faithful pre-emission turn for the compatibility recovery arena."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from police_thief_p2p.services.experiments.compatibility_grid import (
    Cell,
    legal_action,
    move,
    reachable,
)
from police_thief_p2p.services.experiments.compatibility_opponents import (
    OpponentState,
    opponent_decision,
    opponent_hint,
)
from police_thief_p2p.services.strategy.compatibility import CompatibilityStrategySession
from police_thief_p2p.services.strategy.compatibility_models import CompatibilityTurnObservation
from police_thief_p2p.services.strategy.compatibility_scent import decay_only, step_update


@dataclass(slots=True)
class ArenaState:
    """Mutable referee truth used only inside the offline arena."""

    cop: Cell
    thief: Cell
    barriers: set[Cell]
    scent: dict[str, dict[Cell, float]]


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Capture, legality, barrier, and graph-cut effects of one action."""

    capture: bool
    illegal: int
    barrier: Cell | None
    region_reduction: int


def execute_turn(
    arena: Any,
    actor: str,
    candidate_role: str,
    step: int,
    state: ArenaState,
    session: CompatibilityStrategySession,
    opponent: OpponentState,
    records: list[dict[str, Any]],
    latencies: list[float],
) -> ActionResult:
    """Execute one actor turn and deliver only lawful public observations."""
    position = state.cop if actor == "police" else state.thief
    before_region = reachable(state.thief, state.barriers, arena.size)
    if actor == candidate_role:
        decision = session.decide(
            position=position,
            barriers=set(state.barriers),
            step=step,
        )
        token, barrier = decision.move, decision.barrier
        hint, intent = decision.hint, decision.intent
        latencies.append(decision.metrics.latency_ms)
    else:
        token, barrier = opponent_decision(
            opponent,
            state.cop,
            state.thief,
            state.barriers,
            step,
            arena.size,
            arena.max_barriers,
        )
        hint, intent = opponent_hint(position, arena.size), "truth"

    illegal = int(not legal_action(position, token, barrier, state.barriers, arena.size, actor))
    if illegal:
        token, barrier = "STAY", None
    if barrier is not None:
        state.barriers.add(barrier)
        capture = barrier == state.thief
        reduction = before_region - reachable(state.thief, state.barriers, arena.size)
        if actor != candidate_role:
            opponent.barriers_used += 1
    else:
        new_position = move(position, token)
        if actor == "police":
            state.cop = new_position
        else:
            state.thief = new_position
        capture, reduction = state.cop == state.thief, 0

    served = decay_only(state.scent[actor], arena.rho, arena.scent_model)
    actor_position = state.cop if actor == "police" else state.thief
    state.scent[actor] = step_update(
        state.scent[actor], actor_position, arena.size, arena.rho, arena.scent_model
    )
    record: dict[str, Any] = {
        "payload": {
            "step": step,
            "role": actor,
            "state": f"grid={arena.size};self={list(actor_position)}",
            "move": token,
            "hint": hint,
            "intent": intent,
            **({"barrier_placed": list(barrier)} if barrier is not None else {}),
        },
        "barrier_placed": barrier,
    }
    if actor != candidate_role:
        records.append(record)
        session.observe(
            CompatibilityTurnObservation(
                step,
                served,
                hint,
                state.cop if actor == "police" else None,
                barrier,
            )
        )
        opponent.history.append(actor_position)
    else:
        opponent.target_history.append(actor_position)
    return ActionResult(capture, illegal, barrier, reduction)
