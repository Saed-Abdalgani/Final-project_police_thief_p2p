import pytest
from pydantic import ValidationError

from police_thief_p2p.services.protocol.compatibility import negotiate_extensions
from police_thief_p2p.services.protocol.errors import ProtocolFailure
from police_thief_p2p.services.protocol.negotiation import NegotiationService
from police_thief_p2p.services.protocol.negotiation_context import NegotiationContext
from police_thief_p2p.services.protocol.negotiation_models import (
    CountedLedger,
    Participant,
    PlayedCommits,
    RepositoryLinks,
)
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.identifiers import GroupId
from tests.helpers.protocol import GROUP_A, GROUP_B, make_acceptance, make_proposal


def _service(
    shared_config: SharedConfig,
    shared_bytes: bytes,
    *,
    opponents: frozenset[str] = frozenset(),
) -> NegotiationService:
    return NegotiationService(
        NegotiationContext(
            GROUP_A,
            shared_config,
            shared_bytes,
            CountedLedger(opponents),
            {"edu.example.trace": {"version": 1}},
        )
    )


def test_valid_warmup_proposal_and_exact_acceptance(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    service = _service(shared_config, shared_config_bytes)
    agreement = service.validate_proposal(proposal)
    service.validate_acceptance(make_acceptance(proposal), proposal)
    assert agreement["game_uid"] == proposal.game_uid
    assert agreement["optional_capabilities"] == {"edu.example.trace": {"version": 1}}
    compatible_minor = proposal.model_copy(update={"protocol_version": "0.3.9"})
    service.validate_proposal(compatible_minor)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("game_id", "wrong-game", "deterministic"),
        ("schema_version", "9.9.9", "schema"),
        ("protocol_version", "9.9.9", "protocol"),
        ("raw_config_sha256", "0" * 64, "raw_config"),
        ("config_sha256", "0" * 64, "config_sha256"),
        ("scent_model_sha256", "0" * 64, "scent model"),
        ("scent_vector_version", "wrong", "numeric-vector"),
    ],
)
def test_negotiation_mismatch_matrix(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
    field: str,
    value: str,
    message: str,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes).model_copy(update={field: value})
    with pytest.raises(ProtocolFailure, match=message):
        _service(shared_config, shared_config_bytes).validate_proposal(proposal)


def test_one_byte_config_and_schedule_mismatch_fail(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    changed_bytes = shared_config_bytes + b"\n"
    with pytest.raises(ProtocolFailure, match="raw shared"):
        _service(shared_config, changed_bytes).validate_proposal(proposal)
    reversed_schedule = tuple(reversed(proposal.role_schedule))
    with pytest.raises(ProtocolFailure, match="schedule"):
        _service(shared_config, shared_config_bytes).validate_proposal(
            proposal.model_copy(update={"role_schedule": reversed_schedule})
        )


def test_counted_boundaries_ledger_truth_and_duplicate_opponent(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    nine = tuple(f"OPP0000{index}" for index in range(1, 10))
    proposal = make_proposal(
        shared_config,
        shared_config_bytes,
        counted=True,
        opponents_a=nine,
        opponents_b=nine,
    )
    _service(shared_config, shared_config_bytes, opponents=frozenset(nine)).validate_proposal(
        proposal
    )
    ten = (*nine, "OPP00010")
    over_limit = make_proposal(
        shared_config,
        shared_config_bytes,
        counted=True,
        opponents_a=ten,
        opponents_b=ten,
    )
    with pytest.raises(ProtocolFailure, match="limit"):
        _service(shared_config, shared_config_bytes, opponents=frozenset(ten)).validate_proposal(
            over_limit
        )
    with pytest.raises(ProtocolFailure, match="local ledger"):
        _service(shared_config, shared_config_bytes).validate_proposal(proposal)
    duplicate = make_proposal(
        shared_config,
        shared_config_bytes,
        counted=True,
        opponents_a=(GROUP_B,),
    )
    with pytest.raises(ProtocolFailure, match="second counted"):
        _service(
            shared_config, shared_config_bytes, opponents=frozenset({GROUP_B})
        ).validate_proposal(duplicate)


def test_counted_group_commit_and_url_shapes_are_strict() -> None:
    with pytest.raises(ValueError, match="eight"):
        GroupId("short", submission_mode=True)
    with pytest.raises(ValidationError, match="played commit"):
        PlayedCommits(police="dirty", thief="a" * 40)
    with pytest.raises(ValidationError, match="credential-free"):
        RepositoryLinks.model_validate(
            {
                "police": "https://user:pass@example.com/a",  # pragma: allowlist secret
                "thief": "https://example.com/b",
            }
        )


def test_acceptance_and_repository_conflicts_fail(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    service = _service(shared_config, shared_config_bytes)
    acceptance = make_acceptance(proposal).model_copy(update={"proposal_digest": "0" * 64})
    with pytest.raises(ProtocolFailure, match="acceptance"):
        service.validate_acceptance(acceptance, proposal)
    duplicate_links = proposal.participants[1].model_copy(
        update={"repositories": proposal.participants[0].repositories}
    )
    with pytest.raises(ProtocolFailure, match="four repository"):
        service.validate_proposal(
            proposal.model_copy(
                update={"participants": (proposal.participants[0], duplicate_links)}
            )
        )


def test_participant_rejects_credential_url_roles_and_false_total() -> None:
    base = {
        "group_name": "Group",
        "group_id": GROUP_A,
        "members": ("Member",),
        "repositories": RepositoryLinks.model_validate(
            {"police": "https://example.com/a", "thief": "https://example.com/b"}
        ),
        "commits": PlayedCommits(police="a" * 40, thief="b" * 40),
        "public_mcp_url": "https://example.com/mcp",
        "role_capabilities": ("police", "thief"),
        "counted_total": 0,
        "counted_opponents": (),
    }
    with pytest.raises(ValidationError, match="credentials"):
        Participant.model_validate({**base, "public_mcp_url": "https://x:y@example.com/mcp"})
    with pytest.raises(ValidationError, match="role"):
        Participant.model_validate({**base, "role_capabilities": ("police",)})
    with pytest.raises(ValidationError, match="counted total"):
        Participant.model_validate({**base, "counted_total": 1})
    assert negotiate_extensions({}, {}) == {}


def test_proposal_and_ledger_model_invariants(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    with pytest.raises(ValidationError, match="must differ"):
        RepositoryLinks.model_validate(
            {"police": "https://example.com/a", "thief": "https://example.com/a"}
        )
    with pytest.raises(ValidationError, match="unique"):
        Participant.model_validate(
            {
                **proposal.participants[0].model_dump(mode="json"),
                "counted_total": 2,
                "counted_opponents": ["OTHER001", "OTHER001"],
            }
        )
    with pytest.raises(ValidationError, match="digest"):
        type(proposal).model_validate(
            {**proposal.model_dump(mode="json"), "config_sha256": "short"}
        )
    with pytest.raises(ValidationError, match="distinct"):
        type(proposal).model_validate(
            {
                **proposal.model_dump(mode="json"),
                "participants": [proposal.participants[0], proposal.participants[0]],
            }
        )
    with pytest.raises(ValidationError, match="exactly one"):
        type(proposal).model_validate({**proposal.model_dump(mode="json"), "warmup_name": None})
    with pytest.raises(ValidationError, match="declarations"):
        type(proposal).model_validate(
            {
                **proposal.model_dump(mode="json"),
                "declarations": list(reversed(proposal.declarations)),
            }
        )
    with pytest.raises(ValueError, match="safe ASCII"):
        CountedLedger(frozenset({"../bad"}))
    assert proposal.canonical_bytes()
