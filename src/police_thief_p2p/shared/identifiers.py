"""Validated identifiers used by configuration and protocol contracts."""

import re
import uuid
from dataclasses import dataclass
from typing import ClassVar, Self

_GROUP_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,62}[A-Za-z0-9])?$")
_GAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
_SUBMISSION_GROUP_PATTERN = re.compile(r"^[A-Za-z0-9]{8}$")
MAX_COUNTER = 2_147_483_647


@dataclass(frozen=True, slots=True)
class GroupId:
    """ASCII group identifier with an optional strict submission mode."""

    value: str
    submission_mode: bool = False

    def __post_init__(self) -> None:
        """Reject ambiguous, unsafe, or incorrectly sized group identifiers."""
        pattern = _SUBMISSION_GROUP_PATTERN if self.submission_mode else _GROUP_PATTERN
        if pattern.fullmatch(self.value) is None:
            mode = "eight ASCII alphanumerics" if self.submission_mode else "a safe ASCII ID"
            raise ValueError(f"group_id must be {mode}")

    def __str__(self) -> str:
        """Return the validated wire value."""
        return self.value


@dataclass(frozen=True, slots=True)
class GameId:
    """Lowercase ASCII game slug safe for URLs and filenames."""

    value: str
    MAX_LENGTH: ClassVar[int] = 64

    def __post_init__(self) -> None:
        """Reject traversal, Unicode confusables, and invalid slug syntax."""
        if len(self.value) > self.MAX_LENGTH or _GAME_PATTERN.fullmatch(self.value) is None:
            raise ValueError("game_id must be a lowercase ASCII slug of at most 64 characters")

    def __str__(self) -> str:
        """Return the validated wire value."""
        return self.value


@dataclass(frozen=True, slots=True)
class UuidId:
    """Canonical UUID-backed identifier base."""

    value: uuid.UUID

    def __init__(self, value: uuid.UUID | str) -> None:
        """Parse a UUID and retain its canonical value."""
        try:
            parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("identifier must be a valid UUID") from exc
        object.__setattr__(self, "value", parsed)

    @classmethod
    def generate(cls) -> Self:
        """Generate a cryptographically random UUID4 identifier."""
        return cls(uuid.uuid4())

    def __str__(self) -> str:
        """Return the lowercase canonical UUID."""
        return str(self.value)


class GameUid(UuidId):
    """Globally unique game-series identifier."""


class MessageId(UuidId):
    """Globally unique protocol-message identifier."""


class CorrelationId(UuidId):
    """Identifier joining request, retry, and response records."""


@dataclass(frozen=True, slots=True)
class BoundedCounter:
    """Positive protocol counter with a signed 32-bit wire ceiling."""

    value: int
    label: ClassVar[str] = "counter"

    def __post_init__(self) -> None:
        """Reject booleans, non-integers, zero, negatives, and overflow."""
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError(f"{self.label} must be an integer")
        if not 1 <= self.value <= MAX_COUNTER:
            raise ValueError(f"{self.label} must be between 1 and {MAX_COUNTER}")

    def __int__(self) -> int:
        """Return the validated integer."""
        return self.value


class SubGameNumber(BoundedCounter):
    """One-based sub-game sequence number."""

    label = "sub_game_number"


class StepNumber(BoundedCounter):
    """One-based step sequence number."""

    label = "step_number"
