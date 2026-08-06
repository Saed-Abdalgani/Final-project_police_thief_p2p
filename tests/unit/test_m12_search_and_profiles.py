from collections.abc import Mapping

import pytest

from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE
from police_thief_p2p.services.experiments.memory_probe import peak_rss_mb
from police_thief_p2p.services.experiments.profiles import (
    derive_pair,
    derive_profile,
    profile_digest,
    split_point,
    with_decision_budget,
)
from police_thief_p2p.services.experiments.resources import (
    ResourceLedger,
    host_facts,
    measure,
)
from police_thief_p2p.services.experiments.spaces import (
    BELIEF_SPACE,
    Dimension,
    clamp_point,
    sample_point,
    space,
    space_document,
    strategy_dimensions,
)
from police_thief_p2p.services.experiments.surrogate import Surrogate, surrogate_search
from police_thief_p2p.services.experiments.tuning import (
    FULL_STAGE,
    SCREENING_STAGE,
    TrialResult,
    random_search,
    screening_threshold,
)
from tests.helpers.strategy import strategy_config


def _linear_objective(point: Mapping[str, float | int], stage: int) -> TrialResult:
    value = float(point["police.distance"]) + (1.0 if stage == FULL_STAGE else 0.0)
    return TrialResult(value, 50.0 + value, True, 100.0, 4)


def _failing_objective(point: Mapping[str, float | int], stage: int) -> TrialResult:
    return TrialResult(1.0, 51.0, False, 400.0, 4)


def test_every_declared_space_is_bounded_and_serializable() -> None:
    document = space_document()
    assert set(document) == {"police", "thief", "belief", "hint"}
    for name in document:
        for item in space(name):
            assert item.low <= item.high
    with pytest.raises(KeyError, match="unknown search space"):
        space("nope")
    with pytest.raises(ValueError, match="inverted bounds"):
        Dimension("bad", 1.0, 0.0)
    with pytest.raises(ValueError, match="integral bounds"):
        Dimension("bad", 0.5, 2.5, integer=True)


def test_sampling_and_clamping_stay_inside_declared_bounds() -> None:
    dimensions = strategy_dimensions()
    point = sample_point(dimensions, DeterministicRandomSource(5))
    index = {item.name: item for item in dimensions}
    for name, value in point.items():
        assert index[name].low <= value <= index[name].high
        if index[name].integer:
            assert isinstance(value, int)
    clamped = clamp_point(dimensions, {"police.distance": 10_000.0, "unknown": 1.0})
    assert clamped == {"police.distance": index["police.distance"].high}


def test_derived_profiles_revalidate_and_keep_a_guard_margin() -> None:
    base = strategy_config()
    derived = derive_profile(base, {"police.distance": 6.5, "hints.trust_threshold": 0.8})
    assert derived.police.distance == 6.5
    assert derived.hints.trust_threshold == 0.8
    assert profile_digest(derived) != profile_digest(base)
    budgeted = with_decision_budget(base, 40)
    assert budgeted.decision_budget_ms == 40
    assert budgeted.guard_margin_ms < budgeted.decision_budget_ms
    with pytest.raises(KeyError, match="unknown strategy weight"):
        derive_profile(base, {"police.nonexistent": 1.0})
    with pytest.raises(KeyError, match="unknown strategy field"):
        derive_profile(base, {"nonexistent": 1.0})


def test_search_points_split_into_strategy_and_belief_halves() -> None:
    point = {"police.distance": 4.0, "chase": 0.4, "recency": 0.8}
    strategy, belief = split_point(point)
    assert strategy == {"police.distance": 4.0}
    assert belief == {"chase": 0.4, "recency": 0.8}
    derived, profile = derive_pair(strategy_config(), point, DEFAULT_BELIEF_PROFILE)
    assert derived.police.distance == 4.0
    assert profile.chase == 0.4
    assert profile.evade == DEFAULT_BELIEF_PROFILE.evade


