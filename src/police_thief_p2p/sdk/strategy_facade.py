"""SDK-only strategy selection and commitment-field composition."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from police_thief_p2p.domain.state import LocalGameState
    from police_thief_p2p.domain.values import Action
    from police_thief_p2p.services.belief.grid import BeliefGrid
    from police_thief_p2p.services.ports.clock import ClockPort
    from police_thief_p2p.services.ports.random_source import RandomSource
    from police_thief_p2p.services.strategy.commitment import StrategyCommitmentFields
    from police_thief_p2p.services.strategy.contracts import Decision
    from police_thief_p2p.services.strategy.request import OpponentSummary
    from police_thief_p2p.shared.effective_config import EffectiveConfig


class StrategyFacade:
    """Expose role strategy without allowing adapters to import services."""

    __slots__ = ()

    def choose_strategy_action(
        self,
        state: LocalGameState,
        belief: BeliefGrid,
        effective: EffectiveConfig,
        *,
        public_history: tuple[Action, ...] = (),
        opponent: OpponentSummary | None = None,
        clock: ClockPort | None = None,
        rng: RandomSource | None = None,
        deadline: float | None = None,
    ) -> Decision:
        """Choose through private selectors and shared world/hint limits."""
        from police_thief_p2p.adapters.system.clocks import SystemClock
        from police_thief_p2p.adapters.system.deterministic_random import (
            DeterministicRandomSource,
        )
        from police_thief_p2p.services.strategy.request import OpponentSummary
        from police_thief_p2p.services.strategy.service import StrategyService

        strategy = effective.private.strategy
        selected_clock = SystemClock() if clock is None else clock
        selected_rng = (
            DeterministicRandomSource(strategy.seed + state.step_number) if rng is None else rng
        )
        return StrategyService().decide(
            state,
            belief,
            strategy,
            clock=selected_clock,
            rng=selected_rng,
            deadline=deadline,
            public_history=public_history,
            opponent=OpponentSummary() if opponent is None else opponent,
            map_area=effective.shared.world.map_area,
            hint_max_words=effective.shared.world.hint_max_words,
        )

    def strategy_commitment_fields(
        self,
        decision: Decision,
    ) -> StrategyCommitmentFields:
        """Bind one guarded decision into exact Commit-Reveal fields."""
        from police_thief_p2p.services.strategy.commitment import commitment_fields

        return commitment_fields(decision)
