import json

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.cli.app import build_parser, main
from police_thief_p2p.sdk import Action, Role, SubGameOutcome, TerminalReason
from police_thief_p2p.sdk.dto import ReadinessStatus
from police_thief_p2p.sdk.errors import (
    DependencyUnavailableError,
    ErrorCode,
    InvalidInputError,
)
from police_thief_p2p.shared.config_models import SharedConfig


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
            "detail": "Packaged schemas match schema 0.2.0 and protocol 0.7.0.",
        },
    ]


def test_cli_json_calls_sdk_and_returns_safe_payload(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["readiness", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "READY"
    assert payload["package_version"] == "0.10.0"


def test_cli_human_output_and_parser(capsys: pytest.CaptureFixture[str]) -> None:
    assert build_parser().prog == "police-thief-p2p"
    assert main(["readiness"]) == 0
    output = capsys.readouterr().out
    assert "READY: package 0.10.0" in output
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


def test_sdk_exposes_domain_transition_schedule_and_scoring(
    shared_config: SharedConfig,
) -> None:
    sdk = SimulationSdk()
    state = sdk.create_local_game(shared_config, Role.POLICE)
    legal = sdk.legal_actions(state)
    stayed = sdk.apply_action(state, Action.stay())
    assert Action.stay() in legal
    assert stayed.state.step_number == 1

    schedule = sdk.create_role_schedule("ATEAM001", "BTEAM002")
    outcomes = tuple(
        SubGameOutcome.from_terminal(
            int(assignment.sub_game_number),
            assignment.police_group,
            assignment.thief_group,
            TerminalReason.CAPTURE,
            shared_config.scoring,
        )
        for assignment in schedule
    )
    score = sdk.aggregate_series_score(
        outcomes,
        "ATEAM001",
        "BTEAM002",
    )
    assert score.winner is None


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
