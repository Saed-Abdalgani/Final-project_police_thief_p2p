"""Run the local end-to-end playtest suite that does not need a second machine."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS: tuple[tuple[str, list[str]], ...] = (
    ("sync", ["uv", "sync", "--frozen", "--all-groups"]),
    ("readiness", ["uv", "run", "police-thief-p2p", "readiness", "--json"]),
    (
        "dual_process_mcp",
        ["uv", "run", "pytest", "tests/integration/test_dual_process_mcp.py", "-q", "--no-cov"],
    ),
    ("league_rehearsal_loopback", ["uv", "run", "python", "-m", "scripts.run_m12_league_rehearsal"]),
    ("replay_screenshots", ["uv", "run", "python", "scripts/generate_m10_screenshots.py"]),
)


def main() -> int:
    """Execute each local playtest step and print a compact pass/fail table."""
    results: list[dict[str, object]] = []
    for name, command in STEPS:
        print(f"==> {name}", flush=True)
        completed = subprocess.run(command, cwd=ROOT, check=False)  # noqa: S603
        passed = completed.returncode == 0
        results.append({"step": name, "passed": passed, "returncode": completed.returncode})
        if not passed:
            print(json.dumps({"results": results, "result": "FAIL"}, sort_keys=True))
            return completed.returncode or 1
    print(json.dumps({"results": results, "result": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
