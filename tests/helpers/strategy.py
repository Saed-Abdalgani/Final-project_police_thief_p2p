from pathlib import Path

from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import LocalGameState, Role, initial_local_state
from police_thief_p2p.services.belief import BeliefGrid
from police_thief_p2p.services.strategy.request import OpponentSummary, StrategyRequest
from police_thief_p2p.shared.config_loader import load_private_path
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig

ROOT = Path(__file__).parents[2]


def strategy_config() -> StrategyConfig:
    return load_private_path(ROOT / "config/private/game.example.toml").strategy


def request_for(
    shared: SharedConfig,
    role: Role,
    *,
    belief: BeliefGrid | None = None,
    clock: FakeClock | None = None,
    seed: int = 7,
) -> StrategyRequest:
    state = initial_local_state(shared, role)
    selected_clock = FakeClock() if clock is None else clock
    return StrategyRequest(
        state=state,
        belief=belief or BeliefGrid.uniform(state.rules.board),
        legal_actions=state.legal_actions(),
        public_history=(),
        config=strategy_config(),
        opponent=OpponentSummary(),
        clock=selected_clock,
        rng=DeterministicRandomSource(seed),
        deadline=selected_clock.monotonic() + 1,
        map_area=shared.world.map_area,
        hint_max_words=shared.world.hint_max_words,
    )


def point_belief(state: LocalGameState, row: int, col: int) -> BeliefGrid:
    cell = next(item for item in state.rules.board.cells() if item.row == row and item.col == col)
    return BeliefGrid.from_weights(state.rules.board.size, {cell: 1.0})
