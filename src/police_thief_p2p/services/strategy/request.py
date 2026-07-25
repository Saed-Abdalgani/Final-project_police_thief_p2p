"""Local-truth-only input contract passed to strategy brains."""

from dataclasses import dataclass

from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.domain.values import Action
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.shared.strategy_config import StrategyConfig


@dataclass(frozen=True, slots=True)
class OpponentSummary:
    """Normalized legally learned motion and trust summary."""

    mixture: tuple[float, float, float, float, float] = (0.2,) * 5
    hint_trust: float = 0.5
    observations: int = 0

    def __post_init__(self) -> None:
        """Require a normalized, finite public-only summary."""
        if len(self.mixture) != 5 or any(value < 0 or value > 1 for value in self.mixture):
            raise ValueError("opponent mixture weights must be probabilities")
        if abs(sum(self.mixture) - 1.0) > 1e-9:
            raise ValueError("opponent mixture weights must sum to one")
        if not 0 <= self.hint_trust <= 1 or self.observations < 0:
            raise ValueError("opponent summary bounds are invalid")


@dataclass(frozen=True, slots=True)
class StrategyRequest:
    """Complete safe input for one deterministic role decision."""

    state: LocalGameState
    belief: BeliefGrid
    legal_actions: tuple[Action, ...]
    public_history: tuple[Action, ...]
    config: StrategyConfig
    opponent: OpponentSummary
    clock: ClockPort
    rng: RandomSource
    deadline: float
    map_area: str = ""
    hint_max_words: int = 15

    def __post_init__(self) -> None:
        """Validate board consistency, engine candidates, and bounded context."""
        if self.state.rules.board.size != self.belief.size:
            raise ValueError("strategy state and belief dimensions differ")
        if not self.legal_actions or any(
            action not in self.state.legal_actions() for action in self.legal_actions
        ):
            raise ValueError("strategy candidates must be engine-provided legal actions")
        if self.deadline < 0 or not 1 <= self.hint_max_words <= 100:
            raise ValueError("strategy deadline or hint cap is invalid")
        if len(self.public_history) > 1_024:
            raise ValueError("strategy public history is unbounded")

    @property
    def guard_deadline(self) -> float:
        """Return the search cutoff that reserves commitment/persistence time."""
        return self.deadline - self.config.guard_margin_ms / 1_000
