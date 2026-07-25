"""Validation and mutation helpers for the inbound pipeline."""

from __future__ import annotations

from pydantic import ValidationError

from police_thief_p2p.services.protocol.compatibility import protocol_is_compatible
from police_thief_p2p.services.protocol.envelope import ProtocolEnvelope, ProtocolResponse
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure
from police_thief_p2p.services.protocol.inventory import MUTATING_TOOLS, SESSION_TOOLS
from police_thief_p2p.services.protocol.limits import ProtocolLimits, parse_envelope
from police_thief_p2p.services.protocol.negotiation import NegotiationService
from police_thief_p2p.services.protocol.negotiation_models import (
    MatchAcceptance,
    MatchProposal,
)
from police_thief_p2p.services.protocol.phases import next_phase
from police_thief_p2p.services.protocol.session import ProtocolSession, SessionRegistry
from police_thief_p2p.shared.version import PROTOCOL_VERSION


class RequestProcessor:
    """Own request validation and one deterministic session mutation."""

    __slots__ = ("_limits", "_local_group", "_negotiation", "_sessions")

    def __init__(
        self,
        local_group: str,
        negotiation: NegotiationService,
        sessions: SessionRegistry,
        limits: ProtocolLimits,
    ) -> None:
        """Bind validation dependencies without owning persistence order."""
        self._local_group = local_group
        self._negotiation = negotiation
        self._sessions = sessions
        self._limits = limits

    def parse(self, tool: str, document: bytes) -> ProtocolEnvelope:
        """Parse and validate tool and protocol compatibility."""
        if tool not in SESSION_TOOLS:
            raise ProtocolFailure(ProtocolErrorCode.VALIDATION, "unknown protocol tool")
        envelope = parse_envelope(document, self._limits)
        if envelope.message_type != tool:
            raise ProtocolFailure(ProtocolErrorCode.VALIDATION, "message type does not match tool")
        if not protocol_is_compatible(PROTOCOL_VERSION, envelope.protocol_version):
            raise ProtocolFailure(ProtocolErrorCode.VALIDATION, "protocol version is incompatible")
        return envelope

    def resolve_session(self, envelope: ProtocolEnvelope, tool: str) -> ProtocolSession:
        """Load a session or validate and create the proposal bootstrap."""
        existing = self._sessions.get_optional(envelope.game_uid)
        if existing is not None:
            if tool == "propose_match_v1":
                proposal = self.proposal(envelope)
                if proposal.digest() != existing.proposal.digest():
                    raise ProtocolFailure(
                        ProtocolErrorCode.CONFLICT, "proposal changed for game UID"
                    )
            return existing
        if tool != "propose_match_v1":
            raise ProtocolFailure(ProtocolErrorCode.UNKNOWN_SESSION, "unknown game session")
        proposal = self.proposal(envelope)
        self._negotiation.validate_proposal(proposal)
        remote = envelope.sender.group_id
        if remote == self._local_group:
            raise ProtocolFailure(ProtocolErrorCode.IDENTITY, "sender must be the remote group")
        return self._sessions.create(proposal, remote)

    @staticmethod
    def validate_identity(session: ProtocolSession, envelope: ProtocolEnvelope) -> None:
        """Require the negotiated sender and role for this sub-game."""
        if envelope.sender.group_id != session.remote_group:
            raise ProtocolFailure(
                ProtocolErrorCode.IDENTITY, "sender identity does not match session"
            )
        try:
            term = session.proposal.role_schedule[envelope.sub_game_number - 1]
        except IndexError as exc:
            raise ProtocolFailure(
                ProtocolErrorCode.IDENTITY, "sub-game is outside negotiated schedule"
            ) from exc
        expected = "police" if term.police_group == envelope.sender.group_id else "thief"
        if envelope.sender.role.value != expected:
            raise ProtocolFailure(ProtocolErrorCode.IDENTITY, "sender role does not match schedule")

    def validate_sequence(
        self,
        session: ProtocolSession,
        envelope: ProtocolEnvelope,
    ) -> None:
        """Reject duplicates, gaps, and far-future sequences without buffering."""
        expected = session.next_sequences.get(envelope.sender.group_id, 1)
        if envelope.sequence == expected:
            return
        distance = envelope.sequence - expected
        detail = "old or duplicate sequence" if distance < 0 else "out-of-order sequence"
        if distance > self._limits.reorder_window:
            detail = "future sequence exceeds bounded reorder window"
        raise ProtocolFailure(ProtocolErrorCode.SEQUENCE, detail)

    def apply(
        self,
        session: ProtocolSession,
        envelope: ProtocolEnvelope,
        tool: str,
    ) -> ProtocolResponse:
        """Apply a validated mutation and return its deterministic response."""
        payload: dict[str, object]
        if tool == "propose_match_v1":
            payload = self._negotiation.validate_proposal(session.proposal)
        elif tool == "accept_match_v1":
            acceptance = self._acceptance(envelope)
            self._negotiation.validate_acceptance(acceptance, session.proposal)
            payload = {"agreement": "accepted", **acceptance.model_dump(mode="json")}
        elif tool in MUTATING_TOOLS:
            payload = {"accepted": True, "event_number": len(session.effects) + 1}
        else:
            raise ProtocolFailure(ProtocolErrorCode.VALIDATION, "tool is not mutating")
        session.phase = next_phase(tool, envelope.payload)
        payload["phase"] = session.phase.value
        return ProtocolResponse(
            ok=True,
            code="OK",
            message=f"{tool} applied",
            correlation_id=envelope.correlation_id,
            payload=payload,
        )

    @staticmethod
    def status(session: ProtocolSession, envelope: ProtocolEnvelope) -> ProtocolResponse:
        """Return only the public phase and terminal flag."""
        return ProtocolResponse(
            ok=True,
            code="OK",
            message="session status",
            correlation_id=envelope.correlation_id,
            payload={"phase": session.phase.value, "terminal": session.phase.terminal},
        )

    @staticmethod
    def proposal(envelope: ProtocolEnvelope) -> MatchProposal:
        """Parse a strict proposal payload."""
        try:
            return MatchProposal.model_validate(envelope.payload)
        except ValidationError as exc:
            raise ProtocolFailure(
                ProtocolErrorCode.VALIDATION, "match proposal payload is invalid"
            ) from exc

    @staticmethod
    def _acceptance(envelope: ProtocolEnvelope) -> MatchAcceptance:
        try:
            return MatchAcceptance.model_validate(envelope.payload)
        except ValidationError as exc:
            raise ProtocolFailure(
                ProtocolErrorCode.VALIDATION, "acceptance payload is invalid"
            ) from exc
