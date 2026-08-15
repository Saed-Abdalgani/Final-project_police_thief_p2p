"""Pursuit/evasion policy for the amireman peer."""

from __future__ import annotations

import random

from police_thief_p2p.adapters.amireman.strategy import apply_move, choose_move


def _police(**kwargs):
    defaults = dict(
        role="police",
        pos=(0, 0),
        barriers=set(),
        size=7,
        scent={},
        known_opp=None,
        rng=random.Random(0),
        barriers_used=0,
        barriers_max=14,
        last_target=None,
        step=1,
        max_steps=35,
        opp_start=(3, 3),
    )
    defaults.update(kwargs)
    return choose_move(**defaults)


def _thief(**kwargs):
    defaults = dict(
        role="thief",
        pos=(3, 3),
        barriers=set(),
        size=7,
        scent={},
        known_opp=None,
        rng=random.Random(0),
        barriers_used=0,
        barriers_max=14,
        opp_start=(0, 0),
        sub_game=2,
    )
    defaults.update(kwargs)
    return choose_move(**defaults)


def test_police_steps_onto_adjacent_believed_thief() -> None:
    move, barrier = _police(pos=(2, 3), known_opp=(3, 3))
    assert barrier is None
    assert apply_move((2, 3), move) == (3, 3)


def test_police_does_not_drop_spawn_wall() -> None:
    for step in range(1, 5):
        move, barrier = _police(pos=(0, 0), known_opp=(3, 3), step=step)
        assert barrier is None
        assert move in {"S", "E"}


def test_police_paths_around_a_wall() -> None:
    barriers = {(1, 0), (1, 1)}
    move, barrier = _police(pos=(0, 0), known_opp=(2, 0), barriers=barriers)
    assert barrier is None
    assert move == "E"
    assert apply_move((0, 0), move) not in barriers


def test_thief_max_manhattan_from_known_cop() -> None:
    move, barrier = _thief(pos=(3, 3), known_opp=(0, 0))
    assert barrier is None
    nxt = apply_move((3, 3), move)
    assert abs(nxt[0] - 0) + abs(nxt[1] - 0) >= 6


def test_thief_holds_far_corner_when_cop_closes() -> None:
    move, barrier = _thief(pos=(6, 6), known_opp=(4, 4), sub_game=2)
    assert barrier is None
    assert move == "STAY"


def test_thief_game_six_camps_south_west_not_south_east() -> None:
    pos = (3, 3)
    for _ in range(12):
        move, barrier = _thief(pos=pos, known_opp=(0, 0), sub_game=6)
        assert barrier is None
        pos = apply_move(pos, move)
    assert pos == (6, 0)
    move, barrier = _thief(pos=(6, 0), known_opp=(4, 0), sub_game=6)
    assert move == "STAY"


def test_thief_games_two_and_four_still_sit_south_east() -> None:
    for sub_game in (2, 4):
        pos = (3, 3)
        for _ in range(12):
            move, _barrier = _thief(pos=pos, known_opp=(0, 0), sub_game=sub_game)
            pos = apply_move(pos, move)
        assert pos == (6, 6)


def test_thief_opening_does_not_walk_toward_cop_start() -> None:
    move, barrier = _thief(pos=(3, 3), known_opp=None, opp_start=(0, 0), rng=random.Random(0))
    assert barrier is None
    nxt = apply_move((3, 3), move)
    assert abs(nxt[0]) + abs(nxt[1]) >= 6


def test_police_captures_naive_fleer_from_standard_starts() -> None:
    from police_thief_p2p.adapters.amireman.strategy import legal_moves

    cop, thief = (0, 0), (3, 3)
    barriers: set[tuple[int, int]] = set()
    used = 0
    last = None
    captured = False
    rng = random.Random(0)
    for step in range(1, 36):
        seen = thief
        moves = legal_moves(thief, barriers, 7)
        t_move = max(moves, key=lambda move: abs(apply_move(thief, move)[0] - cop[0]) + abs(apply_move(thief, move)[1] - cop[1]))
        thief = apply_move(thief, t_move)
        p_move, barrier = _police(
            pos=cop,
            known_opp=seen,
            last_target=last,
            barriers=barriers,
            barriers_used=used,
            step=step,
            rng=rng,
        )
        last = seen
        if barrier is not None:
            cell = (int(barrier[0]), int(barrier[1]))
            barriers.add(cell)
            used += 1
            if cell == thief:
                captured = True
                break
        else:
            cop = apply_move(cop, p_move)
        if cop == thief:
            captured = True
            break
    assert captured
