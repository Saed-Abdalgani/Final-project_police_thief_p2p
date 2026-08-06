"""SDK-only offline tournament execution for reproducible experiments."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from police_thief_p2p.services.experiments.belief_track import BeliefProfile
    from police_thief_p2p.services.experiments.report import TournamentReport
    from police_thief_p2p.services.experiments.spec import TournamentSpec
    from police_thief_p2p.services.ports.clock import ClockPort
    from police_thief_p2p.shared.config_models import SharedConfig
    from police_thief_p2p.shared.strategy_config import StrategyConfig


class SimulationFacade:
    """Expose the offline experimentation arena without leaking service imports."""

    __slots__ = ()

    def run_tournament(
        self,
        spec: TournamentSpec,
        shared: SharedConfig,
        strategy: StrategyConfig,
        *,
        belief: BeliefProfile | None = None,
        clock: ClockPort | None = None,
    ) -> TournamentReport:
        """Play one declared campaign offline and return its aggregated report."""
        from police_thief_p2p.adapters.system.clocks import SystemClock
        from police_thief_p2p.adapters.system.deterministic_random import (
            DeterministicRandomSource,
        )
        from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE
        from police_thief_p2p.services.experiments.runner import ExperimentRunner

        runner = ExperimentRunner(
            base_config=shared,
            strategy=strategy,
            clock=SystemClock() if clock is None else clock,
            random_factory=DeterministicRandomSource,
            belief=DEFAULT_BELIEF_PROFILE if belief is None else belief,
        )
        return runner.run(spec)

    def split_manifest_document(self, split: str) -> dict[str, object]:
        """Return the frozen declaration of one experiment split."""
        from police_thief_p2p.services.experiments.splits import split_manifest

        manifest = split_manifest(split)
        return {**manifest.as_document(), "split_sha256": manifest.digest()}

    def search_space_document(self) -> dict[str, list[dict[str, object]]]:
        """Return the declared bounded hyperparameter spaces."""
        from police_thief_p2p.services.experiments.spaces import space_document

        return space_document()
