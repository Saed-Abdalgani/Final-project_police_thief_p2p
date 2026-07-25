from pathlib import Path

import pytest

from scripts.validate_imports import find_forbidden_imports

pytestmark = pytest.mark.security


def test_protected_adapters_do_not_import_services_or_domain() -> None:
    """REQ: FR-SDK-002."""
    root = Path(__file__).parents[2]
    adapters = root / "src/police_thief_p2p/adapters"
    assert find_forbidden_imports(adapters) == []


def test_boundary_validator_detects_forbidden_import(tmp_path: Path) -> None:
    cli = tmp_path / "cli"
    cli.mkdir()
    (cli / "bad.py").write_text(
        "from police_thief_p2p.services import hidden\n",
        encoding="utf-8",
    )
    findings = find_forbidden_imports(tmp_path)
    assert len(findings) == 1
    assert findings[0].module == "police_thief_p2p.services"
