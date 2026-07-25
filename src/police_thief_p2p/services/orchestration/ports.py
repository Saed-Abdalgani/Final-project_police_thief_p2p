"""Injected service ports coordinated by the policy-free Orchestrator."""

from typing import Protocol, runtime_checkable

from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.deadlines import DeadlineTracker
from police_thief_p2p.services.orchestration.phases import GamePhase


@runtime_checkable
class PeerWorkflowPort(Protocol):
    """Implement domain/protocol operations outside the Orchestrator."""

    def execute(
        self,
        phase: GamePhase,
        sub_game_number: int,
        step_number: int,
        deadline: DeadlineTracker,
        cancellation: CancellationToken,
    ) -> None:
        """Execute one bounded phase-specific service operation."""
        ...

    def reset_sub_game(self, sub_game_number: int) -> None:
        """Reset role-local state before one scheduled sub-game."""
        ...

    def sub_game_terminal(self, sub_game_number: int, step_number: int) -> bool:
        """Return service-owned terminal detection after verification."""
        ...


class RefusalError(RuntimeError):
    """Negotiation was safely refused for a semantic incompatibility."""


class IntegrityError(RuntimeError):
    """Verified evidence indicates tamper or integrity failure."""
