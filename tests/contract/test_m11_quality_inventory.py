import inspect
from pathlib import Path

import police_thief_p2p
import police_thief_p2p.sdk as sdk
from scripts.m11_inventory import build_inventory
from scripts.m11_trace_matrix import build_matrix

ROOT = Path(__file__).parents[2]


def test_every_source_module_has_direct_tests_and_documented_public_callables() -> None:
    inventory = build_inventory(ROOT)
    summary = inventory["summary"]
    assert isinstance(summary, dict)
    assert summary["source_modules"] == summary["mapped_modules"]
    assert summary["public_callables"] >= 800
    assert summary["undocumented_public_callables"] == 0
    assert summary["result"] == "PASS"
    assert inventory["unmapped"] == []
    assert inventory["undocumented"] == []


def test_every_normative_requirement_and_appendix_rule_has_executable_tests() -> None:
    matrix = build_matrix(ROOT)
    summary = matrix["summary"]
    assert isinstance(summary, dict)
    assert summary == {
        "requirements": 227,
        "appendix_e_rules": 55,
        "appendix_f_parameters": 32,
        "mapped_entries": 314,
        "result": "PASS",
    }
    assert matrix["missing"] == []
    entries = matrix["entries"]
    assert isinstance(entries, list)
    assert all(item["tests"] for item in entries)


def test_versioned_package_and_sdk_public_surfaces_are_documented() -> None:
    checked = 0
    for module in (police_thief_p2p, sdk):
        public_names = getattr(module, "__all__", tuple(vars(module)))
        for name in public_names:
            value = getattr(module, name)
            if name.startswith("_") or not callable(value):
                continue
            assert inspect.getdoc(value), f"public API lacks docstring: {module.__name__}.{name}"
            checked += 1
    assert checked >= 70
