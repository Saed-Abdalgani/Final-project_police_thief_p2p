import json

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.cli.app import build_parser, main
from police_thief_p2p.sdk.dto import ReadinessStatus
from police_thief_p2p.sdk.errors import (
    DependencyUnavailableError,
    ErrorCode,
    InvalidInputError,
)


def test_sdk_readiness_is_typed_and_serializable() -> None:
    report = SimulationSdk().check_readiness()
    payload = report.as_dict()

    assert report.status is ReadinessStatus.READY
    assert report.is_ready
    assert payload["status"] == "READY"
    assert payload["checks"] == [
        {
            "name": "sdk.import",
            "passed": True,
            "detail": "Typed SimulationSdk foundation is importable.",
        }
    ]


def test_cli_json_calls_sdk_and_returns_safe_payload(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["readiness", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "READY"
    assert payload["package_version"] == "0.1.0"


def test_cli_human_output_and_parser(capsys: pytest.CaptureFixture[str]) -> None:
    assert build_parser().prog == "police-thief-p2p"
    assert main(["readiness"]) == 0
    assert "READY: package 0.1.0" in capsys.readouterr().out


def test_typed_errors_serialize_and_repr_only_safe_fields() -> None:
    error = InvalidInputError("request rejected", correlation_id="correlation-1")
    assert error.code is ErrorCode.INVALID_INPUT
    assert str(error) == "request rejected"
    assert error.as_dict() == {
        "code": "INVALID_INPUT",
        "message": "request rejected",
        "correlation_id": "correlation-1",
    }
    assert "request rejected" in repr(error)


def test_dependency_error_has_stable_code() -> None:
    error = DependencyUnavailableError("provider unavailable")
    assert error.code is ErrorCode.DEPENDENCY_UNAVAILABLE
    assert error.as_dict()["correlation_id"] is None
