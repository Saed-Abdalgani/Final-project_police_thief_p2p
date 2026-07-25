"""Stable abstract interface implemented by every strategy plugin."""

from abc import ABC, abstractmethod
from typing import ClassVar

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.request import StrategyRequest


class StrategyBrain(ABC):
    """Select one action from an engine-generated legal candidate set."""

    role: ClassVar[Role]

    @abstractmethod
    def decide(self, request: StrategyRequest) -> Decision:
        """Return a deterministic, deadline-aware decision."""
