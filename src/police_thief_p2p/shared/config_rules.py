"""Appendix F fixed values, defaults, and minimum-direction semantics."""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final


class MinimumDirection(StrEnum):
    """Direction in which a numeric minimum may become stricter."""

    AT_LEAST = "at_least"
    AT_MOST = "at_most"


@dataclass(frozen=True, slots=True)
class MinimumRule:
    """One Appendix F minimum with its safety-aware direction."""

    threshold: int
    direction: MinimumDirection

    def accepts(self, value: int) -> bool:
        """Return whether a candidate preserves or strengthens the minimum."""
        if self.direction is MinimumDirection.AT_LEAST:
            return value >= self.threshold
        return value <= self.threshold


FIXED_PARAMETERS: Final = MappingProxyType(
    {
        "board_and_agents.num_agents": 2,
        "movement_and_barriers.move_set": ("N", "S", "E", "W", "STAY"),
        "pheromones.pheromone_center_intensity": "0.9",
        "pheromones.pheromone_decay": "0.10",
        "pheromones.pheromone_grid_size": 5,
        "scoring.capture_cop": 20,
        "scoring.capture_thief": 5,
        "scoring.survival_cop": 5,
        "scoring.survival_thief": 10,
        "scoring.tie_score": 2,
        "network_and_league.num_games": 6,
        "network_and_league.diversity_reward": 10,
        "network_and_league.min_games_to_pass": 2,
        "network_and_league.max_games_per_team": 10,
    }
)

MINIMUM_PARAMETERS: Final = MappingProxyType(
    {
        "board_and_agents.grid_size": MinimumRule(7, MinimumDirection.AT_LEAST),
        "movement_and_barriers.max_barriers": MinimumRule(14, MinimumDirection.AT_LEAST),
        "movement_and_barriers.max_moves": MinimumRule(35, MinimumDirection.AT_LEAST),
        "movement_and_barriers.survival_threshold": MinimumRule(35, MinimumDirection.AT_LEAST),
        "rate_limiter_gatekeeper.requests_per_minute": MinimumRule(30, MinimumDirection.AT_MOST),
        "rate_limiter_gatekeeper.concurrent_requests": MinimumRule(2, MinimumDirection.AT_MOST),
        "rate_limiter_gatekeeper.retry_backoff_sec": MinimumRule(5, MinimumDirection.AT_LEAST),
        "rate_limiter_gatekeeper.max_retries": MinimumRule(3, MinimumDirection.AT_LEAST),
        "rate_limiter_gatekeeper.queue_depth": MinimumRule(100, MinimumDirection.AT_LEAST),
    }
)

NEGOTIABLE_DEFAULTS: Final = MappingProxyType(
    {
        "board_and_agents.axis_origin_corner": "top-left",
        "board_and_agents.axis_start_index": 0,
        "board_and_agents.thief_start": (3, 3),
        "board_and_agents.cop_start": (0, 0),
        "world.map_area": "",
        "world.hint_max_words": 15,
        "network_and_league.token_budget_per_series": 200_000,
        "network_and_league.response_timeout_sec": 30,
        "network_and_league.watchdog_timeout_sec": 60,
    }
)
