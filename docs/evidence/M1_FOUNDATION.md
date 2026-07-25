# M1 Foundation Evidence

- **Milestone:** M1 - Foundation and tooling
- **Package:** `police-thief-p2p` `0.1.0`
- **Date:** 2026-07-25
- **Branch:** `codex/m1-foundation`
- **Status:** `READY` for M2 entry

## Environment

- `uv 0.11.14`
- Managed CPython `3.13.13`
- Windows development host
- Frozen dependency graph: 97 resolved packages
- Source-of-truth files: `pyproject.toml` and `uv.lock`

## Candidate quality results

| Control | Result |
|---|---|
| Frozen lock/sync | Pass |
| Required structure | Pass: 43 paths |
| File hygiene | Pass: 113 tracked files in the clean clone |
| Source size | Pass: no Python source over 150 code lines |
| Requirement/task traceability | Pass |
| Adapter import boundaries | Pass |
| CI matrix validator | Pass |
| Ruff lint | Pass: zero violations |
| Ruff format | Pass |
| Strict mypy | Pass: 65 source files |
| Tests | Pass: 56 |
| Branch-aware coverage | Pass: 91.57%, threshold 85% |
| Deliberate low-coverage probe | Expected rejection at 11.11% |
| Secret scan | Pass |
| Full pre-push hook suite | Pass |
| Source and wheel build | Pass |
| Isolated wheel import/readiness | Pass: `0.1.0`, `READY` |
| Clean-clone suite | Pass at candidate `91364067957b0cad82c1fccf730a1aeeb732c825` |

## Architecture and safety evidence

- `SimulationSdk` is the public application facade.
- CLI, GUI, MCP, and email adapters are protected by AST import-boundary checks.
- External-call policy begins at the typed `GatekeeperPort`; concrete provider
  behavior is deliberately deferred to its owning milestone.
- Time and entropy are injectable; deterministic randomness is isolated from the
  non-seedable cryptographic production source.
- Logging is structured JSON with correlation context and centralized recursive
  redaction.
- Secret-like files, runtime outputs, build outputs, caches, and local reference
  materials are excluded from Git.

## Preserved local reference material

The M0 analysis artifacts were not deleted from the workstation. Git no longer
tracks them, and `.gitignore` protects them from recommit:

- `tmp/pdfs/`: 170 files retained locally.
- `tmp/reference/Game-P2P-Cop-Chase`: retained locally at
  `960499fd5e8777b4929625f5d8fdcf2ab4677b54`.

## Clean-clone proof

Candidate commit `91364067957b0cad82c1fccf730a1aeeb732c825` was cloned with
`--no-local` into a new directory. Frozen sync, all validators, Ruff, formatting,
strict mypy, 56 tests, 91.57% coverage, build, the full pre-push hooks, and an
isolated wheel smoke test passed. The clone remained Git-clean.

Artifact SHA-256 values:

- Wheel:
  `a7188a229f543f4eb09565a2c05a9cb33938f85c4c1c4a1abed52e132a4c89a8`
- Source distribution:
  `d954a41073b3bc99febbed3355f8e7e392948760991873c1d26d4545cc399aed`

The command transcript is archived in `docs/evidence/M1_CLEAN_CLONE.txt`. The
annotated local tag `m1-foundation-v0.1.0` identifies the signed evidence commit.
