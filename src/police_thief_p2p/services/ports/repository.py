"""Durable byte-repository port."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class RepositoryPort(Protocol):
    """Load and atomically save opaque versioned records."""

    def load(self, key: str) -> bytes | None:
        """Load bytes or return ``None`` when the key is absent."""
        ...

    def save(self, key: str, data: bytes) -> None:
        """Atomically persist bytes under a validated key."""
        ...
