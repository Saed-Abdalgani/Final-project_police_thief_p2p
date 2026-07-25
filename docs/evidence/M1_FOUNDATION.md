# M1 Foundation Evidence

- **Milestone:** M1 - Foundation and tooling
- **Package:** `police-thief-p2p` `0.1.0`
- **Date:** 2026-07-25
- **Branch:** `codex/m1-foundation`
- **Status:** candidate checks passed; clean-clone proof pending

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
| File hygiene | Pass: 111 tracked candidate files |
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

## Remaining closure action

Commit the candidate, clone that exact commit into a new directory, execute the
CI-equivalent frozen command suite, archive the transcript, complete T074-T075,
and create the annotated local milestone tag.
