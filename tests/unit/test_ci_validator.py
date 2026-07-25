from pathlib import Path

from scripts.validate_ci import load_workflow, validate_workflow


def test_real_ci_workflow_has_required_platforms() -> None:
    root = Path(__file__).parents[2]
    workflow = load_workflow(root / ".github/workflows/ci.yml")
    assert validate_workflow(workflow) == []


def test_ci_validator_rejects_non_windows_quality_platforms() -> None:
    workflow: dict[str, object] = {
        "jobs": {
            "quality": {
                "strategy": {
                    "matrix": {
                        "os": ["ubuntu-latest"],
                        "python-version": ["3.12"],
                    }
                }
            },
            "macos-smoke": {"runs-on": "ubuntu-latest"},
        }
    }
    errors = validate_workflow(workflow)
    assert len(errors) == 3
