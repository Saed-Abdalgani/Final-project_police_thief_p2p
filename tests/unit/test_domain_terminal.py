import pytest

from police_thief_p2p.domain import (
    BarrierSet,
    Board,
    Position,
    TerminalReason,
    barrier_capture,
    direct_capture,
    enclosure_capture,
    maximum_step_reached,
    resolve_verified_terminal,
    survival_reached,
)


def test_direct_and_barrier_capture_predicates() -> None:
    cell = Position(2, 2)
    other = Position(2, 3)
    assert direct_capture(cell, cell)
    assert not direct_capture(cell, other)
    assert barrier_capture(cell, cell)
    assert not barrier_capture(cell, other)


@pytest.mark.parametrize(
    ("thief", "barriers", "expected"),
    [
        (Position(0, 0), {Position(0, 1), Position(1, 0)}, True),
        (Position(0, 1), {Position(0, 0), Position(0, 2), Position(1, 1)}, True),
        (
            Position(1, 1),
            {Position(0, 1), Position(2, 1), Position(1, 0), Position(1, 2)},
            True,
        ),
        (Position(1, 1), {Position(0, 1), Position(2, 1), Position(1, 0)}, False),
    ],
)
def test_enclosure_excludes_stay_for_corner_edge_and_corridor(
    thief: Position,
    barriers: set[Position],
    expected: bool,
) -> None:
    assert enclosure_capture(Board(3), thief, BarrierSet(frozenset(barriers))) is expected


def test_enclosure_handles_barrier_cell_and_invalid_position() -> None:
    cell = Position(1, 1)
    assert enclosure_capture(Board(3), cell, BarrierSet(frozenset({cell})))
    with pytest.raises(ValueError, match="outside"):
        enclosure_capture(Board(3), Position(3, 0), BarrierSet())


@pytest.mark.parametrize("steps", [34, 35, 36])
def test_survival_and_ceiling_exact_boundaries(steps: int) -> None:
    assert survival_reached(steps, 35) is (steps >= 35)
    assert maximum_step_reached(steps, 35) is (steps >= 35)


def test_step_predicates_reject_invalid_values() -> None:
    for predicate in (survival_reached, maximum_step_reached):
        with pytest.raises(ValueError, match="steps"):
            predicate(-1, 35)
        with pytest.raises(ValueError, match="positive"):
            predicate(0, 0)


def _resolve(**overrides: object) -> TerminalReason | None:
    arguments: dict[str, object] = {
        "board": Board(4),
        "police_position": Position(3, 3),
        "thief_position": Position(1, 1),
        "barriers": BarrierSet(),
        "completed_steps": 1,
        "survival_threshold": 35,
        "max_steps": 35,
    }
    arguments.update(overrides)
    return resolve_verified_terminal(**arguments)  # type: ignore[arg-type]


def test_verified_terminal_resolution_order_and_all_reasons() -> None:
    assert _resolve(tamper=True, technical=True) is TerminalReason.TAMPER
    assert _resolve(technical=True) is TerminalReason.TECHNICAL
    assert _resolve(placed_barrier=Position(1, 1)) is TerminalReason.BARRIER_CAPTURE
    assert _resolve(police_position=Position(1, 1)) is TerminalReason.CAPTURE
    enclosure = BarrierSet(
        frozenset(
            {
                Position(0, 1),
                Position(2, 1),
                Position(1, 0),
                Position(1, 2),
            }
        )
    )
    assert _resolve(barriers=enclosure) is TerminalReason.ENCLOSURE
    assert _resolve(completed_steps=35) is TerminalReason.SURVIVAL
    assert (
        _resolve(completed_steps=20, survival_threshold=30, max_steps=20)
        is TerminalReason.STEP_CEILING
    )
    assert _resolve(stopped=True) is TerminalReason.STOPPED
    assert _resolve() is None


def test_verified_terminal_rejects_invalid_offline_evidence() -> None:
    with pytest.raises(ValueError, match="position"):
        _resolve(police_position=Position(4, 0))
    with pytest.raises(ValueError, match="barrier"):
        _resolve(barriers=BarrierSet(frozenset({Position(4, 0)})))
    with pytest.raises(ValueError, match="placed barrier"):
        _resolve(placed_barrier=Position(4, 0))
    with pytest.raises(ValueError, match="steps"):
        _resolve(completed_steps=-1)
