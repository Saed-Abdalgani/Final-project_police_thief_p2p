import time
from dataclasses import dataclass, field

import pytest

from police_thief_p2p.adapters.system.clocks import FakeClock, SystemClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import Role
from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.deadlines import (
    DeadlinePolicy,
    DeadlineTracker,
    Operation,
)
from police_thief_p2p.services.orchestration.journal import OrchestrationJournal
from police_thief_p2p.services.orchestration.orchestrator import PeerOrchestrator
from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.orchestration.watchdog import Watchdog
from police_thief_p2p.services.strategy.service import StrategyService
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.strategy import request_for

pytestmark = [pytest.mark.performance, pytest.mark.no_cover]


class MemoryRepository:
    def __init__(self) -> None:
        self.records: dict[str, bytes] = {}

    def load(self, key: str) -> bytes | None:
        return self.records.get(key)

    def save(self, key: str, data: bytes) -> None:
        self.records[key] = data


@dataclass
class PersistentWorkflow:
    journal: OrchestrationJournal = field(
        default_factory=lambda: OrchestrationJournal(MemoryRepository(), "soak")
    )

    def execute(
        self,
        phase: GamePhase,
        sub_game_number: int,
        step_number: int,
        _deadline: DeadlineTracker,
        _cancellation: CancellationToken,
    ) -> None:
        self.journal.append(
            "phase",
            {
                "phase": phase.value,
                "sub_game": sub_game_number,
                "step": step_number,
            },
        )

    def reset_sub_game(self, sub_game_number: int) -> None:
        assert sub_game_number == 1

    def sub_game_terminal(self, sub_game_number: int, step_number: int) -> bool:
        return sub_game_number == step_number == 1


def test_strategy_normal_decisions_fit_bounded_latency(
    shared_config: SharedConfig,
) -> None:
    latencies = []
    for role in Role:
        for seed in range(3):
            request = request_for(shared_config, role, seed=seed)
            started = time.perf_counter()
            decision = StrategyService().decide(
                request.state,
                request.belief,
                request.config,
                clock=SystemClock(),
                rng=DeterministicRandomSource(seed),
            )
            latencies.append((time.perf_counter() - started) * 1_000)
            assert decision.action in request.legal_actions
    assert max(latencies) < 500


def test_one_thousand_persistent_watchdog_subgames_make_progress() -> None:
    policy = DeadlinePolicy(dict.fromkeys(Operation, 2.0), 3)
    terminals: dict[GamePhase, int] = {}
    for _seed in range(1_000):
        clock = FakeClock()
        workflow = PersistentWorkflow()
        result = PeerOrchestrator(
            workflow,
            clock=clock,
            deadlines=policy,
        ).run_series(sub_games=1, max_steps=1)
        watchdog = Watchdog(clock, policy.watchdog_timeout)
        for heartbeat in result.heartbeats:
            assert watchdog.check(heartbeat) is None
        terminals[result.phase] = terminals.get(result.phase, 0) + 1
        assert workflow.journal.records
    assert terminals == {GamePhase.COMPLETED: 1_000}
