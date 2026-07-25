"""One-process deterministic local sub-game simulator for tests only."""

from police_thief_p2p import SimulationSdk
from police_thief_p2p.domain import Action, LocalGameState
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


def simulate(
    initial_state: LocalGameState,
    actions: tuple[Action, ...],
) -> tuple[LocalGameState, bytes]:
    """Apply actions through the SDK and return final state plus canonical events."""
    sdk = SimulationSdk()
    state = initial_state
    events: list[object] = []
    for action in actions:
        result = sdk.apply_action(state, action)
        state = result.state
        events.extend(event.as_dict() for event in result.public_events)
        if state.terminal_reason is not None:
            break
    return state, canonical_json_bytes(events)
