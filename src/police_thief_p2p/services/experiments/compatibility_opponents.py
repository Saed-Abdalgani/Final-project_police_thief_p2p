"""Clean-room behavioral sparring profiles for compatibility training."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from police_thief_p2p.services.experiments.compatibility_grid import (
    Cell,
    distance,
    legal_moves,
    move,
    neighbors,
    passable,
    reachable,
)


@dataclass(slots=True)
class OpponentState:
    """Mutable public-history state for one clean-room sparring policy."""

    family: str
    role: str
    rng: random.Random
    history: list[Cell] = field(default_factory=list)
    target_history: list[Cell] = field(default_factory=list)
    barriers_used: int = 0


def opponent_decision(
    opponent: OpponentState,
    cop: Cell,
    thief: Cell,
    barriers: set[Cell],
    step: int,
    size: int,
    max_barriers: int,
) -> tuple[str, Cell | None]:
    """Choose one action from the named clean-room behavior family."""
    family = opponent.family
    if family == "policy-switch":
        family = "boundary" if step <= 12 else "risk-juke"
    elif family == "g005-unknown":
        family = ("random", "cycle", "anti-intercept")[opponent.rng.randrange(3)]
    if opponent.role == "thief":
        return thief_decision(family, opponent, cop, thief, barriers, step, size), None
    return police_decision(family, opponent, cop, thief, barriers, size, max_barriers)


def thief_decision(
    family: str,
    opponent: OpponentState,
    cop: Cell,
    thief: Cell,
    barriers: set[Cell],
    step: int,
    size: int,
) -> str:
    """Choose a deterministic or seeded mixed evasion action."""
    moves = legal_moves(thief, barriers, size)
    if family == "random":
        return opponent.rng.choice(moves)
    if family == "cycle":
        preferred = ("N", "E", "S", "W")[(step - 1) % 4]
        if preferred in moves:
            return preferred
    scored: list[tuple[tuple[float, ...], str]] = []
    for token in moves:
        candidate = move(thief, token)
        gap = distance(candidate, cop, barriers, size)
        degree = len(neighbors(candidate, barriers, size))
        region = reachable(candidate, barriers, size)
        boundary = int(candidate[0] in {0, size - 1}) + int(candidate[1] in {0, size - 1})
        revisit = opponent.history.count(candidate)
        straight = int(
            len(opponent.history) >= 2
            and (candidate[0] - thief[0], candidate[1] - thief[1])
            == (
                opponent.history[-1][0] - opponent.history[-2][0],
                opponent.history[-1][1] - opponent.history[-2][1],
            )
        )
        score: tuple[float | int | bool, ...]
        if family in {"smngrp05", "open-space"}:
            score = (region, degree, gap, -boundary, -revisit)
        elif family in {"ahk-yosi", "risk-juke", "anti-intercept"}:
            score = (gap >= 2, degree, region, gap, -straight, -boundary, -revisit)
        elif family == "boundary":
            score = (boundary, gap, degree, -revisit)
        elif family == "corner-squeeze":
            score = (gap, -degree, boundary, -revisit)
        else:
            score = (gap, degree, region, -boundary, -revisit)
        scored.append((tuple(float(value) for value in score), token))
    return max(scored)[1]


def police_decision(
    family: str,
    opponent: OpponentState,
    cop: Cell,
    thief: Cell,
    barriers: set[Cell],
    size: int,
    max_barriers: int,
) -> tuple[str, Cell | None]:
    """Choose clean-room intercept, squeeze, graph-cut, or random pursuit."""
    target = thief
    if (
        family in {"ahk-yosi", "velocity-intercept", "anti-intercept"}
        and len(opponent.target_history) >= 2
    ):
        previous, current = opponent.target_history[-2:]
        predicted = (target[0] + current[0] - previous[0], target[1] + current[1] - previous[1])
        if passable(predicted, barriers, size):
            target = predicted
    if opponent.barriers_used < max_barriers and family in {
        "smngrp05",
        "corner-squeeze",
        "aggressive-barrier",
    }:
        best: tuple[int, Cell] | None = None
        old_region = reachable(thief, barriers, size)
        for barrier in neighbors(cop, barriers, size):
            updated = barriers | {barrier}
            if barrier == thief:
                return "STAY", barrier
            if reachable(cop, updated, size) >= 4:
                item = (old_region - reachable(thief, updated, size), barrier)
                best = item if best is None or item > best else best
        threshold = 1 if family == "aggressive-barrier" else 2
        if best is not None and best[0] >= threshold:
            return "STAY", best[1]
    moves = legal_moves(cop, barriers, size)
    if family == "random":
        return opponent.rng.choice(moves), None
    token = min(
        moves,
        key=lambda item: (
            distance(move(cop, item), target, barriers, size),
            -len(neighbors(move(cop, item), barriers, size)),
            item,
        ),
    )
    return token, None


def opponent_hint(position: Cell, size: int) -> str:
    """Return one truthful parser-safe coarse-region hint."""
    vertical = "north" if position[0] < size // 2 else "south"
    horizontal = "west" if position[1] < size // 2 else "east"
    return f"Movement remains in the {vertical} {horizontal} district"
