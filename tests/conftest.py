"""Deterministic shared pytest and Hypothesis configuration."""

from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings

from police_thief_p2p.shared.config_loader import load_shared_bytes
from police_thief_p2p.shared.config_models import SharedConfig

settings.register_profile(
    "ci",
    deadline=None,
    derandomize=True,
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
settings.load_profile("ci")

PROJECT_ROOT = Path(__file__).parents[1]


@pytest.fixture
def shared_config_bytes() -> bytes:
    """Return the complete binding shared configuration example."""
    return (PROJECT_ROOT / "config/shared/game.example.json").read_bytes()


@pytest.fixture
def private_config_bytes() -> bytes:
    """Return the complete safe private configuration example."""
    return (PROJECT_ROOT / "config/private/game.example.toml").read_bytes()


@pytest.fixture
def shared_config(shared_config_bytes: bytes) -> SharedConfig:
    """Return the validated shared configuration example."""
    return load_shared_bytes(shared_config_bytes)
