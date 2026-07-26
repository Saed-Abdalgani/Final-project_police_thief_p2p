import pytest

from police_thief_p2p.services.orchestration.phases import (
    TRANSITIONS,
    GamePhase,
    PhaseMachine,
    TransitionReason,
)
from police_thief_p2p.services.protocol.errors import ProtocolFailure
from police_thief_p2p.services.protocol.inventory import MUTATING_TOOLS
from police_thief_p2p.services.protocol.phases import ProtocolPhase, require_phase

pytestmark = pytest.mark.property

_PROTOCOL_ALLOWED = {
    "propose_match_v1": {ProtocolPhase.NEGOTIATING},
    "accept_match_v1": {ProtocolPhase.NEGOTIATING},
    "commit_step_v1": {ProtocolPhase.READY, ProtocolPhase.WAITING},
    "acknowledge_step_v1": {ProtocolPhase.AWAITING_ACK},
    "reveal_step_v1": {ProtocolPhase.REVEALING},
    "capture_claim_v1": {ProtocolPhase.WAITING},
    "capture_response_v1": {ProtocolPhase.VERIFYING},
    "final_reveal_v1": {ProtocolPhase.AUDITING},
    "audit_result_v1": {ProtocolPhase.AGREEING_RESULT},
    "agree_result_v1": {ProtocolPhase.REPORTING},
}


def test_every_orchestration_source_reason_target_combination() -> None:
    examined = 0
    legal = 0
    for source in GamePhase:
        for reason in TransitionReason:
            allowed = TRANSITIONS[source].get(reason, frozenset())
            for target in GamePhase:
                examined += 1
                machine = PhaseMachine(source)
                if target in allowed:
                    snapshot = machine.transition(source, target, reason)
                    assert snapshot.phase is target
                    assert snapshot.revision == 1
                    legal += 1
                else:
                    with pytest.raises(ValueError, match="not allowed"):
                        machine.transition(source, target, reason)
                    assert machine.snapshot().phase is source
                    assert machine.snapshot().revision == 0
    assert examined == len(GamePhase) ** 2 * len(TransitionReason)
    assert legal == sum(
        len(targets) for values in TRANSITIONS.values() for targets in values.values()
    )


def test_every_protocol_tool_phase_pair_is_explicitly_accepted_or_rejected() -> None:
    examined = 0
    for tool in sorted(MUTATING_TOOLS):
        allowed = _PROTOCOL_ALLOWED.get(tool, set())
        for phase in ProtocolPhase:
            examined += 1
            if phase in allowed:
                require_phase(tool, phase)
            else:
                with pytest.raises(ProtocolFailure, match="not allowed"):
                    require_phase(tool, phase)
    assert examined == len(MUTATING_TOOLS) * len(ProtocolPhase)
