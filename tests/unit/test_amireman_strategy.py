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


def test_thief_leaves_corner_when_cop_closes() -> None:
    move, barrier = _thief(pos=(6, 6), known_opp=(4, 4), sub_game=2)
    assert barrier is None
    assert move != "STAY"
    nxt = apply_move((6, 6), move)
    assert nxt != (6, 6)


def test_thief_never_camps_a_corner() -> None:
    for sub_game in (2, 4, 6):
        pos = (3, 3)
        last = None
        for step in range(1, 13):
            move, barrier = _thief(
                pos=pos, known_opp=(0, 0), sub_game=sub_game, last_move=last, step=step
            )
            assert barrier is None
            last = move
            pos = apply_move(pos, move)
        assert pos not in {(0, 0), (0, 6), (6, 0), (6, 6)}


def test_thief_opening_does_not_walk_toward_cop_start() -> None:
    move, barrier = _thief(pos=(3, 3), known_opp=None, opp_start=(0, 0), rng=random.Random(0))
    assert barrier is None
    nxt = apply_move((3, 3), move)
    assert abs(nxt[0]) + abs(nxt[1]) >= 6


def test_thief_keeps_two_cell_buffer() -> None:
    move, _barrier = _thief(pos=(3, 3), known_opp=(3, 1), last_target=(3, 0))
    nxt = apply_move((3, 3), move)
    assert nxt != (3, 1)
    assert abs(nxt[0] - 3) + abs(nxt[1] - 1) >= 2


def test_thief_does_not_step_onto_edge_to_buy_distance() -> None:
    move, _barrier = _thief(pos=(5, 5), known_opp=(4, 4), last_target=(3, 3))
    nxt = apply_move((5, 5), move)
    assert nxt[0] not in (0, 6)
    assert nxt[1] not in (0, 6)
    assert abs(nxt[0] - 4) + abs(nxt[1] - 4) >= 2


def test_thief_keeps_buffer_when_cop_stands_on_own_barrier() -> None:
    move, _barrier = _thief(
        pos=(4, 5),
        known_opp=(5, 4),
        last_target=(5, 4),
        last_move="N",
        barriers={(5, 4)},
    )
    nxt = apply_move((4, 5), move)
    assert nxt != (4, 4)
    assert nxt != (5, 5)
    assert abs(nxt[0] - 5) + abs(nxt[1] - 4) >= 2


def test_thief_does_not_flee_into_corner_when_cop_is_close() -> None:
    move, _barrier = _thief(pos=(6, 5), known_opp=(5, 4), last_move="STAY")
    nxt = apply_move((6, 5), move)
    assert nxt != (6, 6)
    assert abs(nxt[0] - 5) + abs(nxt[1] - 4) >= 2


def test_thief_does_not_stay_twice() -> None:
    move, _barrier = _thief(pos=(3, 3), known_opp=(0, 0), last_move="STAY")
    assert move != "STAY"


def _play(*, thief_seen_lag: bool, intercept: bool = False, sub_game: int = 2) -> tuple[bool, int]:
    """Return (captured, last_step). Thief moves first."""
    cop, thief = (0, 0), (3, 3)
    barriers: set[tuple[int, int]] = set()
    used = 0
    last_seen = None
    last_cop = None
    t_last = None
    prev_thief = thief
    trail: list[tuple[int, int]] = [thief]
    for step in range(1, 36):
        t_move, _ = _thief(
            pos=thief,
            known_opp=cop,
            last_target=last_cop,
            last_move=t_last,
            barriers=barriers,
            step=step,
            barriers_used=used,
            sub_game=sub_game,
        )
        t_last = t_move
        thief = apply_move(thief, t_move)
        seen = prev_thief if thief_seen_lag else thief
        if intercept and len(trail) >= 2:
            dr = trail[-1][0] - trail[-2][0]
            dc = trail[-1][1] - trail[-2][1]
            if abs(dr) + abs(dc) == 1:
                cand = (trail[-1][0] + dr, trail[-1][1] + dc)
                if 0 <= cand[0] < 7 and 0 <= cand[1] < 7:
                    seen = cand
        p_move, barrier = _police(
            pos=cop,
            known_opp=seen,
            last_target=last_seen,
            barriers=barriers,
            barriers_used=used,
            step=step,
        )
        last_seen = seen
        last_cop = cop
        prev_thief = thief
        trail.append(thief)
        if barrier is not None:
            cell = (int(barrier[0]), int(barrier[1]))
            barriers.add(cell)
            used += 1
            if cell == thief:
                return True, step
        else:
            cop = apply_move(cop, p_move)
        if cop == thief:
            return True, step
        exits = 0
        for dr, dc in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            nxt = (thief[0] + dr, thief[1] + dc)
            if 0 <= nxt[0] < 7 and 0 <= nxt[1] < 7 and nxt not in barriers:
                exits += 1
        if exits == 0:
            return True, step
    return False, 35


def test_thief_survives_lagged_scent_police() -> None:
    captured, _step = _play(thief_seen_lag=True)
    assert captured is False


def test_thief_survives_velocity_intercept_police() -> None:
    captured, _step = _play(thief_seen_lag=True, intercept=True)
    assert captured is False


def test_thief_survives_intercept_in_every_even_game() -> None:
    for sub_game in (2, 4, 6):
        captured, _step = _play(thief_seen_lag=True, intercept=True, sub_game=sub_game)
        assert captured is False, f"captured in sub-game {sub_game}"


def test_thief_flees_cop_scent_when_they_do_not_claim() -> None:
    move, _barrier = _thief(pos=(3, 3), known_opp=None, scent={(1, 1): 0.8, (0, 0): 0.2})
    nxt = apply_move((3, 3), move)
    assert abs(nxt[0] - 1) + abs(nxt[1] - 1) >= abs(3 - 1) + abs(3 - 1)


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
