"""Offline two-role referee that plays one deterministic experiment sub-game."""

from dataclasses import dataclass, field, replace

from police_thief_p2p.domain.engine import transition
from police_thief_p2p.domain.state import LocalGameState, initial_local_state
from police_thief_p2p.domain.terminal import resolve_verified_terminal
from police_thief_p2p.domain.values import Action, ActionType, Position, Role, TerminalReason
from police_thief_p2p.services.experiments.belief_track import (
    DEFAULT_BELIEF_PROFILE,
    BeliefProfile,
    BeliefTrack,
    MatchScent,
)
from police_thief_p2p.services.experiments.observation import ObservationChannel
from police_thief_p2p.services.experiments.outcome import MatchOutcome, build_outcome
from police_thief_p2p.services.experiments.pairing import MatchBrains, PairResolver
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.request import OpponentSummary
from police_thief_p2p.services.strategy.service import StrategyService
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig

_RECENT_CELLS = 4


@dataclass(slots=True)
class _Side:
    """Mutable per-actor bookkeeping for one offline match."""

    state: LocalGameState
    track: BeliefTrack
    channel: ObservationChannel
    history: list[Action] = field(default_factory=list)
    recent: list[Position] = field(default_factory=list)


class MatchArena:
    """Play one sub-game through the real strategy guard and domain engine."""

    __slots__ = ("_belief", "_clock", "_config", "_opponent", "_service", "_strategy")

    def __init__(
        self,
        config: SharedConfig,
        strategy: StrategyConfig,
        brains: MatchBrains,
        clock: ClockPort,
        opponent: OpponentSummary | None = None,
        belief: BeliefProfile = DEFAULT_BELIEF_PROFILE,
    ) -> None:
        """Create an arena bound to one shared constitution and brain pair."""
        self._config = config
        self._strategy = strategy
        self._clock = clock
        self._opponent = OpponentSummary() if opponent is None else opponent
        self._belief = belief
        self._service = StrategyService(PairResolver(brains))

    def play(
        self,
        rng: RandomSource,
        *,
        observation_delay: int = 0,
        scent_dropout: float = 0.0,
    ) -> MatchOutcome:
        """Run Police-then-Thief turns until one verified terminal reason holds."""
        sides = {
            role: _Side(
                initial_local_state(self._config, role),
                BeliefTrack.create(self._config, role, self._belief),
                ObservationChannel(rng, observation_delay, scent_dropout),
            )
            for role in Role
        }
        scent = MatchScent()
        decisions: list[Decision] = []
        limit = sides[Role.THIEF].state.rules.max_steps
        for turn in range(1, limit + 1):
            for role in (Role.POLICE, Role.THIEF):
                decision = self._decide(sides[role], rng)
                decisions.append(decision)
                reason = self._apply(sides, role, decision, scent, turn)
                if reason is not None:
                    return build_outcome(reason, turn, decisions)
            scent.complete_turn(turn)
            _deliver(sides, turn)
        return build_outcome(TerminalReason.SURVIVAL, limit, decisions)

    def _decide(self, side: _Side, rng: RandomSource) -> Decision:
        return self._service.decide(
            side.state,
            side.track.belief,
            self._strategy,
            clock=self._clock,
            rng=rng,
            public_history=tuple(side.history),
            opponent=self._opponent,
            map_area=self._config.world.map_area,
            hint_max_words=self._config.world.hint_max_words,
        )

    def _apply(
        self,
        sides: dict[Role, _Side],
        role: Role,
        decision: Decision,
        scent: MatchScent,
        turn: int,
    ) -> TerminalReason | None:
        side = sides[role]
        action = decision.action
        side.state = transition(side.state, action).state
        side.history.append(action)
        side.recent = [*side.recent, side.state.position][-_RECENT_CELLS:]
        reason = _referee(sides, side, action, turn if role is Role.THIEF else turn - 1)
        if reason is not None:
            return reason
        opponent = sides[role.opponent]
        opponent.state = replace(opponent.state, public_barriers=side.state.public_barriers)
        opponent.channel.submit(turn, scent.emit(side.state, action), decision.hint)
        return None


def _referee(
    sides: dict[Role, _Side],
    actor: _Side,
    action: Action,
    completed_steps: int,
) -> TerminalReason | None:
    rules = actor.state.rules
    return resolve_verified_terminal(
        board=rules.board,
        police_position=sides[Role.POLICE].state.position,
        thief_position=sides[Role.THIEF].state.position,
        barriers=actor.state.public_barriers,
        completed_steps=completed_steps,
        survival_threshold=rules.survival_threshold,
        max_steps=rules.max_steps,
        placed_barrier=action.target if action.action_type is ActionType.BARRIER else None,
    )


def _deliver(sides: dict[Role, _Side], turn: int) -> None:
    for side in sides.values():
        for frame, hint in side.channel.due(turn):
            side.track.observe(
                frame,
                hint=hint,
                own_position=side.state.position,
                barriers=side.state.public_barriers,
                recent_cells=tuple(side.recent),
            )