def test_random_search_persists_every_trial_and_stops_inferior_ones() -> None:
    dimensions = (Dimension("police.distance", 1.0, 20.0),)
    outcome = random_search(dimensions, _linear_objective, DeterministicRandomSource(21), trials=10)
    assert len(outcome.trials) == 10
    assert any(not item.completed for item in outcome.trials)
    assert all(item.stop_reason for item in outcome.trials)
    assert outcome.best.completed
    document = outcome.as_document()
    assert document["attempted"] == 10
    assert document["stopped_early"] == 10 - int(str(document["completed"]))
    with pytest.raises(ValueError, match="at least one trial"):
        random_search(dimensions, _linear_objective, DeterministicRandomSource(1), trials=0)


def test_reliability_failures_stop_a_trial_before_the_full_stage() -> None:
    outcome = random_search(
        (Dimension("police.distance", 1.0, 2.0),),
        _failing_objective,
        DeterministicRandomSource(4),
        trials=3,
    )
    assert all(item.stop_reason == "RELIABILITY_GATE" for item in outcome.trials)
    assert not outcome.eligible
    assert outcome.best.screening.objective == 1.0


def test_screening_threshold_needs_history_before_it_prunes() -> None:
    assert screening_threshold([1.0, 2.0]) is None
    assert screening_threshold([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert int(SCREENING_STAGE) < int(FULL_STAGE)


def test_surrogate_refinement_reuses_prior_trials_and_stays_bounded() -> None:
    dimensions = (Dimension("police.distance", 1.0, 20.0),)
    rng = DeterministicRandomSource(77)
    broad = random_search(dimensions, _linear_objective, rng, trials=6)
    refined = surrogate_search(
        dimensions, _linear_objective, rng, trials=4, prior=broad.trials, first_id=6, pool=8
    )
    assert [item.trial_id for item in refined.trials] == [6, 7, 8, 9]
    assert refined.method == "surrogate"
    assert refined.best.objective >= 1.0
    with pytest.raises(ValueError, match="candidate pool"):
        surrogate_search(dimensions, _linear_objective, rng, trials=1, pool=0)


def test_surrogate_prefers_regions_with_higher_observed_objectives() -> None:
    surrogate = Surrogate(((0.0,), (1.0,)), (0.0, 10.0))
    assert surrogate.acquisition((0.95,)) > surrogate.acquisition((0.05,))
    assert Surrogate((), ()).acquisition((0.5,)) == 0.0
    with pytest.raises(ValueError, match="one objective per observed point"):
        Surrogate(((0.0,),), ())
    assert BELIEF_SPACE[0].name == "chase"


def test_objective_stage_constants_change_the_measured_value() -> None:
    screening = _linear_objective({"police.distance": 3.0}, SCREENING_STAGE)
    full = _linear_objective({"police.distance": 3.0}, FULL_STAGE)
    assert full.objective > screening.objective


def test_every_campaign_records_host_runtime_traffic_and_token_cost() -> None:
    with measure() as ledger:
        ledger.record_call(2_048, 12.5)
        ledger.record_call(1_024, 30.0)
        ledger.record_tokens(120, 45)
        _ = [object() for _ in range(20_000)]
    document = ledger.usage().as_document()
    assert document["calls"] == 2
    assert document["payload_bytes"] == 3_072
    assert document["prompt_tokens"] == 120
    assert document["completion_tokens"] == 45
    assert document["max_call_latency_ms"] == 30.0
    assert float(str(document["wall_time_sec"])) >= 0.0
    assert float(str(document["peak_rss_mb"])) > 0.0
    host = document["host"]
    assert isinstance(host, dict)
    assert set(host) == {"platform", "processor", "cpu_count", "python", "implementation"}


def test_resource_ledgers_reject_impossible_measurements() -> None:
    ledger = ResourceLedger()
    with pytest.raises(ValueError, match="non-negative"):
        ledger.record_call(-1, 1.0)
    with pytest.raises(ValueError, match="non-negative"):
        ledger.record_call(1, -1.0)
    with pytest.raises(ValueError, match="non-negative"):
        ledger.record_tokens(-1, 0)
    assert ledger.usage().max_call_latency_ms == 0.0
    assert int(str(host_facts()["cpu_count"])) >= 1
    assert peak_rss_mb() > 0.0
