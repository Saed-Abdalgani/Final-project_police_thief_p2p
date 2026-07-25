"""Stable, caller-safe peer protocol failures."""

from enum import StrEnum


class ProtocolErrorCode(StrEnum):
    """Wire-stable protocol error categories."""

    VALIDATION = "PROTOCOL_VALIDATION"
    UNKNOWN_SESSION = "UNKNOWN_SESSION"
    IDENTITY = "IDENTITY_MISMATCH"
    PHASE = "PHASE_VIOLATION"
    SEQUENCE = "SEQUENCE_VIOLATION"
    CONFLICT = "IDEMPOTENCY_CONFLICT"
    TIMEOUT = "REQUEST_TIMEOUT"
    OVERLOADED = "SERVER_OVERLOADED"
    INTERNAL = "INTERNAL_FAILURE"


class ProtocolFailure(Exception):
    """A safe failure that may cross the remote protocol boundary."""

    def __init__(
        self,
        code: ProtocolErrorCode,
        safe_message: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """Retain only a stable code, safe message, and optional correlation ID."""
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
        self.correlation_id = correlation_id
