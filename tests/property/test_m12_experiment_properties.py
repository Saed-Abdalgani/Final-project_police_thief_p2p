import pytest
from hypothesis import given
from hypothesis import strategies as st

from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE
from police_thief_p2p.services.experiments.manifest import (
    CandidateFreeze,
    ReproducibilityManifest,
    runtime_facts,
)
from police_thief_p2p.services.experiments.profiles import derive_pair, profile_digest
from police_thief_p2p.services.experiments.resources import ResourceLedger
from police_thief_p2p.services.experiments.spaces import (
    clamp_point,
    sample_point,
    space_document,
    strategy_dimensions,
)
from police_thief_p2p.services.experiments.statistics import bootstrap_interval, percentile
from tests.helpers.strategy import strategy_config

pytestmark = pytest.mark.property


@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
def test_any_sampled_point_produces_a_valid_revalidated_profile(seed: int) -> None:
    dimensions = strategy_dimensions()
    point = sample_point(dimensions, DeterministicRandomSource(seed))
    strategy, belief = derive_pair(strategy_config(), point, DEFAULT_BELIEF_PROFILE)
    assert strategy.guard_margin_ms < strategy.decision_budget_ms
    assert 1 <= strategy.search_horizon <= 8
    assert 0.0 <= strategy.hints.trust_threshold <= 1.0
    assert belief == DEFAULT_BELIEF_PROFILE
    assert len(profile_digest(strategy)) == 64


@given(
    values=st.lists(
        st.floats(min_value=-1_000, max_value=1_000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=25,
    )
)
def test_percentiles_are_monotone_and_inside_the_sample_range(values: list[float]) -> None:
    assert percentile(values, 0.0) == min(values)
    assert percentile(values, 1.0) == max(values)
    assert percentile(values, 0.25) <= percentile(values, 0.75)


@given(
    values=st.lists(
        st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=12,
    ),
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_bootstrap_intervals_never_leave_the_observed_support(
    values: list[float],
    seed: int,
) -> None:
    interval = bootstrap_interval(values, DeterministicRandomSource(seed), resamples=60)
    assert min(values) <= interval.lower <= interval.upper <= max(values)
    assert min(values) <= interval.mean <= max(values)


@given(
    overrides=st.dictionaries(
        st.sampled_from([item.name for item in strategy_dimensions()]),
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        max_size=6,
    )
)
def test_clamping_always_lands_inside_declared_bounds(overrides: dict[str, float]) -> None:
    dimensions = strategy_dimensions()
    index = {item.name: item for item in dimensions}
    for name, value in clamp_point(dimensions, overrides).items():
        assert index[name].low <= value <= index[name].high


@given(objective=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False))
def test_manifests_are_reproducible_and_refuse_holdout_selection(objective: float) -> None:
    freeze = CandidateFreeze(
        candidate_id="candidate-advanced",
        strategy=strategy_config(),
        belief=DEFAULT_BELIEF_PROFILE,
        selection_split="train",
        selection_objective=objective,
        trial_id=3,
    )
    manifest = ReproducibilityManifest(
        campaign_id="p",
        commit_sha="a" * 40,
        split="train",
        freeze=freeze,
        metrics={"share": "60"},
    )
    measured = ReproducibilityManifest(
        campaign_id="p",
        commit_sha="a" * 40,
        split="train",
        freeze=freeze,
        metrics={"share": "60"},
        resources=ResourceLedger().usage(),
    )
    assert manifest.digest() == manifest.digest() == measured.digest()
    assert manifest.as_document()["resources"] is None
    assert measured.as_document()["resources"] is not None
    assert len(freeze.digest()) == 64
    assert set(runtime_facts()) == {"python", "implementation", "platform", "machine"}
    assert manifest.as_document()["candidate_freeze_sha256"] == freeze.digest()
    with pytest.raises(ValueError, match="holdout"):
        CandidateFreeze(
            candidate_id="c",
            strategy=strategy_config(),
            belief=DEFAULT_BELIEF_PROFILE,
            selection_split="holdout",
            selection_objective=objective,
            trial_id=1,
        )


def test_every_space_dimension_is_documented_once() -> None:
    document = space_document()
    names = [item["name"] for values in document.values() for item in values]
    assert len(names) == len(set(names))
