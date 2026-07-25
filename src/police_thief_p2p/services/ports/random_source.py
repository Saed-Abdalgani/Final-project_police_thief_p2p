"""Randomness abstractions separating security entropy from seeded simulation."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EntropySource(Protocol):
    """Produce cryptographically appropriate opaque bytes."""

    def token_bytes(self, length: int) -> bytes:
        """Return exactly ``length`` random bytes."""
        ...


@runtime_checkable
class RandomSource(Protocol):
    """Provide strategy/simulation randomness behind an injectable boundary."""

    def random(self) -> float:
        """Return a value in the half-open interval [0.0, 1.0)."""
        ...

    def randbelow(self, upper_bound: int) -> int:
        """Return an integer in ``range(upper_bound)``."""
        ...
