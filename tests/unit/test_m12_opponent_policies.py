import pytest
from pydantic import ValidationError

from police_thief_p2p.domain import Role
from police_thief_p2p.services.experiments.hint_adversaries import HINT_ADVERSARIES
from police_thief_p2p.services.experiments.roster import ROSTER
from police_thief_p2p.services.strategy.contracts import HintVerdict
from police_thief_p2p.services.strategy.hint_profiles import (
    HintProfile,
    HintProfiledPoliceBrain,
    HintProfiledThiefBrain,
    lies_at,
    profiled_intent,
)
from police_thief_p2p.services.strategy.hints import configured_policy, realize_hint
from police_thief_p2p.services.strategy.random_policy import (
    RandomLegalPoliceBrain,
    RandomLegalThiefBrain,
)
from police_thief_p2p.services.strategy.reference import (
    ReferenceGreedyPoliceBrain,
    ReferenceGreedyThiefBrain,
)
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import HintPolicyConfig
from tests.helpers.strategy import request_for


def test_every_registered_policy_returns_a_legal_bounded_decision(
    shared_config: SharedConfig,
) -> None:
    for identifier, item in ROSTER.items():
        for role in Role:
            request = request_for(shared_config, role)
            decision = item.brain(role).decide(request)
            assert decision.action in request.legal_actions, f"{identifier}/{role}"
            assert len(decision.hint.split()) <= request.hint_max_words, identifier
            assert decision.reason_code


def test_policies_are_deterministic_for_one_seed(shared_config: SharedConfig) -> None:
    for item in ROSTER.values():
        for role in Role:
            first = item.brain(role).decide(request_for(shared_config, role, seed=31))
            second = item.brain(role).decide(request_for(shared_config, role, seed=31))
            assert first.action == second.action
            assert first.hint == second.hint


def test_reference_baseline_moves_toward_and_away_from_the_posterior_peak(
    shared_config: SharedConfig,
) -> None:
    police = ReferenceGreedyPoliceBrain().decide(request_for(shared_config, Role.POLICE))
    thief = ReferenceGreedyThiefBrain().decide(request_for(shared_config, Role.THIEF))
    assert police.reason_code.startswith("REFERENCE_GREEDY")
    assert thief.reason_code.startswith("REFERENCE_GREEDY")


def test_random_legal_baselines_only_ever_choose_offered_actions(
    shared_config: SharedConfig,
) -> None:
    for brain, role in (
        (RandomLegalPoliceBrain(), Role.POLICE),
        (RandomLegalThiefBrain(), Role.THIEF),
    ):
        for seed in range(6):
            request = request_for(shared_config, role, seed=seed)
            assert brain.decide(request).action in request.legal_actions


@pytest.mark.parametrize(
    ("profile", "step", "expected"),
    [
        (HintProfile.ALWAYS_HONEST, 0, False),
        (HintProfile.ALWAYS_HONEST, 40, False),
        (HintProfile.ALWAYS_LIE, 0, True),
        (HintProfile.PERIODIC_LIE, 0, True),
        (HintProfile.PERIODIC_LIE, 1, False),
        (HintProfile.PERIODIC_LIE, 3, True),
        (HintProfile.TRUST_SWITCH, 14, False),
        (HintProfile.TRUST_SWITCH, 15, True),
    ],
)
def test_hint_profiles_follow_their_declared_schedule(
    profile: HintProfile,
    step: int,
    expected: bool,
) -> None:
    assert lies_at(profile, step) is expected
    with pytest.raises(ValueError, match="non-negative"):
        lies_at(profile, -1)


def test_profiled_intent_inverts_only_the_claimed_region(
    shared_config: SharedConfig,
) -> None:
    request = request_for(shared_config, Role.THIEF)
    honest = profiled_intent(HintProfile.ALWAYS_HONEST, request)
    lying = profiled_intent(HintProfile.ALWAYS_LIE, request)
    assert honest.verdict is HintVerdict.TRUTH
    assert lying.verdict is HintVerdict.LIE
    assert honest.region is not lying.region


def test_hint_wrappers_keep_movement_and_change_only_the_hint(
    shared_config: SharedConfig,
) -> None:
    inner = ReferenceGreedyPoliceBrain()
    wrapped = HintProfiledPoliceBrain(inner, HintProfile.ALWAYS_LIE)
    plain = inner.decide(request_for(shared_config, Role.POLICE, seed=5))
    profiled = wrapped.decide(request_for(shared_config, Role.POLICE, seed=5))
    assert profiled.action == plain.action
    assert profiled.hint != plain.hint
    assert profiled.hint_intent.verdict is HintVerdict.LIE
    with pytest.raises(ValueError, match="keep the wrapped brain role"):
        HintProfiledThiefBrain(inner, HintProfile.ALWAYS_LIE)


def test_hint_adversaries_are_registered_for_both_roles() -> None:
    assert {item.opponent_id for item in HINT_ADVERSARIES} <= set(ROSTER)
    for item in HINT_ADVERSARIES:
        assert item.classification == "adversary"
        assert item.brain(Role.POLICE).role is Role.POLICE
        assert item.brain(Role.THIEF).role is Role.THIEF


def test_configured_hint_policy_respects_private_cadence_bounds() -> None:
    strict = configured_policy(HintPolicyConfig(trust_threshold=1.0))
    permissive = configured_policy(HintPolicyConfig(trust_threshold=0.2))
    assert strict.trust_threshold == 1.0
    assert permissive.trust_threshold == 0.2
    with pytest.raises(ValidationError, match="trust_threshold"):
        HintPolicyConfig(trust_threshold=1.5)
    with pytest.raises(ValidationError, match="max_consecutive_lies"):
        HintPolicyConfig(max_consecutive_lies=99)


def test_template_variants_are_distinct_and_bounded(shared_config: SharedConfig) -> None:
    request = request_for(shared_config, Role.THIEF)
    intent = profiled_intent(HintProfile.ALWAYS_HONEST, request)
    first = realize_hint(intent, request.map_area, request.hint_max_words, 0)
    second = realize_hint(intent, request.map_area, request.hint_max_words, 1)
    assert first != second
    assert len(second.split()) <= request.hint_max_words
    with pytest.raises(ValueError, match="template variant"):
        realize_hint(intent, request.map_area, request.hint_max_words, 2)
