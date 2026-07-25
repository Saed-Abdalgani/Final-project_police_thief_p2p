"""Structurally validate the required GitHub Actions platform matrix."""

from collections.abc import Mapping
from pathlib import Path
from typing import cast

import yaml


def load_workflow(path: Path) -> Mapping[str, object]:
    """Safely load a workflow document."""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        msg = "workflow root must be a mapping"
        raise ValueError(msg)
    return cast("Mapping[str, object]", loaded)


def _mapping(value: object, label: str) -> Mapping[str, object]:
    """Return a checked mapping."""
    if not isinstance(value, Mapping):
        msg = f"{label} must be a mapping"
        raise ValueError(msg)
    return cast("Mapping[str, object]", value)


def validate_workflow(workflow: Mapping[str, object]) -> list[str]:
    """Return missing matrix/platform requirements."""
    errors: list[str] = []
    jobs = _mapping(workflow.get("jobs"), "jobs")
    quality = _mapping(jobs.get("quality"), "jobs.quality")
    strategy = _mapping(quality.get("strategy"), "jobs.quality.strategy")
    matrix = _mapping(strategy.get("matrix"), "jobs.quality.strategy.matrix")
    operating_systems = matrix.get("os")
    python_versions = matrix.get("python-version")
    if operating_systems != ["windows-latest"]:
        errors.append("quality matrix must contain only windows-latest")
    if not isinstance(python_versions, list) or "3.13" not in python_versions:
        errors.append("quality matrix must include Python 3.13")
    macos = _mapping(jobs.get("macos-smoke"), "jobs.macos-smoke")
    if macos.get("runs-on") != "macos-latest":
        errors.append("macos-smoke must run on macos-latest")
    return errors


def main() -> int:
    """Validate the repository workflow and return a shell-friendly status."""
    errors = validate_workflow(load_workflow(Path(".github/workflows/ci.yml")))
    for error in errors:
        print(error)
    if errors:
        return 1
    print("CI workflow OK: Windows matrix and macOS smoke job are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
