from dataclasses import replace
from typing import cast

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import ActionType, Role
from police_thief_p2p.services.belief import BeliefGrid
from police_thief_p2p.services.strategy.baseline import (
    PoliceBaselineBrain,
    ThiefBaselineBrain,
)
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.police import AdvancedPoliceBrain
from police_thief_p2p.services.strategy.request import StrategyRequest
from police_thief_p2p.services.strategy.resolver import StrategyResolver
from police_thief_p2p.services.strategy.service import StrategyService
from police_thief_p2p.services.strategy.thief import AdvancedThiefBrain
from police_thief_p2p.shared.config_loader import load_private_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig
from tests.helpers.strategy import point_belief, request_for


def test_posterior_baselines_use_full_distribution_and_never_illegal(
    shared_config: SharedConfig,
) -> None:
    police = request_for(shared_config, Role.POLICE)
    p_decision = PoliceBaselineBrain().decide(police)
    assert p_decision.action in police.legal_actions
    assert p_decision.reason_code == "POLICE_EXPECTED_DISTANCE"

    thief = request_for(shared_config, Role.THIEF)
    t_decision = ThiefBaselineBrain().decide(thief)
    assert t_decision.action in thief.legal_actions
    assert t_decision.action.action_type is not ActionType.BARRIER
    assert t_decision.reason_code == "THIEF_RISK_QUANTILE"


def test_advanced_police_prioritizes_proven_capture_and_avoids_self_barrier(
    shared_config: SharedConfig,
) -> None:
    base = request_for(shared_config, Role.POLICE)
    belief = point_belief(base.state, 0, 1)
    request = replace(base, belief=belief, rng=DeterministicRandomSource(3))
    decision = AdvancedPoliceBrain().decide(request)
    assert decision.reason_code == "POLICE_PROVEN_CAPTURE"
    assert decision.action.action_type in {ActionType.MOVE, ActionType.BARRIER}
    if decision.action.action_type is ActionType.BARRIER:
        assert decision.action.target != request.state.position
    assert dict(decision.metrics.score.features)["PROVEN_CAPTURE"] > 0


def test_advanced_thief_is_deterministic_by_seed_and_never_barriers(
    shared_config: SharedConfig,
) -> None:
    first = AdvancedThiefBrain().decide(request_for(shared_config, Role.THIEF, seed=19))
    second = AdvancedThiefBrain().decide(request_for(shared_config, Role.THIEF, seed=19))
    assert first.action == second.action
    assert first.hint_intent == second.hint_intent
    assert first.action.action_type is not ActionType.BARRIER
    assert first.metrics.completed_depth >= 1
    features = dict(first.metrics.score.features)
    assert {"RISK_DISTANCE", "SPACE", "ROUTES", "TRAPS", "SCENT"} <= features.keys()


class _BrokenBrain(StrategyBrain):
    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        raise RuntimeError("private strategy failure")


class _InvalidBrain(StrategyBrain):
    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        return cast(Decision, object())


class _Resolver(StrategyResolver):
    def __init__(self, brain: StrategyBrain) -> None:
        self.brain = brain

    def resolve(self, role: Role, config: StrategyConfig) -> StrategyBrain:
        del role, config
        return self.brain


@pytest.mark.parametrize(
    ("brain", "reason"),
    [(_BrokenBrain(), "FALLBACK_EXCEPTION"), (_InvalidBrain(), "FALLBACK_INVALID")],
)
def test_service_falls_back_for_exception_or_malicious_output(
    shared_config: SharedConfig,
    brain: StrategyBrain,
    reason: str,
) -> None:
    request = request_for(shared_config, Role.POLICE)
    decision = StrategyService(_Resolver(brain)).decide(
        request.state,
        request.belief,
        request.config,
        clock=request.clock,
        rng=request.rng,
    )
    assert decision.fallback_used
    assert decision.reason_code == reason
    assert decision.action in request.legal_actions


def test_service_fake_clock_deadline_returns_fast_legal_fallback(
    shared_config: SharedConfig,
) -> None:
    request = request_for(shared_config, Role.POLICE)
    decision = StrategyService().decide(
        request.state,
        request.belief,
        request.config,
        clock=request.clock,
        rng=request.rng,
        deadline=request.clock.monotonic(),
    )
    assert decision.reason_code == "FALLBACK_DEADLINE"
    assert decision.metrics.latency_ms == 0


def test_resolver_enforces_namespace_subclass_and_role(
    private_config_bytes: bytes,
) -> None:
    config = load_private_bytes(private_config_bytes).strategy
    assert isinstance(StrategyResolver().resolve(Role.POLICE, config), AdvancedPoliceBrain)
    mismatch = config.model_copy(update={"police_class": config.thief_class})
    with pytest.raises(ValueError, match="role"):
        StrategyResolver().resolve(Role.POLICE, mismatch)
    not_brain = config.model_copy(
        update={"police_class": ("police_thief_p2p.services.strategy.contracts.Decision")}
    )
    with pytest.raises(ValueError, match="subclass"):
        StrategyResolver().resolve(Role.POLICE, not_brain)


def test_sdk_places_strategy_between_belief_and_commitment(
    shared_config_bytes: bytes,
    private_config_bytes: bytes,
) -> None:
    sdk = SimulationSdk()
    effective = sdk.load_configuration(
        shared_config_bytes, private_config_bytes, submission_mode=True
    )
    state = sdk.create_local_game(effective.shared, Role.THIEF)
    belief = BeliefGrid.uniform(state.rules.board)
    first = sdk.choose_strategy_action(state, belief, effective, clock=FakeClock())
    second = sdk.choose_strategy_action(state, belief, effective, clock=FakeClock())
    fields = sdk.strategy_commitment_fields(first)
    assert first.action == second.action
    assert fields.action.action_type == first.action.action_type
    assert fields.verdict == first.hint_intent.verdict.value
    assert fields.hint_semantic_intent == first.hint_intent.region.value
    assert fields.hint == first.hint
