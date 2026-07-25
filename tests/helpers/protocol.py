"""Deterministic M4 proposal and envelope builders."""

from __future__ import annotations

import base64
import hashlib
import uuid
from typing import Any

from pydantic import HttpUrl, TypeAdapter

from police_thief_p2p.domain import Role, balanced_schedule
from police_thief_p2p.services.protocol.declaration import (
    HardwareDeclaration,
    SoftwareDeclaration,
    StepZeroDeclaration,
)
from police_thief_p2p.services.protocol.envelope import ProtocolEnvelope, SenderIdentity
from police_thief_p2p.services.protocol.negotiation_context import deterministic_game_id
from police_thief_p2p.services.protocol.negotiation_models import (
    MatchAcceptance,
    MatchProposal,
    Participant,
    PlayedCommits,
    RepositoryLinks,
    RoleTerm,
)
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.version import PROTOCOL_VERSION, SCHEMA_VERSION

GROUP_A = "GRP00001"
GROUP_B = "GRP00002"
GAME_UID = "11111111-1111-4111-8111-111111111111"
_URL = TypeAdapter(HttpUrl)


def _participant(group: str, index: int, opponents: tuple[str, ...]) -> Participant:
    return Participant(
        group_name=f"Group {index}",
        group_id=group,
        members=(f"Member {index}",),
        repositories=RepositoryLinks(
            police=_URL.validate_python(f"https://example.com/group-{index}-police"),
            thief=_URL.validate_python(f"https://example.com/group-{index}-thief"),
        ),
        commits=PlayedCommits(police=f"{index}" * 40, thief=f"{index + 2}" * 40),
        public_mcp_url=_URL.validate_python(f"http://127.0.0.1:800{index}/mcp"),
        role_capabilities=(Role.POLICE, Role.THIEF),
        counted_total=len(opponents),
        counted_opponents=opponents,
    )


def _declaration(participant: Participant) -> StepZeroDeclaration:
    return StepZeroDeclaration(
        group_id=participant.group_id,
        hardware=HardwareDeclaration(
            operating_system="test-os",
            cpu_model="test-cpu",
            cpu_cores=4,
            cpu_frequency_mhz=None,
            ram_bytes=8_000_000_000,
            gpu_model=None,
            vram_bytes=None,
            timezone="UTC",
        ),
        software=SoftwareDeclaration(
            code_version="0.7.0",
            played_commit=participant.commits.police,
            model_provider="template",
            model_name="deterministic-template",
            estimated_tokens=0,
        ),
    )


def make_proposal(
    shared_config: SharedConfig,
    shared_bytes: bytes,
    *,
    counted: bool = False,
    opponents_a: tuple[str, ...] = (),
    opponents_b: tuple[str, ...] = (),
) -> MatchProposal:
    """Build one complete, valid deterministic proposal."""
    participants = (
        _participant(GROUP_A, 1, opponents_a),
        _participant(GROUP_B, 2, opponents_b),
    )
    schedule = tuple(
        RoleTerm(
            sub_game_number=int(item.sub_game_number),
            police_group=item.police_group,
            thief_group=item.thief_group,
        )
        for item in balanced_schedule(GROUP_A, GROUP_B)
    )
    config_digest = shared_config.digest()
    return MatchProposal(
        protocol_version=PROTOCOL_VERSION,
        schema_version=SCHEMA_VERSION,
        game_id=deterministic_game_id(GROUP_A, GROUP_B, config_digest),
        game_uid=GAME_UID,
        counted=counted,
        warmup_name=None if counted else "localhost-conformance",
        participants=participants,
        config_raw_b64=base64.b64encode(shared_bytes).decode("ascii"),
        raw_config_sha256=hashlib.sha256(shared_bytes).hexdigest(),
        config_sha256=config_digest,
        scent_model_sha256=sha256_digest(shared_config.pheromones.model_dump(mode="json")),
        scent_vector_version="scent-5x5-v1",
        role_schedule=schedule,
        declarations=(
            _declaration(participants[0]),
            _declaration(participants[1]),
        ),
        optional_capabilities={"edu.example.trace": {"version": 1}},
    )


def make_acceptance(proposal: MatchProposal) -> MatchAcceptance:
    """Build the exact acceptance for ``proposal``."""
    return MatchAcceptance(
        proposal_digest=proposal.digest(),
        game_id=proposal.game_id,
        game_uid=proposal.game_uid,
        schedule_digest=sha256_digest(
            [item.model_dump(mode="json") for item in proposal.role_schedule]
        ),
    )


def make_envelope(
    proposal: MatchProposal,
    tool: str,
    payload: dict[str, Any],
    *,
    sequence: int,
    sender: str = GROUP_A,
    sub_game_number: int = 1,
    message_id: str | None = None,
) -> ProtocolEnvelope:
    """Build a valid envelope for the sender's scheduled role."""
    term = proposal.role_schedule[sub_game_number - 1]
    role = Role.POLICE if term.police_group == sender else Role.THIEF
    return ProtocolEnvelope(
        protocol_version=PROTOCOL_VERSION,
        message_type=tool,
        message_id=message_id or str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
        game_uid=proposal.game_uid,
        sub_game_number=sub_game_number,
        step_number=1,
        sender=SenderIdentity(group_id=sender, role=role),
        sequence=sequence,
        payload=payload,
    )
