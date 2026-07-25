"""Allowlisted role-aware loading for private strategy selectors."""

import importlib

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.shared.strategy_config import StrategyConfig

_PREFIX = "police_thief_p2p.services.strategy."


class StrategyResolver:
    """Resolve only local strategy classes implementing the stable interface."""

    __slots__ = ()

    def resolve(self, role: Role, config: StrategyConfig) -> StrategyBrain:
        """Instantiate the role's private selector after namespace/type checks."""
        selector = config.police_class if role is Role.POLICE else config.thief_class
        module_name, separator, class_name = selector.rpartition(".")
        if not separator or not module_name.startswith(_PREFIX):
            raise ValueError("strategy selector is outside the local allowlist")
        try:
            module = importlib.import_module(module_name)
            candidate = getattr(module, class_name)
        except (ImportError, AttributeError) as exc:
            raise ValueError("strategy selector cannot be resolved") from exc
        if not isinstance(candidate, type) or not issubclass(candidate, StrategyBrain):
            raise ValueError("strategy selector must name a StrategyBrain subclass")
        if candidate.role is not role:
            raise ValueError("strategy selector role does not match requested role")
        return candidate()
