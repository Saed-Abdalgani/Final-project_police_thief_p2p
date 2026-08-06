"""Reproducible paired role-swapped tournament execution over the offline arena."""

from collections.abc import Callable
from dataclasses import dataclass

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.experiments.arena import MatchArena
from police_thief_p2p.services.experiments.belief_track import (
    DEFAULT_BELIEF_PROFILE,
    BeliefProfile,
)
from police_thief_p2p.services.experiments.metrics import PairedMatch
from police_thief_p2p.services.experiments.pairing import MatchBrains
from police_thief_p2p.services.experiments.profiles import with_decision_budget
from police_thief_p2p.services.experiments.report import TournamentReport, build_report
from police_thief_p2p.services.experiments.roster import opponent
from police_thief_p2p.services.experiments.spec import BoardFixture, TournamentSpec
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.services.strategy.request import OpponentSummary
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig

type RandomFactory = Callable[[int], RandomSource]
_ROLE_SALT = {Role.POLICE: 1, Role.THIEF: 2}


@dataclass(frozen=True, slots=True)
class ExperimentRunner:
    """Run one declared tournament without touching live peers or opponent truth."""

    base_config: SharedConfig
    strategy: StrategyConfig
    clock: ClockPort
    random_factory: RandomFactory
    opponent_summary: OpponentSummary | None = None
    belief: BeliefProfile = DEFAULT_BELIEF_PROFILE

    def run(self, spec: TournamentSpec) -> TournamentReport:
        """Play every declared paired match and return the aggregated report."""
        profile = with_decision_budget(self.strategy, spec.decision_budget_ms)
        matches = [
            match
            for fixture in spec.fixtures
            for opponent_id in spec.opponent_ids
            for match in self._fixture_matches(spec, fixture, opponent_id, profile)
        ]
        rng = self.random_factory(spec.seeds[0])
        return build_report(spec, matches, self.base_config.scoring, rng)

    def _fixture_matches(
        self,
        spec: TournamentSpec,
        fixture: BoardFixture,
        opponent_id: str,
        profile: StrategyConfig,
    ) -> list[PairedMatch]:
        config = fixture.apply(self.base_config)
        entry = opponent(opponent_id)
        return [
            self._play(spec, config, fixture, entry.opponent_id, profile, seed, repetition, role)
            for seed in spec.seeds
            for repetition in range(spec.repetitions)
            for role in Role
        ]

    def _play(
        self,
        spec: TournamentSpec,
        config: SharedConfig,
        fixture: BoardFixture,
        opponent_id: str,
        profile: StrategyConfig,
        seed: int,
        repetition: int,
        candidate_role: Role,
    ) -> PairedMatch:
        brains = self.brains_for(spec.candidate_id, opponent_id, candidate_role)
        arena = MatchArena(config, profile, brains, self.clock, self.opponent_summary, self.belief)
        match_seed = seed * 101 + repetition * 7 + _ROLE_SALT[candidate_role]
        outcome = arena.play(
            self.random_factory(match_seed),
            observation_delay=spec.observation_delay,
            scent_dropout=spec.scent_dropout,
        )
        return PairedMatch(opponent_id, fixture.fixture_id, seed, candidate_role, outcome)

    @staticmethod
    def brains_for(candidate_id: str, opponent_id: str, candidate_role: Role) -> MatchBrains:
        """Assemble one paired brain set with the candidate in a chosen role."""
        candidate = opponent(candidate_id).brain(candidate_role)
        rival = opponent(opponent_id).brain(candidate_role.opponent)
        if candidate_role is Role.POLICE:
            return MatchBrains(candidate, rival)
        return MatchBrains(rival, candidate)
