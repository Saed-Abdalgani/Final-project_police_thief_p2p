"""Persist-before-ack inbound protocol pipeline."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from police_thief_p2p.services.protocol.envelope import (
    ProtocolEnvelope,
    ProtocolResponse,
)
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure
from police_thief_p2p.services.protocol.health import health_payload
from police_thief_p2p.services.protocol.idempotency import (
    IdempotencyKey,
    IdempotencyRepository,
    RecordState,
)
from police_thief_p2p.services.protocol.inventory import TOOL_VERSIONS
from police_thief_p2p.services.protocol.limits import ProtocolLimits
from police_thief_p2p.services.protocol.negotiation import NegotiationService
from police_thief_p2p.services.protocol.phases import require_phase
from police_thief_p2p.services.protocol.processing import RequestProcessor
from police_thief_p2p.services.protocol.session import SessionRegistry
from police_thief_p2p.shared.version import (
    PROTOCOL_VERSION,
    SCHEMA_VERSION,
)


class ProtocolRuntime:
    """Execute strict requests with durable exactly-once application effects."""

    __slots__ = ("_health_provider", "_idempotency", "_processor", "_sessions", "_trace")

    def __init__(
        self,
        *,
        local_group: str,
        negotiation: NegotiationService,
        sessions: SessionRegistry,
        idempotency: IdempotencyRepository,
        limits: ProtocolLimits,
        health_provider: Callable[[], Mapping[str, object]] | None = None,
    ) -> None:
        """Bind one isolated peer's protocol dependencies."""
        self._sessions = sessions
        self._idempotency = idempotency
        self._processor = RequestProcessor(local_group, negotiation, sessions, limits)
        self._health_provider = health_provider
        self._trace: tuple[str, ...] = ()

    @property
    def last_pipeline_trace(self) -> tuple[str, ...]:
        """Return deterministic stage evidence for the most recent request."""
        return self._trace

    def health(self) -> ProtocolResponse:
        """Return liveness without game, identity, path, or private state."""
        return self._ok(
            None,
            "peer is alive",
            health_payload(self._health_provider),
        )

    def capabilities(self) -> ProtocolResponse:
        """Return versioned mandatory capability and readiness metadata."""
        return self._ok(
            None,
            "peer capabilities",
            {
                "status": "ready",
                "protocol_version": PROTOCOL_VERSION,
                "schema_version": SCHEMA_VERSION,
                "role_versions": {"police": "1.0.0", "thief": "1.0.0"},
                "tools": dict(TOOL_VERSIONS),
            },
        )

    def handle(self, tool: str, document: bytes) -> ProtocolResponse:
        """Run parse-to-persist pipeline and map every failure safely."""
        envelope: ProtocolEnvelope | None = None
        trace: list[str] = []
        try:
            trace.append("parse")
            envelope = self._processor.parse(tool, document)
            trace.append("session")
            session = self._processor.resolve_session(envelope, tool)
            trace.append("identity")
            self._processor.validate_identity(session, envelope)
            if tool == "peer_status_v1":
                return self._processor.status(session, envelope)
            trace.append("idempotency")
            key = IdempotencyKey(envelope.game_uid, envelope.sender.group_id, envelope.message_id)
            record = self._idempotency.inspect(key, envelope.digest())
            if record is not None and record.state is RecordState.COMPLETED:
                if record.response is None:
                    raise RuntimeError("completed idempotency record has no response")
                return record.response
            recovered = session.effects.get(envelope.message_id)
            if recovered is not None:
                self._idempotency.persist_result(key, envelope.digest(), recovered)
                return recovered
            trace.append("phase")
            require_phase(tool, session.phase)
            self._processor.validate_sequence(session, envelope)
            trace.append("persist")
            if record is None:
                self._idempotency.persist_intent(key, envelope.digest())
            trace.append("sdk")
            response = self._processor.apply(session, envelope, tool)
            session.next_sequences[envelope.sender.group_id] = envelope.sequence + 1
            session.effects[envelope.message_id] = response
            self._sessions.persist(session)
            trace.append("response")
            self._idempotency.persist_result(key, envelope.digest(), response)
            return response
        except ProtocolFailure as exc:
            return self._failure(exc, envelope)
        except Exception:
            correlation = envelope.correlation_id if envelope is not None else None
            return ProtocolResponse(
                ok=False,
                code=ProtocolErrorCode.INTERNAL.value,
                message="request failed safely; use correlation ID for diagnostics",
                correlation_id=correlation,
            )
        finally:
            self._trace = tuple(trace)

    @staticmethod
    def _ok(
        correlation_id: str | None,
        message: str,
        payload: dict[str, object],
    ) -> ProtocolResponse:
        return ProtocolResponse(
            ok=True,
            code="OK",
            message=message,
            correlation_id=correlation_id,
            payload=payload,
        )

    @staticmethod
    def _failure(
        failure: ProtocolFailure,
        envelope: ProtocolEnvelope | None,
    ) -> ProtocolResponse:
        return ProtocolResponse(
            ok=False,
            code=failure.code.value,
            message=failure.safe_message,
            correlation_id=(
                failure.correlation_id
                or (envelope.correlation_id if envelope is not None else None)
            ),
        )
