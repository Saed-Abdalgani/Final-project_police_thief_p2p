"""Typed, serialization-safe errors exposed by the public SDK."""

from enum import StrEnum
from typing import TypedDict


class ErrorCode(StrEnum):
    """Stable foundation error codes."""

    INVALID_INPUT = "INVALID_INPUT"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorPayload(TypedDict):
    """Safe serialized error shape."""

    code: str
    message: str
    correlation_id: str | None


class SdkError(Exception):
    """Base SDK error containing only caller-safe details."""

    def __init__(
        self,
        code: ErrorCode,
        safe_message: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize an error without accepting unsafe internal detail."""
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
        self.correlation_id = correlation_id

    def as_dict(self) -> ErrorPayload:
        """Return a JSON-compatible caller-safe payload."""
        return {
            "code": self.code.value,
            "message": self.safe_message,
            "correlation_id": self.correlation_id,
        }

    def __repr__(self) -> str:
        """Return a representation that cannot expose an exception cause."""
        return (
            f"{type(self).__name__}(code={self.code.value!r}, "
            f"safe_message={self.safe_message!r}, correlation_id={self.correlation_id!r})"
        )


class InvalidInputError(SdkError):
    """Caller input failed validation."""

    def __init__(self, safe_message: str, *, correlation_id: str | None = None) -> None:
        """Initialize an invalid-input error."""
        super().__init__(
            ErrorCode.INVALID_INPUT,
            safe_message,
            correlation_id=correlation_id,
        )


class DependencyUnavailableError(SdkError):
    """An injected external dependency is unavailable."""

    def __init__(self, safe_message: str, *, correlation_id: str | None = None) -> None:
        """Initialize a dependency-unavailable error."""
        super().__init__(
            ErrorCode.DEPENDENCY_UNAVAILABLE,
            safe_message,
            correlation_id=correlation_id,
        )
