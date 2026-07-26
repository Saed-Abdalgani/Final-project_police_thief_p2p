import json
from pathlib import Path
from typing import cast

ROOT = Path(__file__).parents[2]
EVIDENCE = ROOT / "results/benchmarks"


def _load(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((EVIDENCE / name).read_text(encoding="utf-8")),
    )


def test_m11_measured_release_evidence_passes() -> None:
    performance = _load("m11_performance.json")
    soak = _load("m11_soak.json")
    gates = performance["gates"]
    assert isinstance(gates, dict)
    assert gates["result"] == "PASS"
    assert soak["result"] == "PASS"
    completed = soak["completed_sub_games"]
    assert isinstance(completed, int)
    assert completed >= 1_000
    assert soak["deadlocks"] == 0
    assert soak["retained_object_delta"] == 0


def test_m11_audits_are_complete_and_finding_free() -> None:
    assert _load("m11_security_audit.json")["result"] == "PASS"
    assert _load("m11_licenses.json")["result"] == "PASS"
    assert _load("m11_mutation.json")["result"] == "PASS"
    vulnerability = _load("m11_vulnerabilities.json")
    dependencies = vulnerability["dependencies"]
    assert isinstance(dependencies, list)
    assert dependencies
    assert all(not item["vulns"] for item in dependencies)


def test_m11_inventories_cover_every_declared_item() -> None:
    modules = _load("m11_module_inventory.json")["summary"]
    requirements = _load("m11_requirement_tests.json")["summary"]
    assert isinstance(modules, dict)
    assert modules["result"] == "PASS"
    assert requirements == {
        "requirements": 227,
        "appendix_e_rules": 55,
        "appendix_f_parameters": 32,
        "mapped_entries": 314,
        "result": "PASS",
    }
