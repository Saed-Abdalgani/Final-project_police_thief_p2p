"""Reusable deterministic measurements for the M7 evidence runner."""

import statistics
import time
from dataclasses import replace

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import Action, ActionType, LocalGameState, Role
from police_thief_p2p.services.belief import BeliefGrid
from police_thief_p2p.services.strategy.geometry import destination
from police_thief_p2p.services.strategy.police_features import PoliceEvaluator
from police_thief_p2p.services.strategy.request import OpponentSummary, StrategyRequest
from police_thief_p2p.services.strategy.search import cvar, stratified_samples
from police_thief_p2p.services.strategy.search_state import SearchState
from police_thief_p2p.services.strategy.thief_features import ThiefEvaluator
from police_thief_p2p.shared.coordinates import Position
from police_thief_p2p.shared.effective_config import EffectiveConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig


def percentile(values: list[float], fraction: float) -> float:
    """Return a nearest-rank percentile."""
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * fraction + 0.999) - 1)]


def isolated_request(
    state: LocalGameState,
    belief: BeliefGrid,
    config: StrategyConfig,
    seed: int,
) -> StrategyRequest:
    """Build one isolated deterministic evaluation request."""
    clock = SystemClock()
    return StrategyRequest(
        state,
        belief,
        state.legal_actions(),
        (),
        config,
        OpponentSummary(),
        clock,
        DeterministicRandomSource(seed),
        clock.monotonic() + 2,
    )


def utility(role: Role, item: StrategyRequest, action: Action) -> float:
    """Score one action under the role's declared feature objective."""
    samples = stratified_samples(
        item.belief,
        item.config.posterior_samples,
        DeterministicRandomSource(item.config.seed),
    )
    evaluation_request = replace(item, rng=DeterministicRandomSource(item.config.seed))
    search = SearchState(
        item.state.position,
        item.state.public_barriers,
        samples,
        role,
        item.state.rules.max_barriers - item.state.barriers_placed,
        item.config.search_horizon,
        (),
        item.state.rules.board.size,
    )
    evaluator = (
        PoliceEvaluator(evaluation_request)
        if role is Role.POLICE
        else ThiefEvaluator(evaluation_request)
    )
    breakdown, outcomes = evaluator.evaluate(search, action, item.config.search_horizon)
    risk = item.config.police.risk if role is Role.POLICE else item.config.thief.risk
    return (1 - risk) * breakdown.total + risk * cvar(outcomes, 0.25)


def reference_action(role: Role, state: LocalGameState, belief: BeliefGrid) -> Action:
    """Return the documented argmax-Manhattan, no-graph reference action."""
    peak = belief.most_likely()
    candidates = tuple(
        action for action in state.legal_actions() if action.action_type is not ActionType.BARRIER
    )
    ranked: list[tuple[int, int, Action]] = []
    for index, action in enumerate(candidates):
        target = destination(state.rules.board, state.position, action)
        distance = abs(target.row - peak.row) + abs(target.col - peak.col)
        score = -distance if role is Role.POLICE else distance
        ranked.append((score, -index, action))
    return max(ranked, key=lambda item: (item[0], item[1]))[2]


def collect_latency(
    sdk: SimulationSdk,
    effective: EffectiveConfig,
) -> tuple[dict[str, list[float]], int, list[dict[str, object]]]:
    """Measure role latency, fallback count, and deterministic snapshots."""
    latencies: dict[str, list[float]] = {role.value: [] for role in Role}
    fallbacks = 0
    snapshots: list[dict[str, object]] = []
    for role in Role:
        state = sdk.create_local_game(effective.shared, role)
        belief = BeliefGrid.uniform(state.rules.board)
        for seed in range(10):
            started = time.perf_counter()
            decision = sdk.choose_strategy_action(
                state, belief, effective, rng=DeterministicRandomSource(seed)
            )
            latencies[role.value].append((time.perf_counter() - started) * 1_000)
            fallbacks += int(decision.fallback_used)
            if seed == 0:
                snapshots.append(
                    {
                        "role": role.value,
                        "action": repr(decision.action),
                        "reason": decision.reason_code,
                    }
                )
    return latencies, fallbacks, snapshots


def paired_matrix(
    sdk: SimulationSdk,
    effective: EffectiveConfig,
) -> dict[str, dict[str, int]]:
    """Run a role-swapped paired matrix against the reference policy."""
    matrix: dict[str, dict[str, int]] = {}
    for role in Role:
        state = sdk.create_local_game(effective.shared, role)
        outcomes = {"advanced_wins": 0, "ties": 0, "baseline_wins": 0}
        for seed in range(1_000, 1_020):
            first = Position(seed % 7, (seed * 3) % 7)
            second = Position(6 - first.row, 6 - first.col)
            belief = BeliefGrid.from_weights(7, {first: 0.51, second: 0.49})
            advanced = sdk.choose_strategy_action(
                state, belief, effective, rng=DeterministicRandomSource(seed)
            )
            item = isolated_request(state, belief, effective.private.strategy, seed)
            baseline = reference_action(role, state, belief)
            delta = utility(role, item, advanced.action) - utility(role, item, baseline)
            tolerance = 0.001 * max(1, abs(utility(role, item, baseline)))
            key = (
                "advanced_wins"
                if delta > tolerance
                else "baseline_wins"
                if delta < -tolerance
                else "ties"
            )
            outcomes[key] += 1
        matrix[role.value] = outcomes
    return matrix


def latency_summary(values: list[float], fallbacks: int) -> dict[str, float | int]:
    """Summarize the latency distribution for the evidence document."""
    return {
        "p50": round(statistics.median(values), 3),
        "p95": round(percentile(values, 0.95), 3),
        "max": round(max(values), 3),
        "fallbacks": fallbacks,
    }
