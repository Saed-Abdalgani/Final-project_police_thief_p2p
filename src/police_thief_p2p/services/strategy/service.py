"""Deadline, failure, and final-legality boundary around strategy plugins."""

from dataclasses import replace

from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.domain.values import Action, ActionType, Role
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.services.strategy.baseline import fallback_decision
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.request import OpponentSummary, StrategyRequest
from police_thief_p2p.services.strategy.resolver import StrategyResolver
from police_thief_p2p.shared.strategy_config import StrategyConfig


class StrategyService:
    """Call one strategy under a hard cutoff and legal-action guard."""

    __slots__ = ("_resolver",)

    def __init__(self, resolver: StrategyResolver | None = None) -> None:
        """Create the service with an optional allowlisted resolver."""
        self._resolver = StrategyResolver() if resolver is None else resolver

    def decide(
        self,
        state: LocalGameState,
        belief: BeliefGrid,
        config: StrategyConfig,
        *,
        clock: ClockPort,
        rng: RandomSource,
        deadline: float | None = None,
        public_history: tuple[Action, ...] = (),
        opponent: OpponentSummary | None = None,
        map_area: str = "",
        hint_max_words: int = 15,
    ) -> Decision:
        """Return a legal decision or a deterministic baseline fallback."""
        start = clock.monotonic()
        absolute_deadline = (
            start + config.decision_budget_ms / 1_000 if deadline is None else deadline
        )
        request = StrategyRequest(
            state=state,
            belief=belief,
            legal_actions=state.legal_actions(),
            public_history=public_history,
            config=config,
            opponent=OpponentSummary() if opponent is None else opponent,
            clock=clock,
            rng=rng,
            deadline=absolute_deadline,
            map_area=map_area,
            hint_max_words=hint_max_words,
        )
        if start >= request.guard_deadline:
            return self._timed(fallback_decision(request, "FALLBACK_DEADLINE"), clock, start)
        try:
            decision = self._resolver.resolve(state.role, config).decide(request)
        except Exception:
            decision = fallback_decision(request, "FALLBACK_EXCEPTION")
        if clock.monotonic() >= request.deadline:
            decision = fallback_decision(request, "FALLBACK_DEADLINE")
        elif not self._legal(decision, request):
            decision = fallback_decision(request, "FALLBACK_INVALID")
        return self._timed(decision, clock, start)

    @staticmethod
    def _legal(decision: object, request: StrategyRequest) -> bool:
        if not isinstance(decision, Decision) or decision.action not in request.legal_actions:
            return False
        return not (
            request.state.role is Role.THIEF and decision.action.action_type is ActionType.BARRIER
        )

    @staticmethod
    def _timed(decision: Decision, clock: ClockPort, start: float) -> Decision:
        latency = max(0.0, (clock.monotonic() - start) * 1_000)
        return replace(decision, metrics=replace(decision.metrics, latency_ms=latency))
