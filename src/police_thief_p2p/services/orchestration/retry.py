"""Retry classification and deterministic bounded exponential backoff."""

from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.services.ports.random_source import RandomSource


class RetryClass(StrEnum):
    """Stable retry disposition for one failed operation."""

    RETRYABLE = "retryable"
    SEMANTIC = "semantic"
    INTEGRITY = "integrity"
    EXHAUSTED = "exhausted"


_RETRYABLE_CODES = frozenset(
    {
        "TIMEOUT",
        "CONNECTION_RESET",
        "CONNECTION_REFUSED",
        "HTTP_500",
        "HTTP_502",
        "HTTP_503",
        "HTTP_504",
        "DEPENDENCY_UNAVAILABLE",
    }
)
_INTEGRITY_CODES = frozenset({"DIGEST_MISMATCH", "TAMPER", "INVALID_SIGNATURE"})


def classify_failure(code: str, attempt: int, max_attempts: int) -> RetryClass:
    """Classify transport-only retries; semantic/integrity errors never retry."""
    if attempt >= max_attempts:
        return RetryClass.EXHAUSTED
    if code in _INTEGRITY_CODES:
        return RetryClass.INTEGRITY
    if code in _RETRYABLE_CODES:
        return RetryClass.RETRYABLE
    return RetryClass.SEMANTIC


@dataclass(frozen=True, slots=True)
class BackoffPolicy:
    """Exponential delay with bounded positive/negative seeded jitter."""

    base_ms: int
    maximum_ms: int
    jitter_fraction: float = 0.2

    def __post_init__(self) -> None:
        """Validate finite bounded delay configuration."""
        if self.base_ms < 1 or self.maximum_ms < self.base_ms:
            raise ValueError("backoff bounds are invalid")
        if not 0 <= self.jitter_fraction <= 1:
            raise ValueError("backoff jitter must be in [0, 1]")

    def delay_seconds(self, attempt: int, rng: RandomSource) -> float:
        """Return a deterministic bounded delay; callers own fake-clock waiting."""
        if attempt < 1:
            raise ValueError("backoff attempt must be positive")
        raw = float(min(self.maximum_ms, self.base_ms * (2 ** (attempt - 1))))
        jitter = (rng.random() * 2 - 1) * self.jitter_fraction
        delay = min(self.maximum_ms / 1_000, raw * (1 + jitter) / 1_000)
        return max(0.0, float(delay))
