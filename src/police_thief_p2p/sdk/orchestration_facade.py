"""SDK composition boundary for orchestration and redacted health."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from police_thief_p2p.services.orchestration.cancellation import CancellationToken
    from police_thief_p2p.services.orchestration.orchestrator import OrchestrationResult
    from police_thief_p2p.services.orchestration.ports import PeerWorkflowPort
    from police_thief_p2p.services.orchestration.watchdog import HealthView, Heartbeat
    from police_thief_p2p.services.ports.clock import ClockPort
    from police_thief_p2p.shared.effective_config import EffectiveConfig


class OrchestrationFacade:
    """Run the policy-free durable lifecycle through the application SDK."""

    __slots__ = ()

    def run_peer_lifecycle(
        self,
        workflow: PeerWorkflowPort,
        effective: EffectiveConfig,
        *,
        clock: ClockPort | None = None,
        cancellation: CancellationToken | None = None,
    ) -> OrchestrationResult:
        """Run the negotiated series using config-derived bounds."""
        from police_thief_p2p.adapters.system.clocks import SystemClock
        from police_thief_p2p.services.orchestration.deadlines import DeadlinePolicy
        from police_thief_p2p.services.orchestration.orchestrator import PeerOrchestrator

        selected_clock = SystemClock() if clock is None else clock
        orchestrator = PeerOrchestrator(
            workflow,
            clock=selected_clock,
            deadlines=DeadlinePolicy.from_effective(effective),
            cancellation=cancellation,
        )
        rules = effective.shared.movement_and_barriers
        return orchestrator.run_series(
            sub_games=effective.shared.network_and_league.num_games,
            max_steps=rules.max_moves,
        )

    def redacted_peer_health(
        self,
        heartbeat: Heartbeat | None,
        *,
        ready: bool,
        failed: bool = False,
        degraded: bool = False,
    ) -> HealthView:
        """Return an alive/ready/degraded/failed local-truth-safe view."""
        from police_thief_p2p.services.orchestration.watchdog import health_view

        return health_view(
            heartbeat,
            ready=ready,
            failed=failed,
            degraded=degraded,
        )
