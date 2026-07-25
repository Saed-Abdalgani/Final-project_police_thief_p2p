# Foundation Testing and Quality Plan

## Commands

Run from a clean repository root:

```text
uv sync --frozen --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests scripts
uv run pytest
uv run python scripts/validate_structure.py
uv run python scripts/check_file_sizes.py src scripts
uv run python scripts/validate_traceability.py
uv run python scripts/validate_ci.py
uv build
```

The global coverage threshold is 85%. Public M1 APIs require tests. Critical
configuration, crypto, and protocol modules introduced later target full practical
branch coverage.

## Suites and markers

| Directory / marker | Purpose |
|---|---|
| `tests/unit` | Deterministic class/function behavior |
| `tests/integration` / `integration` | SDK and multiple foundation components |
| `tests/contract` / `contract` | Protocol/port/public-boundary shape |
| `tests/property` / `property` | Generated invariant cases |
| `tests/security` / `security` | Redaction, secret, import, and privacy controls |
| `tests/performance` / `performance` | Stable non-flaky budget guards |
| `tests/chaos` / `chaos` | Fake-clock and deterministic fault behavior |
| `tests/fixtures` | Non-discovered golden and negative fixtures |

Hypothesis uses a deterministic CI profile with no wall-clock deadline. Tests must
not sleep for deadline behavior; they inject `FakeClock`.

## Negative gate evidence

Quality tools include synthetic negative tests:

- removing a required path makes structure validation fail;
- a 151-line Python fixture exceeds the source-size limit;
- duplicate/gapped requirement or task IDs fail traceability validation;
- direct service imports from protected adapters fail the architecture test;
- an explicitly isolated low-coverage probe exits non-zero under the 85% gate.

## Clean-clone evidence

M1 closes only after a local clone of the committed candidate runs the command
suite with `uv sync --frozen`. The transcript, candidate commit, environment, and
artifact hashes are archived under `docs/evidence/`.
