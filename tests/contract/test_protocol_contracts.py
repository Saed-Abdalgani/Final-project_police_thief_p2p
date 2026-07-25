import inspect

import pytest

from police_thief_p2p.sdk import (
    MatchAcceptance,
    MatchProposal,
    ProtocolEnvelope,
    ProtocolResponse,
    SenderIdentity,
)
from police_thief_p2p.services.protocol.inventory import (
    MUTATING_TOOLS,
    SESSION_TOOLS,
    TOOL_VERSIONS,
)
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.schema_registry import validate_schema
from tests.helpers.protocol import make_acceptance, make_envelope, make_proposal

pytestmark = pytest.mark.contract


def test_frozen_tool_inventory_is_complete_versioned_and_minimal() -> None:
    assert TOOL_VERSIONS == {
        "health_v1": "1.0.0",
        "capabilities_v1": "1.0.0",
        "propose_match_v1": "1.0.0",
        "accept_match_v1": "1.0.0",
        "commit_step_v1": "1.0.0",
        "acknowledge_step_v1": "1.0.0",
        "reveal_step_v1": "1.0.0",
        "capture_claim_v1": "1.0.0",
        "capture_response_v1": "1.0.0",
        "final_reveal_v1": "1.0.0",
        "audit_result_v1": "1.0.0",
        "agree_result_v1": "1.0.0",
        "peer_status_v1": "1.0.0",
    }
    assert (
        set(TOOL_VERSIONS)
        - {
            "health_v1",
            "capabilities_v1",
        }
        == SESSION_TOOLS
    )
    assert SESSION_TOOLS - {"peer_status_v1"} == MUTATING_TOOLS


def test_protocol_public_models_are_immutable_documented_and_schema_valid(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    acceptance = make_acceptance(proposal)
    envelope = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    validate_schema(
        proposal.model_dump(mode="json"),
        "match_proposal.schema.json",
        source="generated proposal",
    )
    validate_schema(
        acceptance.model_dump(mode="json"),
        "match_acceptance.schema.json",
        source="generated acceptance",
    )
    validate_schema(
        envelope.model_dump(mode="json"),
        "protocol_envelope.schema.json",
        source="generated envelope",
    )
    for model in (
        MatchAcceptance,
        MatchProposal,
        ProtocolEnvelope,
        ProtocolResponse,
        SenderIdentity,
    ):
        assert inspect.getdoc(model)
        assert model.model_config["frozen"] is True
