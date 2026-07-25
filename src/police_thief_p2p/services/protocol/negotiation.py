"""Fail-closed match negotiation and agreement validation."""

from __future__ import annotations

import base64
import binascii
import hashlib

from police_thief_p2p.domain.schedule import balanced_schedule
from police_thief_p2p.services.protocol.compatibility import (
    negotiate_extensions,
    protocol_is_compatible,
)
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure
from police_thief_p2p.services.protocol.negotiation_context import (
    NegotiationContext,
    deterministic_game_id,
)
from police_thief_p2p.services.protocol.negotiation_models import (
    MatchAcceptance,
    MatchProposal,
)
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.identifiers import GroupId
from police_thief_p2p.shared.version import PROTOCOL_VERSION, SCHEMA_VERSION


class NegotiationService:
    """Validate complete proposal/acceptance terms against local truth."""

    __slots__ = ("_context",)

    def __init__(self, context: NegotiationContext) -> None:
        """Bind one local peer's authoritative negotiation context."""
        self._context = context

    def validate_proposal(self, proposal: MatchProposal) -> dict[str, object]:
        """Validate all identities, bytes, versions, schedules, and league limits."""
        participants = proposal.participants
        groups = tuple(item.group_id for item in participants)
        if self._context.local_group not in groups:
            self._fail("local group is absent from proposal")
        if set(groups) != set(self._context.shared_config.agreed_between):
            self._fail("proposal groups do not match shared configuration")
        if not protocol_is_compatible(PROTOCOL_VERSION, proposal.protocol_version):
            self._fail("protocol version is incompatible")
        if proposal.schema_version != SCHEMA_VERSION:
            self._fail("schema version is incompatible")
        self._validate_bytes(proposal)
        self._validate_schedule(proposal)
        self._validate_league(proposal)
        self._validate_links(proposal)
        if proposal.game_id != deterministic_game_id(groups[0], groups[1], proposal.config_sha256):
            self._fail("game_id is not the deterministic proposal")
        extensions = negotiate_extensions(
            self._context.optional_capabilities,
            proposal.optional_capabilities,
        )
        return {
            "game_id": proposal.game_id,
            "game_uid": proposal.game_uid,
            "proposal_digest": proposal.digest(),
            "schedule_digest": sha256_digest(
                [item.model_dump(mode="json") for item in proposal.role_schedule]
            ),
            "optional_capabilities": extensions,
        }

    def validate_acceptance(
        self,
        acceptance: MatchAcceptance,
        proposal: MatchProposal,
    ) -> None:
        """Require exact proposal, game, UUID, and schedule digests."""
        agreement = self.validate_proposal(proposal)
        expected = (
            agreement["proposal_digest"],
            agreement["game_id"],
            agreement["game_uid"],
            agreement["schedule_digest"],
        )
        actual = (
            acceptance.proposal_digest,
            acceptance.game_id,
            acceptance.game_uid,
            acceptance.schedule_digest,
        )
        if actual != expected:
            raise ProtocolFailure(ProtocolErrorCode.CONFLICT, "acceptance terms do not match")

    def _validate_bytes(self, proposal: MatchProposal) -> None:
        try:
            remote_bytes = base64.b64decode(proposal.config_raw_b64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ProtocolFailure(
                ProtocolErrorCode.VALIDATION, "shared config bytes are not valid base64"
            ) from exc
        if remote_bytes != self._context.shared_raw_bytes:
            self._fail("raw shared config bytes differ")
        if hashlib.sha256(remote_bytes).hexdigest() != proposal.raw_config_sha256:
            self._fail("raw_config_sha256 does not match exchanged bytes")
        if proposal.config_sha256 != self._context.shared_config.digest():
            self._fail("config_sha256 does not match local shared configuration")
        if proposal.scent_model_sha256 != self._context.scent_digest:
            self._fail("scent model digest does not match")
        if proposal.scent_vector_version != "scent-5x5-v1":
            self._fail("scent numeric-vector version is unsupported")

    def _validate_schedule(self, proposal: MatchProposal) -> None:
        groups = tuple(item.group_id for item in proposal.participants)
        expected = balanced_schedule(*groups)
        actual = tuple(
            (item.sub_game_number, item.police_group, item.thief_group)
            for item in proposal.role_schedule
        )
        wanted = tuple(
            (int(item.sub_game_number), item.police_group, item.thief_group) for item in expected
        )
        if actual != wanted:
            self._fail("role schedule is not the balanced six-game schedule")

    def _validate_league(self, proposal: MatchProposal) -> None:
        if not proposal.counted:
            return
        for participant in proposal.participants:
            GroupId(participant.group_id, submission_mode=True)
            if participant.counted_total >= 10:
                self._fail("counted-game limit has already been reached")
        local = next(
            item for item in proposal.participants if item.group_id == self._context.local_group
        )
        if local.counted_total != self._context.ledger.total or set(local.counted_opponents) != set(
            self._context.ledger.opponents
        ):
            self._fail("counted declaration does not match the local ledger")
        opponent = next(item.group_id for item in proposal.participants if item is not local)
        if opponent in self._context.ledger.opponents:
            self._fail("a second counted match against this group is prohibited")

    def _validate_links(self, proposal: MatchProposal) -> None:
        links = [
            str(url)
            for participant in proposal.participants
            for url in (participant.repositories.police, participant.repositories.thief)
        ]
        if len(set(links)) != 4:
            self._fail("all four repository URLs must be distinct")

    @staticmethod
    def _fail(message: str) -> None:
        raise ProtocolFailure(ProtocolErrorCode.VALIDATION, message)
