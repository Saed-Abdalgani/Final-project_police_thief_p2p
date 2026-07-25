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
        },
        {
            "name": "config.contracts",
            "passed": True,
            "detail": "Packaged schemas match schema/protocol 0.2.0.",
        },
    ]


def test_cli_json_calls_sdk_and_returns_safe_payload(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["readiness", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "READY"
    assert payload["package_version"] == "0.2.0"


def test_cli_human_output_and_parser(capsys: pytest.CaptureFixture[str]) -> None:
    assert build_parser().prog == "police-thief-p2p"
    assert main(["readiness"]) == 0
    output = capsys.readouterr().out
    assert "READY: package 0.2.0" in output
    assert "config.contracts: PASS" in output


def test_sdk_loads_effective_configuration(
    shared_config_bytes: bytes,
    private_config_bytes: bytes,
) -> None:
    effective = SimulationSdk().load_configuration(
        shared_config_bytes,
        private_config_bytes,
        submission_mode=True,
    )
    assert effective.shared.schema_version == "0.2.0"
    assert effective.private.identity.group_id == "GRP00001"


def test_sdk_submission_mode_validates_private_identity(
    shared_config_bytes: bytes,
    private_config_bytes: bytes,
) -> None:
    invalid_private = private_config_bytes.replace(b"GRP00001", b"team-one")
    with pytest.raises(ValueError, match="eight ASCII"):
        SimulationSdk().load_configuration(
            shared_config_bytes,
            invalid_private,
            submission_mode=True,
        )


def test_sdk_reports_contract_drift_as_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "police_thief_p2p.sdk.facade.contracts_are_compatible",
        lambda _schema, _protocol: False,
    )
    report = SimulationSdk().check_readiness()
    assert report.status is ReadinessStatus.NOT_READY
    assert not report.is_ready
    assert report.checks[-1].detail == "Packaged schema compatibility mismatch."


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
