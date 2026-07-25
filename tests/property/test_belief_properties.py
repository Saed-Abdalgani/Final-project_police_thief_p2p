import math

from hypothesis import given
from hypothesis import strategies as st

from police_thief_p2p.domain import BarrierSet, Board, Position
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.belief.motion import MotionContext, UniformMotionModel


@st.composite
def belief_cases(
    draw: st.DrawFn,
) -> tuple[int, list[float], frozenset[Position]]:
    size = draw(st.integers(min_value=2, max_value=12))
    weights = draw(
        st.lists(
            st.floats(
                min_value=0,
                max_value=1e100,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=size * size,
            max_size=size * size,
        )
    )
    masked_indices = draw(
        st.sets(
            st.integers(min_value=0, max_value=size * size - 1),
            max_size=size * size - 1,
        )
    )
    masked = frozenset(Position(index // size, index % size) for index in masked_indices)
    return size, weights, masked


@given(belief_cases())
def test_belief_normalization_finiteness_masks_and_determinism(
    case: tuple[int, list[float], frozenset[Position]],
) -> None:
    size, values, masked = case
    weights = {Position(index // size, index % size): value for index, value in enumerate(values)}
    left = BeliefGrid.from_weights(size, weights, masked=masked)
    right = BeliefGrid.from_weights(size, weights, masked=masked)
    assert left == right
    assert math.isclose(math.fsum(left.probabilities), 1.0, abs_tol=1e-12)
    assert all(math.isfinite(value) and value >= 0 for value in left.probabilities)
    assert all(left.probability(cell) == 0 for cell in masked)


@given(
    size=st.integers(min_value=2, max_value=30),
    row=st.integers(min_value=0, max_value=29),
    col=st.integers(min_value=0, max_value=29),
)
def test_uniform_transition_mass_is_row_stochastic(size: int, row: int, col: int) -> None:
    source = Position(row % size, col % size)
    transitions = UniformMotionModel().transition(
        Board(size),
        source,
        BarrierSet(),
        MotionContext(Position(0, 0)),
    )
    assert math.isclose(
        math.fsum(probability for _, probability in transitions),
        1.0,
        abs_tol=1e-12,
    )
    assert all(probability >= 0 for _, probability in transitions)
