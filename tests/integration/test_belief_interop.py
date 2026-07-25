from police_thief_p2p.domain import Action, BarrierSet, Role, initial_local_state, transition
from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.belief.reliability import HintReliability
from police_thief_p2p.services.crypto.scent_evidence import scent_model_digest
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.scent import ScentPolicy
from tests.helpers.belief import GAME_UID, make_scent_reveal


def test_independent_peers_emit_identical_evidence_and_beliefs(
    shared_config: SharedConfig,
) -> None:
    emitters = (SimulationSdk(), SimulationSdk())
    state = initial_local_state(shared_config, Role.THIEF)
    next_state = transition(state, Action.stay()).state
    model_digest = scent_model_digest(ScentPolicy())
    frames = tuple(
        sdk.emit_scent_frame(
            game_uid=GAME_UID,
            sub_game_number=1,
            state=next_state,
            action=Action.stay(),
            scent_model_sha256=model_digest,
        )
        for sdk in emitters
    )
    assert frames[0].model_dump_json() == frames[1].model_dump_json()
    assert frames[0].frame_sha256 == frames[1].frame_sha256
    reveal = make_scent_reveal(frames[0])
    observers = (SimulationSdk(), SimulationSdk())
    updates = tuple(
        sdk.update_belief_from_reveal(
            sdk.initialize_belief(shared_config, Role.POLICE),
            frames[0],
            reveal,
            barriers=BarrierSet(),
            hint="north",
            own_position=initial_local_state(shared_config, Role.POLICE).position,
            reliability=HintReliability(),
        )
        for sdk in observers
    )
    assert updates[0].belief.digest() == updates[1].belief.digest()
    assert updates[0].belief.most_likely() == next_state.position
    view = observers[0].create_local_view(
        initial_local_state(shared_config, Role.POLICE),
        updates[0],
    )
    assert view.belief_entropy_bits >= 0
    assert not hasattr(view, "opponent_position")
    assert view.own_position == (0, 0)
