"""Controlled cooperative resource shutdown in safety order."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from police_thief_p2p.services.orchestration.cancellation import CancellationToken


@runtime_checkable
class ShutdownResource(Protocol):
    """One bounded closeable orchestration resource."""

    def close(self) -> None:
        """Close or flush the resource."""
        ...


@dataclass(frozen=True, slots=True)
class ShutdownResources:
    """Resources ordered by required shutdown dependency."""

    transport: ShutdownResource
    journal: ShutdownResource
    artifact_writer: ShutdownResource
    gui: ShutdownResource
    workers: ShutdownResource


def controlled_shutdown(
    resources: ShutdownResources,
    cancellation: CancellationToken,
) -> tuple[str, ...]:
    """Cancel work then close transport, journal, artifacts, GUI, and workers."""
    cancellation.cancel()
    order = (
        ("transport", resources.transport),
        ("journal", resources.journal),
        ("artifact_writer", resources.artifact_writer),
        ("gui", resources.gui),
        ("workers", resources.workers),
    )
    closed: list[str] = []
    for name, resource in order:
        resource.close()
        closed.append(name)
    return tuple(closed)
