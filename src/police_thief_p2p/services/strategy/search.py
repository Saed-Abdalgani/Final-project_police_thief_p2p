"""Bounded deterministic sampling and risk-sensitive iterative search."""

import math
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from police_thief_p2p.domain.values import Action, Position
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.services.strategy.contracts import ScoreBreakdown
from police_thief_p2p.services.strategy.search_state import RoleEvaluator, SearchState


class BoundedTranspositionCache[K, V]:
    """Deterministic least-recently-used cache with an exact entry ceiling."""

    __slots__ = ("_entries", "_limit", "hits")

    def __init__(self, limit: int) -> None:
        """Create a positive-capacity cache."""
        if limit < 1:
            raise ValueError("cache limit must be positive")
        self._entries: OrderedDict[K, V] = OrderedDict()
        self._limit = limit
        self.hits = 0

    def get_or_compute(self, key: K, compute: Callable[[], V]) -> V:
        """Return a cached value or compute and deterministically evict oldest."""
        if key in self._entries:
            self.hits += 1
            value = self._entries.pop(key)
            self._entries[key] = value
            return value
        value = compute()
        self._entries[key] = value
        if len(self._entries) > self._limit:
            self._entries.popitem(last=False)
        return value

    def keys(self) -> tuple[K, ...]:
        """Return keys from least to most recently used."""
        return tuple(self._entries)


def stratified_samples(
    belief: BeliefGrid,
    count: int,
    rng: RandomSource,
) -> tuple[tuple[Position, float], ...]:
    """Sample the full posterior by deterministic equal-mass strata."""
    if count < 1:
        raise ValueError("posterior sample count must be positive")
    populated = tuple((cell, mass) for cell, mass in belief.items() if mass > 0)
    cumulative: list[tuple[Position, float]] = []
    total = 0.0
    for cell, mass in populated:
        total += mass
        cumulative.append((cell, total))
    selected: dict[Position, int] = {}
    for index in range(count):
        target = (index + rng.random()) / count
        cell = next(cell for cell, upper in cumulative if target <= upper + 1e-15)
        selected[cell] = selected.get(cell, 0) + 1
    return tuple(
        (cell, occurrences / count)
        for cell, occurrences in sorted(
            selected.items(), key=lambda item: (item[0].row, item[0].col)
        )
    )


def cvar(values: tuple[float, ...], tail_fraction: float) -> float:
    """Return the mean of the lowest-score tail for risk-averse maximization."""
    if not values or not 0 < tail_fraction <= 1:
        raise ValueError("CVaR inputs are invalid")
    ordered = sorted(values)
    count = max(1, math.ceil(len(ordered) * tail_fraction))
    return math.fsum(ordered[:count]) / count


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Best action from the deepest fully completed iteration."""

    action: Action
    breakdown: ScoreBreakdown
    completed_depth: int
    cache_hits: int


def iterative_search(
    state: SearchState,
    actions: tuple[Action, ...],
    evaluator: RoleEvaluator,
    *,
    clock: ClockPort,
    deadline: float,
    cache_entries: int,
    risk_weight: float,
    near_tie_epsilon: float = 0.0,
    rng: RandomSource | None = None,
) -> SearchResult:
    """Run depth iterations and never publish a partially evaluated depth."""
    if not actions or not 0 <= risk_weight <= 1 or not 0 <= near_tie_epsilon <= 0.25:
        raise ValueError("search actions or risk weight are invalid")
    cache: BoundedTranspositionCache[tuple[object, ...], tuple[ScoreBreakdown, tuple[float, ...]]]
    cache = BoundedTranspositionCache(cache_entries)
    best: tuple[Action, ScoreBreakdown] | None = None
    completed = 0
    for depth in range(1, state.horizon + 1):
        ranked: list[tuple[float, int, Action, ScoreBreakdown]] = []
        interrupted = False
        for index, action in enumerate(actions):
            if clock.monotonic() >= deadline:
                break
            key = (*state.cache_key(), action, depth)
            try:
                breakdown, outcomes = cache.get_or_compute(
                    key,
                    partial(evaluator.evaluate, state, action, depth),
                )
            except TimeoutError:
                interrupted = True
                break
            tail = cvar(outcomes, 0.25)
            objective = (1 - risk_weight) * breakdown.total + risk_weight * tail
            ranked.append((objective, -index, action, breakdown))
        if interrupted or len(ranked) != len(actions):
            break
        maximum = max(item[0] for item in ranked)
        tolerance = near_tie_epsilon * max(1.0, abs(maximum))
        near = tuple(item for item in ranked if maximum - item[0] <= tolerance)
        selected = 0 if rng is None or len(near) == 1 else rng.randbelow(len(near))
        _, _, action, breakdown = near[selected]
        best = (action, breakdown)
        completed = depth
    if best is None:
        raise TimeoutError("strategy deadline expired before depth one")
    return SearchResult(*best, completed, cache.hits)
