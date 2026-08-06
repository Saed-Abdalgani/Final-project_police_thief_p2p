import pytest

from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.experiments.gate_result import GateReport, GateResult
from police_thief_p2p.services.experiments.generalization import (
    interval_beats,
    overfitting_gate,
    robustness_gate,
)
from police_thief_p2p.services.experiments.statistics import (
    bootstrap_interval,
    bradley_terry_strengths,
    elo_ratings,
    paired_difference_interval,
    percentile,
)


def test_percentile_is_deterministic_nearest_rank() -> None:
    values = [4.0, 1.0, 3.0, 2.0]
    assert percentile(values, 0.0) == 1.0
    assert percentile(values, 0.5) == 2.0
    assert percentile(values, 1.0) == 4.0
    with pytest.raises(ValueError, match="at least one value"):
        percentile([], 0.5)
    with pytest.raises(ValueError, match="must be in"):
        percentile(values, 1.5)


def test_bootstrap_interval_brackets_the_mean_and_is_reproducible() -> None:
    values = [10.0, 20.0, 20.0, 10.0, 20.0, 10.0]
    first = bootstrap_interval(values, DeterministicRandomSource(11), resamples=200)
    second = bootstrap_interval(values, DeterministicRandomSource(11), resamples=200)
    assert first == second
    assert first.lower <= first.mean <= first.upper
    assert first.samples == len(values)


def test_paired_interval_detects_a_real_positive_uplift() -> None:
    candidate = [20.0] * 8
    baseline = [5.0] * 8
    interval = paired_difference_interval(
        candidate, baseline, DeterministicRandomSource(3), resamples=200
    )
    assert interval.lower == interval.upper == 15.0
    assert interval_beats(interval, 0.0)
    with pytest.raises(ValueError, match="equal-length"):
        paired_difference_interval([1.0], [1.0, 2.0], DeterministicRandomSource(3))


def test_ranking_orders_a_dominant_competitor_above_a_losing_one() -> None:
    wins = {("alpha", "beta"): 9, ("beta", "alpha"): 1}
    strengths = bradley_terry_strengths(wins, ["alpha", "beta"])
    assert strengths["alpha"] > strengths["beta"]
    ratings = elo_ratings(wins, ["alpha", "beta"])
    assert ratings["alpha"] > 1_500.0 > ratings["beta"]


def test_generalization_and_robustness_gates_reject_material_regression() -> None:
    assert overfitting_gate(70.0, 68.0).passed
    assert not overfitting_gate(90.0, 60.0).passed
    assert robustness_gate([72.0, 61.0]).passed
    assert not robustness_gate([72.0, 41.0]).passed
    with pytest.raises(ValueError, match="at least one measured case"):
        robustness_gate([])


def test_gate_report_aggregates_failures_and_requires_documentation() -> None:
    good = GateResult("G1", "must hold", 1.0, True)
    bad = GateResult("G2", "must also hold", 0.0, False)
    report = GateReport((good, bad))
    assert not report.passed
    assert report.failures == ("G2",)
    assert report.as_document()["failures"] == ["G2"]
    assert good.as_document()["measured"] == 1.0
    with pytest.raises(ValueError, match="at least one gate"):
        GateReport(())
    with pytest.raises(ValueError, match="stated requirement"):
        GateResult("", "", 0, True)
