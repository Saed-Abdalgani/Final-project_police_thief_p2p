"""Generate exhaustive FR/NFR and Appendix E/F test mappings."""

import json
import re
from pathlib import Path

from scripts.validate_traceability import extract_requirement_ids

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_requirement_tests.json"
_ROW = re.compile(r"^\| ((?:E|F)-\d{3}) \|", re.MULTILINE)

_REQUIREMENT_TESTS: dict[str, tuple[str, ...]] = {
    "FR-SDK": ("tests/unit/test_sdk.py", "tests/security/test_import_boundaries.py"),
    "FR-CFG": (
        "tests/unit/test_config_models.py",
        "tests/property/test_configuration_properties.py",
    ),
    "FR-NEG": ("tests/unit/test_negotiation.py", "tests/integration/test_protocol_runtime.py"),
    "FR-GAME": (
        "tests/unit/test_domain_state_engine.py",
        "tests/property/test_domain_properties.py",
    ),
    "FR-BEL": (
        "tests/unit/test_hint_belief_service.py",
        "tests/property/test_belief_properties.py",
    ),
    "FR-STR": (
        "tests/unit/test_strategy_policies.py",
        "tests/property/test_strategy_properties.py",
    ),
    "FR-MCP": (
        "tests/contract/test_protocol_contracts.py",
        "tests/integration/test_dual_process_mcp.py",
    ),
    "FR-ORC": (
        "tests/integration/test_orchestrator_lifecycle.py",
        "tests/chaos/test_orchestration_faults.py",
    ),
    "FR-CRY": ("tests/unit/test_crypto_primitives.py", "tests/integration/test_mutual_audit.py"),
    "FR-ART": ("tests/unit/test_m9_artifacts_reporting.py",),
    "FR-UI": ("tests/unit/test_m10_live_view.py", "tests/integration/test_m10_replay_gui.py"),
    "FR-RPT": ("tests/integration/test_m9_outbox_gmail.py",),
    "FR-LGE": ("tests/unit/test_negotiation.py", "tests/unit/test_domain_schedule_scoring.py"),
    "NFR-REL": (
        "tests/chaos/test_orchestration_faults.py",
        "tests/integration/test_dual_process_mcp.py",
    ),
    "NFR-SEC": (
        "tests/security/test_mcp_boundaries.py",
        "tests/security/test_redaction_security.py",
    ),
    "NFR-MNT": (
        "tests/integration/test_quality_entrypoints.py",
        "tests/security/test_import_boundaries.py",
    ),
    "NFR-PERF": ("tests/performance/test_strategy_orchestration_performance.py",),
    "NFR-OBS": ("tests/unit/test_logging_redaction.py", "tests/unit/test_system_probes.py"),
    "NFR-REP": (
        "tests/contract/test_configuration_schemas.py",
        "tests/integration/test_sdk_readiness.py",
    ),
    "NFR-UX": ("tests/integration/test_m10_replay_gui.py",),
}


def appendix_tests(identifier: str) -> tuple[str, ...]:
    """Route one Appendix rule/parameter to its focused executable suite."""
    number = int(identifier.split("-")[1])
    if identifier.startswith("F-"):
        if number <= 15:
            return ("tests/unit/test_config_models.py", "tests/unit/test_coordinates_scent.py")
        if number <= 25:
            return ("tests/unit/test_domain_schedule_scoring.py",)
        return ("tests/unit/test_m9_gatekeeper.py", "tests/chaos/test_deadline_clock.py")
    if number <= 12:
        return (
            "tests/integration/test_protocol_runtime.py",
            "tests/chaos/test_orchestration_faults.py",
        )
    if number <= 16 or 46 <= number <= 48:
        return ("tests/unit/test_domain_state_engine.py", "tests/unit/test_domain_terminal.py")
    if number <= 24 or 36 <= number <= 38:
        return ("tests/integration/test_mutual_audit.py", "tests/unit/test_crypto_primitives.py")
    if number <= 27:
        return ("tests/unit/test_strategy_contracts.py",)
    if number <= 35 or number in {51, 54}:
        return ("tests/integration/test_m9_outbox_gmail.py", "tests/unit/test_m9_gatekeeper.py")
    return (
        "tests/security/test_import_boundaries.py",
        "tests/integration/test_repository_validators.py",
    )


def build_matrix(root: Path = ROOT) -> dict[str, object]:
    """Build complete exact-set mappings and report any missing test files."""
    prd = (root / "docs/PRD.md").read_text(encoding="utf-8")
    trace = (root / "docs/TRACEABILITY.md").read_text(encoding="utf-8")
    requirements = extract_requirement_ids(prd)
    appendix = _ROW.findall(trace)
    entries = []
    missing: list[str] = []
    for identifier in (*requirements, *appendix):
        prefix = identifier.rsplit("-", maxsplit=1)[0]
        tests = (
            _REQUIREMENT_TESTS[prefix]
            if prefix in _REQUIREMENT_TESTS
            else appendix_tests(identifier)
        )
        if any(not (root / path).is_file() for path in tests):
            missing.append(identifier)
        entries.append({"id": identifier, "tests": list(tests)})
    expected = len(requirements) == 227 and appendix == [
        *(f"E-{number:03d}" for number in range(1, 56)),
        *(f"F-{number:03d}" for number in range(1, 33)),
    ]
    return {
        "schema_version": "1.0.0",
        "package_version": "0.10.0",
        "summary": {
            "requirements": len(requirements),
            "appendix_e_rules": sum(item.startswith("E-") for item in appendix),
            "appendix_f_parameters": sum(item.startswith("F-") for item in appendix),
            "mapped_entries": len(entries),
            "result": "PASS" if expected and not missing else "FAIL",
        },
        "missing": missing,
        "entries": entries,
    }


def main() -> int:
    """Write the matrix and fail unless every normative identifier is mapped."""
    document = build_matrix()
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    summary = document["summary"]
    print(json.dumps(summary, sort_keys=True))
    return 0 if isinstance(summary, dict) and summary["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
