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

The global coverage threshold is 85%. Public APIs require tests. Critical
configuration and domain modules target 100% practical branch coverage; crypto and
protocol modules introduced later inherit that standard.

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

M3 overrides the shared Hypothesis profile for its legal-action/state-invariant
campaign and executes 10,000 deterministic examples. Coordinate metamorphism covers
all four origins and both 0/1 index conventions.

## M4 protocol campaign

Run the peer contract and independent-process path directly:

```text
uv run pytest tests/contract/test_protocol_contracts.py -q
uv run pytest tests/integration/test_protocol_runtime.py -q
uv run pytest tests/integration/test_dual_process_mcp.py -q
uv run pytest tests/security/test_mcp_boundaries.py -q
```

The dual-process test runs twice, once per startup order. Every peer gets a
different PID and separate config, artifact, cache, and temporary roots. The only
coordination channel is each peer's loopback streamable-HTTP FastMCP endpoint.
Both peers validate identical shared bytes, apply the same proposal and terminal
public event sequence, and independently reach `COMPLETED`.

Protocol hostile/fault coverage includes duplicate keys, invalid UTF-8, size,
depth, string, collection and finite-number limits; config/scent/version/group/
schedule/UUID mismatch; counted ledger boundaries; duplicate/conflicting IDs;
old/gap/future sequence; illegal phases; response-loss recovery; restart repair;
Gatekeeper timeout/dependency failure; and safe exception mapping.

## M5 cryptography and audit campaign

```text
uv run pytest tests/contract/test_crypto_contracts.py -q
uv run pytest tests/unit/test_crypto_primitives.py -q
uv run pytest tests/unit/test_step_zero_and_evidence.py -q
uv run pytest tests/unit/test_system_probes.py -q
uv run pytest tests/integration/test_mutual_audit.py -q
uv run pytest tests/integration/test_dual_process_mcp.py -q
```

The campaign freezes exact commitment/Step-0 bytes and digests, mutates every
commitment field, exercises the illegal lifecycle matrix, rejects nonce reuse,
forged states/scent/capture/scores, corrupt journals/manifests, foreign/gapped/
duplicated records, dirty revisions, signature tamper, and independent-result
disagreement. The localhost test transports the complete final-reveal graph
through two isolated OS processes in both startup orders and requires both audits
to return `Verified OK`.

## M6 scent and belief campaign

```text
uv run pytest tests/unit/test_scent_phase6.py -q
uv run pytest tests/unit/test_belief_grid.py tests/unit/test_hint_belief_service.py -q
uv run pytest tests/integration/test_belief_interop.py -q
uv run pytest tests/property/test_belief_properties.py -q
uv run pytest tests/security/test_belief_privacy.py -q
uv run pytest tests/performance/test_belief_performance.py -q
```

The campaign independently reproduces all signed scent cases, validates private
history across restart, rejects substituted reveal/frame context, proves
normalization/masks/transition mass with Hypothesis, neutralizes command-like
hints, and scans live DTOs/SDK signatures for opponent truth. Stored 25-sample
35-update p95 results for 7x7 and 15x15 boards are in
`results/benchmarks/m6_belief.json`.

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
