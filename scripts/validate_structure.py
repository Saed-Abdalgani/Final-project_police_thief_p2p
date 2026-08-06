"""Validate the required professional repository structure."""

import argparse
from collections.abc import Sequence
from pathlib import Path

REQUIRED_PATHS: tuple[str, ...] = (
    ".env-example",
    ".gitattributes",
    ".github/workflows/ci.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".python-version",
    "CHANGELOG.md",
    "CREDITS.md",
    "LICENSE",
    "README.md",
    "assets",
    "config",
    "data",
    "data/conformance/domain/golden_scenarios.json",
    "data/conformance/crypto/commitment.v1.json",
    "docs/CRYPTO_AUDIT.md",
    "docs/DOMAIN.md",
    "docs/evidence/M7_M8_EXIT.md",
    "docs/evidence/M9_EXIT.md",
    "docs/evidence/M10_EXIT.md",
    "docs/evidence/M12_EXIT.md",
    "docs/evidence/M13_EXIT.md",
    "docs/RESEARCH_REPORT.md",
    "docs/SCHEMAS.md",
    "scripts/export_role_repo.py",
    "scripts/verify_release.py",
    "docs/screenshots/m10_live_local_view.svg",
    "docs/screenshots/m10_replay_verified.svg",
    "docs/screenshots/m10_replay_tampered.svg",
    "docs/OPERATIONS.md",
    "docs/PLAN.md",
    "docs/PROTOCOL.md",
    "docs/STRATEGY.md",
    "docs/PRD.md",
    "docs/TODO.md",
    "notebooks",
    "pyproject.toml",
    "results",
    "results/benchmarks/m3_domain.json",
    "results/benchmarks/m6_belief.json",
    "results/benchmarks/m7_strategy.json",
    "results/benchmarks/m8_reliability.json",
    "results/benchmarks/m12_tuning.json",
    "results/benchmarks/m12_selection.json",
    "scripts/check_file_hygiene.py",
    "scripts/check_file_sizes.py",
    "scripts/generate_m10_screenshots.py",
    "scripts/validate_ci.py",
    "scripts/validate_imports.py",
    "scripts/validate_structure.py",
    "scripts/validate_traceability.py",
    "src/police_thief_p2p/__init__.py",
    "src/police_thief_p2p/adapters",
    "src/police_thief_p2p/constants.py",
    "src/police_thief_p2p/domain",
    "src/police_thief_p2p/sdk",
    "src/police_thief_p2p/services",
    "src/police_thief_p2p/services/protocol",
    "src/police_thief_p2p/services/crypto",
    "src/police_thief_p2p/services/audit",
    "src/police_thief_p2p/services/belief",
    "src/police_thief_p2p/services/replay",
    "src/police_thief_p2p/shared/config.py",
    "src/police_thief_p2p/shared/gatekeeper.py",
    "src/police_thief_p2p/shared/version.py",
    "tests/chaos",
    "tests/conftest.py",
    "tests/contract",
    "tests/fixtures",
    "tests/integration",
    "tests/integration/test_dual_process_mcp.py",
    "tests/integration/test_mutual_audit.py",
    "tests/performance",
    "tests/property",
    "tests/security",
    "tests/unit",
    "uv.lock",
)


def validate_structure(
    root: Path,
    required_paths: Sequence[str] = REQUIRED_PATHS,
) -> list[str]:
    """Return repository-relative paths that are missing."""
    return [path for path in required_paths if not (root / path).exists()]


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the selected root and return a shell-friendly status."""
    args = build_parser().parse_args(argv)
    missing = validate_structure(args.root.resolve())
    if missing:
        print("Missing required paths:")
        for path in missing:
            print(f"- {path}")
        return 1
    print(f"Structure OK: {len(REQUIRED_PATHS)} required paths present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
