"""Deterministic shared pytest and Hypothesis configuration."""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "ci",
    deadline=None,
    derandomize=True,
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
settings.load_profile("ci")
