"""System-information probe port for sealed Step-0 declarations."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SystemInfo:
    """Normalized non-secret system facts."""

    operating_system: str
    python_version: str
    cpu_model: str | None
    cpu_cores: int | None
    memory_bytes: int | None


@runtime_checkable
class SystemInfoPort(Protocol):
    """Collect normalized system information with safe unknown values."""

    def collect(self) -> SystemInfo:
        """Collect a local snapshot."""
        ...
