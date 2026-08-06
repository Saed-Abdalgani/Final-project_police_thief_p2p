"""Opponent entry type shared by every experiment roster declaration."""

from collections.abc import Callable
from dataclasses import dataclass

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.brain import StrategyBrain

type BrainFactory = Callable[[], StrategyBrain]
_CLASSIFICATIONS = frozenset({"candidate", "baseline", "adversary", "regression"})


@dataclass(frozen=True, slots=True)
class OpponentEntry:
    """One versioned opponent with a brain for each negotiated role."""

    opponent_id: str
    version: str
    classification: str
    police: BrainFactory
    thief: BrainFactory
    summary: str

    def __post_init__(self) -> None:
        """Reject unclassified or undocumented roster entries."""
        if self.classification not in _CLASSIFICATIONS:
            raise ValueError(f"unknown opponent classification: {self.classification!r}")
        if not self.opponent_id or not self.summary:
            raise ValueError("every opponent needs an identifier and a documented summary")

    def brain(self, role: Role) -> StrategyBrain:
        """Instantiate this opponent's brain for one role."""
        return self.police() if role is Role.POLICE else self.thief()


def entry(
    opponent_id: str,
    classification: str,
    police: BrainFactory,
    thief: BrainFactory,
    summary: str,
    version: str = "1.0.0",
) -> OpponentEntry:
    """Build one roster entry with the default profile version."""
    return OpponentEntry(opponent_id, version, classification, police, thief, summary)
