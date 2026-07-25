import tomllib
from pathlib import Path

import pytest

from police_thief_p2p import __version__
from police_thief_p2p.shared.version import (
    PACKAGE_VERSION,
    PROTOCOL_VERSION,
    SCHEMA_VERSION,
    VersionInfo,
    current_versions,
    is_semantic_version,
)


@pytest.mark.parametrize(
    "value",
    ["0.1.0", "1.0.0-alpha.1", "2.4.6+build.9"],
)
def test_semantic_versions_are_accepted(value: str) -> None:
    assert is_semantic_version(value)


@pytest.mark.parametrize("value", ["1", "1.0", "01.0.0", "v1.0.0", "1.0.0.0"])
def test_invalid_semantic_versions_are_rejected(value: str) -> None:
    assert not is_semantic_version(value)


def test_version_info_rejects_invalid_fields() -> None:
    with pytest.raises(ValueError, match="protocol"):
        VersionInfo(package="1.0.0", protocol="invalid", schema="1.0.0")


def test_current_versions_are_valid_and_public_version_matches() -> None:
    versions = current_versions()
    assert versions == VersionInfo(
        package=PACKAGE_VERSION,
        protocol=PROTOCOL_VERSION,
        schema=SCHEMA_VERSION,
    )
    assert __version__ == PACKAGE_VERSION


def test_package_version_matches_pyproject() -> None:
    root = Path(__file__).parents[2]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == PACKAGE_VERSION
    assert pyproject["project"]["requires-python"] == ">=3.13"
