from hypothesis import given
from hypothesis import strategies as st

from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import Role
from police_thief_p2p.services.belief import BeliefGrid
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.service import StrategyService
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.strategy import request_for


@given(
    role=st.sampled_from(tuple(Role)),
    seed=st.integers(min_value=0, max_value=100_000),
    weights=st.lists(
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        min_size=49,
        max_size=49,
    ).filter(lambda values: sum(values) > 0),
)
def test_strategy_always_returns_engine_legal_deterministic_action(
    shared_config: SharedConfig,
    role: Role,
    seed: int,
    weights: list[float],
) -> None:
    base = request_for(shared_config, role)
    belief = BeliefGrid.from_weights(
        7,
        {cell: weights[index] for index, cell in enumerate(base.state.rules.board.cells())},
    )
    config = base.config.model_copy(update={"search_horizon": 1, "posterior_samples": 4})

    def choose() -> Decision:
        return StrategyService().decide(
            base.state,
            belief,
            config,
            clock=FakeClock(),
            rng=DeterministicRandomSource(seed),
        )

    first = choose()
    second = choose()
    assert first.action in base.state.legal_actions()
    assert first.action == second.action
    assert first.hint == second.hint
    assert first.fallback_used == second.fallback_used
