import json

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.cli.app import main

pytestmark = pytest.mark.integration


def test_cli_style_caller_uses_public_sdk_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """REQ: FR-SDK-001."""
    sdk_payload = SimulationSdk().check_readiness().as_dict()
    assert main(["readiness", "--json"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload == sdk_payload
