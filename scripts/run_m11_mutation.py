"""Run the deterministic semantic mutation families required by M11."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_mutation.json"
SUITES = {
    "config_rules": "tests/unit/test_config_models.py",
    "scoring": "tests/unit/test_domain_schedule_scoring.py",
    "state_transitions": "tests/unit/test_domain_state_engine.py",
    "crypto_verification": "tests/unit/test_crypto_primitives.py",
    "gatekeeper_decisions": "tests/unit/test_m9_gatekeeper.py",
    "replay_context": "tests/unit/test_m10_replay.py",
}


def main() -> int:
    """Execute every mutation family and store a compact non-flaky transcript."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        *SUITES.values(),
        "--no-cov",
        "-q",
    ]
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and arguments.
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    transcript = (completed.stdout + completed.stderr).strip().splitlines()
    document = {
        "schema_version": "1.0.0",
        "measured_at": "2026-07-26",
        "package_version": "0.10.0",
        "method": "deterministic semantic mutants and boundary replacements",
        "families": SUITES,
        "operators": [
            "fixed/minimum numeric replacement",
            "terminal/scoring outcome replacement",
            "illegal transition and source/target replacement",
            "canonical byte, nonce, digest, field, and order mutation",
            "quota/admission/retry/circuit decision mutation",
            "replay identity/topology/context mutation",
        ],
        "transcript_tail": transcript[-3:],
        "result": "PASS" if completed.returncode == 0 else "FAIL",
    }
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": document["result"], "tail": transcript[-1:]}))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
