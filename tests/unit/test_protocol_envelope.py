import json
import math
import uuid

import pytest
from pydantic import ValidationError

from police_thief_p2p.services.protocol.compatibility import (
    negotiate_extensions,
    protocol_is_compatible,
)
from police_thief_p2p.services.protocol.errors import ProtocolFailure
from police_thief_p2p.services.protocol.limits import ProtocolLimits, parse_envelope
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.protocol import make_envelope, make_proposal


def test_envelope_round_trips_all_common_fields(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    envelope = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )

    parsed = parse_envelope(envelope.canonical_bytes(), ProtocolLimits())

    assert parsed == envelope
    assert parsed.digest() == envelope.digest()
    assert parsed.message_id == str(uuid.UUID(parsed.message_id))


@pytest.mark.parametrize(
    ("document", "limits"),
    [
        (b'{"a":1,"a":2}', ProtocolLimits()),
        (b"\xff", ProtocolLimits()),
        (b"[]", ProtocolLimits()),
        (b'{"payload":NaN}', ProtocolLimits()),
        (b'{"x":"12345"}', ProtocolLimits(max_string_length=4)),
        (b'{"x":[1,2]}', ProtocolLimits(max_collection_items=1)),
        (b'{"x":{"y":{"z":1}}}', ProtocolLimits(max_json_depth=2)),
        (b"{}" * 20, ProtocolLimits(max_request_bytes=8)),
    ],
)
def test_hostile_or_unbounded_envelopes_fail_closed(
    document: bytes,
    limits: ProtocolLimits,
) -> None:
    with pytest.raises(ProtocolFailure, match=r"bounded|byte"):
        parse_envelope(document, limits)


def test_limits_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="positive"):
        ProtocolLimits(reorder_window=0)


def test_envelope_and_model_validator_edges(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    envelope = make_envelope(proposal, "commit_step_v1", {}, sequence=1)
    for field, value in (
        ("protocol_version", "not-semver"),
        ("message_type", "Bad Tool"),
        ("message_id", "not-a-uuid"),
        ("correlation_id", "not-a-uuid"),
        ("game_uid", "not-a-uuid"),
    ):
        payload = envelope.model_dump(mode="json")
        payload[field] = value
        with pytest.raises(ValidationError):
            type(envelope).model_validate(payload)


def test_object_and_infinite_float_bounds_are_enforced() -> None:
    with pytest.raises(ProtocolFailure, match="bounded"):
        parse_envelope(
            b'{"a":1,"b":2}',
            ProtocolLimits(max_collection_items=1),
        )
    with pytest.raises(ProtocolFailure, match="bounded"):
        parse_envelope(
            b'{"value":1e400}',
            ProtocolLimits(),
        )


def test_protocol_minor_compatibility_and_extension_intersection() -> None:
    assert protocol_is_compatible("1.4.2", "1.3.9")
    assert protocol_is_compatible("1.4.2", "1.4.99")
    assert not protocol_is_compatible("1.4.2", "2.0.0")
    assert not protocol_is_compatible("1.4.2", "1.5.0")
    assert not protocol_is_compatible("bad", "1.0.0")
    assert negotiate_extensions(
        {"edu.example.trace": 1, "edu.example.local": 2},
        {"edu.example.trace": 9, "edu.other.remote": 3},
    ) == {"edu.example.trace": 1}
    with pytest.raises(ProtocolFailure, match="namespace"):
        negotiate_extensions({"unsafe": 1}, {})


def test_nonfinite_payload_is_rejected_before_serialization(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    value = make_envelope(proposal, "commit_step_v1", {}, sequence=1).model_dump(mode="json")
    value["payload"] = {"bad": math.inf}
    document = json.dumps(value).encode()
    with pytest.raises(ProtocolFailure, match="bounded"):
        parse_envelope(document, ProtocolLimits())
