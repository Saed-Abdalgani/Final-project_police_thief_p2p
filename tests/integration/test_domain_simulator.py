import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.domain import Action, Direction, Role
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.sub_game_simulator import simulate

pytestmark = pytest.mark.integration


def test_same_config_and_actions_produce_byte_identical_event_sequence(
    shared_config: SharedConfig,
) -> None:
    initial = SimulationSdk().create_local_game(shared_config, Role.POLICE)
    actions = (
        Action.move(Direction.SOUTH),
        Action.barrier(initial.position),
        Action.stay(),
    )
    first_state, first_events = simulate(initial, actions)
    second_state, second_events = simulate(initial, actions)
    assert first_state == second_state
    assert first_events == second_events
    assert first_events == (
        b'[{"actor":"police","event_type":"barrier_placed","step_number":2,"target":[0,0]}]'
    )
