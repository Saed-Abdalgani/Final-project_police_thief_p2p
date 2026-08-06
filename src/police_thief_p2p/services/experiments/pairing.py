"""Explicit brain pairing for offline experiments without private selectors."""

from dataclasses import dataclass

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.resolver import StrategyResolver
from police_thief_p2p.shared.strategy_config import StrategyConfig


@dataclass(frozen=True, slots=True)
class MatchBrains:
    """One validated Police and Thief brain pair for a single match."""

    police: StrategyBrain
    thief: StrategyBrain

    def __post_init__(self) -> None:
        """Reject brains whose declared role does not match their slot."""
        if self.police.role is not Role.POLICE or self.thief.role is not Role.THIEF:
            raise ValueError("match brains must declare matching roles")

    def for_role(self, role: Role) -> StrategyBrain:
        """Return the brain that plays one role."""
        return self.police if role is Role.POLICE else self.thief

    def swapped(self, other: "MatchBrains") -> "MatchBrains":
        """Return this pair's Police brain against another pair's Thief brain."""
        return MatchBrains(self.police, other.thief)


class PairResolver(StrategyResolver):
    """Resolve pre-instantiated experiment brains instead of TOML selectors."""

    __slots__ = ("_brains",)

    def __init__(self, brains: MatchBrains) -> None:
        """Bind one immutable validated brain pair."""
        self._brains = brains

    def resolve(self, role: Role, config: StrategyConfig) -> StrategyBrain:
        """Return the paired brain for the requested role."""
        del config
        return self._brains.for_role(role)
