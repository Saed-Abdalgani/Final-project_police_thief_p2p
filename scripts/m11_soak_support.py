"""Deterministic six-sub-game workflow used by the M11 soak campaign."""

from dataclasses import dataclass, field

from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.deadlines import DeadlineTracker
from police_thief_p2p.services.orchestration.journal import OrchestrationJournal
from police_thief_p2p.services.orchestration.phases import GamePhase


class MemoryRepository:
    """Small per-series repository proving bounded durable record growth."""

    def __init__(self) -> None:
        """Create an empty byte store."""
        self.values: dict[str, bytes] = {}

    def load(self, key: str) -> bytes | None:
        """Load one record."""
        return self.values.get(key)

    def save(self, key: str, data: bytes) -> None:
        """Save one record."""
        self.values[key] = data


@dataclass
class SeriesWorkflow:
    """One-step-per-game workflow covering the full six-game lifecycle."""

    journal: OrchestrationJournal = field(
        default_factory=lambda: OrchestrationJournal(MemoryRepository(), "m11-soak")
    )
    reset_games: list[int] = field(default_factory=list)

    def execute(
        self,
        phase: GamePhase,
        sub_game_number: int,
        step_number: int,
        _deadline: DeadlineTracker,
        _cancellation: CancellationToken,
    ) -> None:
        """Persist every lifecycle boundary."""
        self.journal.append(
            "phase",
            {
                "phase": phase.value,
                "sub_game": sub_game_number,
                "step": step_number,
            },
        )

    def reset_sub_game(self, sub_game_number: int) -> None:
        """Record each legal sub-game transition."""
        if not 1 <= sub_game_number <= 6:
            raise ValueError("soak sub-game is outside the six-game series")
        self.reset_games.append(sub_game_number)

    def sub_game_terminal(self, sub_game_number: int, step_number: int) -> bool:
        """Finish each sub-game after one verified progress step."""
        return 1 <= sub_game_number <= 6 and step_number == 1
