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

## M9 artifact and reporting campaign

```text
uv run pytest tests/unit/test_m9_artifacts_reporting.py -q
uv run pytest tests/unit/test_m9_gatekeeper.py -q
uv run pytest tests/integration/test_m9_outbox_gmail.py -q
uv run police-thief-p2p report validate \
  --manifest <artifact-root>/official/manifest_<game-id>.json \
  --artifact-root <artifact-root> \
  --sender <account@example.com>
```

The campaign builds one complete 14-document series graph, validates and exports
it, then detects byte tamper, path traversal, unsafe identity, bad linkage,
agreement and token-total corruption. Reporting tests parse deterministic MIME,
recover an interrupted atomic outbox, prove one provider call across duplicate
dispatch, and classify auth, timeout, 429, 5xx, and malformed Gmail responses.
OAuth tests exercise first-run authorization exchange and refresh using a fake
HTTP boundary while asserting exact send-only scope and redacted representation.
Gatekeeper tests cover continuous refill, durable day/session quotas, priority
and backpressure, provider retry guidance, redacted metrics, anomaly thresholds,
open circuit, and confirmed reset.

The real Gmail rehearsal is deliberately not part of automated tests. It requires
interactive team OAuth, a team-controlled safe recipient, and an external
redacted receipt; routine tests must never contact the lecturer address.

## M10 live GUI and replay campaign

```text
uv run pytest tests/unit/test_m10_live_view.py -q
uv run pytest tests/unit/test_m10_replay.py -q
uv run pytest tests/integration/test_m10_replay_gui.py -q
uv run pytest tests/security/test_m10_gui_replay_security.py -q
uv run python scripts/generate_m10_screenshots.py
```

The focused campaign proves immutable local-view privacy, all eight accessible
states, SDK-only GUI actions, background snapshot delivery, terminal retention,
headless parity, fixed contrast/heat scale, safe errors, and deterministic SVG
bytes. Replay validates bounded UTF-8/schema input and the full manifest graph,
recomputes every commitment field, nonce, state, scent, public effect, terminal,
and score, stops on first invalid evidence, gates objective tracks on dual final
audit, navigates all required commands/sub-games, and validates canonical JSON
plus escaped standalone HTML exports.

`docs/screenshots/m10_live_local_view.svg`,
`m10_replay_verified.svg`, and `m10_replay_tampered.svg` are regenerated from
code, byte-stable, and scanned for opponent truth, nonce, credential, and token
field names.

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

## M11 release-candidate campaign

M11 exercises the complete implementation, not a reduced mock package. The local
baseline is Windows 11, CPython 3.13, four CPU cores, and 8 GB RAM. GitHub Actions
runs the full suite on Windows with Python 3.13 and 3.14, plus an independent
macOS/Python 3.13 import and readiness smoke. Platform details and the one
capability-based symlink skip are recorded in `docs/M11_PLATFORM.md`.

Fixtures are immutable builders under `tests/helpers`; each role/process receives
separate config, artifact, cache, and temporary roots. The two-process MCP suite
shares only loopback streamable HTTP. Hypothesis uses the deterministic `ci`
profile (`derandomize=True`, no database, no wall-clock deadline). The continuous
soak uses seed identifiers `0..999`, six one-step sub-games per series, injected
fake clocks, and no external providers.

Run the measured campaign:

```text
uv run python -m scripts.m11_inventory
uv run python -m scripts.m11_trace_matrix
uv run python -m scripts.run_m11_mutation
uv run python -m scripts.run_m11_soak
uv run python -m scripts.run_m11_benchmarks
uv run python -m scripts.run_m11_release_audit
uv run python -m scripts.run_m11_license_audit
uv export --frozen --all-groups --no-emit-project --no-hashes \
  --format requirements-txt --output-file tmp/m11-requirements.txt
uvx pip-audit --requirement tmp/m11-requirements.txt --strict \
  --format json --output results/benchmarks/m11_vulnerabilities.json \
  --progress-spinner off --desc off
uv run pytest
```

The M11 gates are:

- exact mapping of all source modules and all 314 normative FR/NFR/E/F entries;
- every public callable documented and directly mapped to executable tests;
- Ruff zero findings, Ruff-format clean, strict mypy clean, import/static/schema/
  traceability validators clean, and no source file above 150 code lines;
- global statement/branch coverage at least 85%;
- 1,000 continuous six-game series, zero deadlock/unbounded wait, bounded
  journals/cache/signature stores, and zero retained-object growth;
- SDK cold-readiness p95 under 3,000 ms, algorithmic domain p95 under 250 ms,
  six-log replay p95 under 2,000 ms, and artifact write p95 under 100 ms;
- zero known locked-dependency vulnerabilities, incompatible licenses, secret/
  archive/history findings, or unresolved P0/P1 defects.

Machine-readable evidence is committed under `results/benchmarks/m11_*.json`.
The manual cryptographic review is `docs/M11_CRYPTO_REVIEW.md`; the platform
record is `docs/M11_PLATFORM.md`; the signed decision is
`docs/evidence/M11_EXIT.md`.
