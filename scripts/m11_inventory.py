"""Generate the complete source-module, public-API, and direct-test inventory."""

import ast
import json
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_module_inventory.json"

_ROUTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("adapters/cli", ("tests/unit/test_sdk.py", "tests/integration/test_m10_replay_gui.py")),
    ("adapters/email", ("tests/integration/test_m9_outbox_gmail.py",)),
    ("adapters/gui", ("tests/integration/test_m10_replay_gui.py",)),
    ("adapters/mcp", ("tests/integration/test_dual_process_mcp.py",)),
    ("adapters/persistence", ("tests/unit/test_atomic_repository.py",)),
    ("adapters/system", ("tests/unit/test_system_probes.py", "tests/unit/test_clocks.py")),
    (
        "domain",
        ("tests/unit/test_domain_state_engine.py", "tests/property/test_domain_properties.py"),
    ),
    ("sdk", ("tests/unit/test_sdk.py", "tests/integration/test_sdk_readiness.py")),
    ("services/artifacts", ("tests/unit/test_m9_artifacts_reporting.py",)),
    ("services/audit", ("tests/integration/test_mutual_audit.py",)),
    (
        "services/belief",
        ("tests/unit/test_hint_belief_service.py", "tests/property/test_belief_properties.py"),
    ),
    (
        "services/crypto",
        ("tests/unit/test_crypto_primitives.py", "tests/integration/test_mutual_audit.py"),
    ),
    ("services/gatekeeper", ("tests/unit/test_m9_gatekeeper.py",)),
    ("services/orchestration", ("tests/chaos/test_orchestration_faults.py",)),
    ("services/ports", ("tests/contract/test_ports.py",)),
    ("services/protocol", ("tests/integration/test_protocol_runtime.py",)),
    ("services/replay", ("tests/unit/test_m10_replay.py",)),
    ("services/reporting", ("tests/integration/test_m9_outbox_gmail.py",)),
    (
        "services/strategy",
        ("tests/unit/test_strategy_policies.py", "tests/property/test_strategy_properties.py"),
    ),
    ("shared", ("tests/unit/test_config_models.py", "tests/unit/test_canonical_json.py")),
    ("adapters", ("tests/security/test_import_boundaries.py",)),
    ("services", ("tests/unit/test_sdk.py",)),
    ("schemas", ("tests/contract/test_configuration_schemas.py",)),
    ("constants.py", ("tests/unit/test_constants.py",)),
    ("__init__.py", ("tests/integration/test_sdk_readiness.py",)),
)


def _public_symbols(
    tree: ast.Module,
) -> Iterable[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef]]:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            yield node.name, node
            if isinstance(node, ast.ClassDef):
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and not (
                        member.name.startswith("_")
                    ):
                        yield f"{node.name}.{member.name}", member


def direct_tests(module_path: str) -> tuple[str, ...]:
    """Return the stable direct-test route for one package-relative module."""
    return next((tests for prefix, tests in _ROUTES if module_path.startswith(prefix)), ())


def build_inventory(root: Path = ROOT) -> dict[str, object]:
    """Build a deterministic inventory and fail metadata for every source module."""
    modules: list[dict[str, object]] = []
    undocumented: list[str] = []
    unmapped: list[str] = []
    public_count = 0
    source_root = root / "src/police_thief_p2p"
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        symbols = []
        for name, node in _public_symbols(tree):
            public_count += 1
            symbols.append(name)
            if ast.get_docstring(node) is None:
                undocumented.append(f"{relative}:{name}")
        tests = direct_tests(relative)
        if not tests or any(not (root / item).is_file() for item in tests):
            unmapped.append(relative)
        modules.append(
            {
                "module": f"police_thief_p2p.{relative.removesuffix('.py').replace('/', '.')}",
                "source": f"src/police_thief_p2p/{relative}",
                "direct_tests": list(tests),
                "public_symbols": symbols,
            }
        )
    return {
        "schema_version": "1.0.0",
        "package_version": "0.10.0",
        "summary": {
            "source_modules": len(modules),
            "mapped_modules": len(modules) - len(unmapped),
            "public_callables": public_count,
            "undocumented_public_callables": len(undocumented),
            "result": "PASS" if not undocumented and not unmapped else "FAIL",
        },
        "undocumented": undocumented,
        "unmapped": unmapped,
        "modules": modules,
    }


def main() -> int:
    """Write the inventory and return failure when coverage metadata is incomplete."""
    document = build_inventory()
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(document["summary"], sort_keys=True))
    return 0 if document["summary"]["result"] == "PASS" else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
