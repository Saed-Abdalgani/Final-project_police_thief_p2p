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
    cpu_frequency_mhz: int | None = None
    gpu_model: str | None = None
    vram_bytes: int | None = None
    platform: str = "unknown"

    def __post_init__(self) -> None:
        """Reject impossible numeric probe values."""
        positive = (self.cpu_cores, self.memory_bytes, self.cpu_frequency_mhz)
        if any(value is not None and (type(value) is not int or value < 1) for value in positive):
            raise ValueError("system capacities must be positive integers or unknown")
        if self.vram_bytes is not None and (
            type(self.vram_bytes) is not int or self.vram_bytes < 0
        ):
            raise ValueError("VRAM must be a non-negative integer or unknown")


@runtime_checkable
class SystemInfoPort(Protocol):
    """Collect normalized system information with safe unknown values."""

    def collect(self) -> SystemInfo:
        """Collect a local snapshot."""
        ...
