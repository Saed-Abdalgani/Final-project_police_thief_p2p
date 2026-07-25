"""Port for resolving the exact local source revision."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class GitState:
    """Public revision identity used by a Step-0 declaration."""

    commit: str | None
    dirty: bool | None


@runtime_checkable
class GitInfoPort(Protocol):
    """Resolve revision state without exposing repository internals."""

    def collect(self) -> GitState:
        """Return the exact commit and worktree status, or explicit unknowns."""
        ...
