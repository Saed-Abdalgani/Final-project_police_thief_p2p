# KPI and Acceptance Evidence Plan

**Baseline:** `1.0.0`

## 1. Evidence types

| Code | Type | Required properties |
|---|---|---|
| `TEST` | Automated test | deterministic command, version/seed, pass/fail output, retained report |
| `ARTIFACT` | Machine-readable artifact | schema/version, digest, provenance, immutable path |
| `SCREENSHOT` | Visual evidence | timestamp/run manifest, caption, reproduction steps, no secret/private leak |
| `BENCHMARK` | Performance/cost measurement | hardware/runtime/config/commit, warmup/sample method, raw data, statistic |
| `MANUAL` | Manual inspection | named checklist, reviewer/date, inspected revision, findings |
| `EXTERNAL` | External confirmation | provider/opponent/lecturer identity, timestamp, scope, retained reference |

Every requirement range has a primary evidence type in `docs/TRACEABILITY.md`. High-risk requirements should combine automated and independent/manual evidence; external confirmation never replaces local tests.

## 2. KPI catalog

| ID | Dimension | Metric / unit | Target | Measurement and evidence source | Gate |
|---|---|---|---:|---|---|
| KPI-C01 | Compliance | Appendix E rules covered / rules | `55/55` | traceability validator + compliance report | M0 and release |
| KPI-C02 | Compliance | fixed-value violations accepted / cases | `0` | config negative tests | M2 |
| KPI-C03 | Compliance | minimum weakening accepted / cases | `0` | negotiation truth table | M4 |
| KPI-C04 | Integrity | undetected tamper mutations / corpus | `0` | mutation/audit suite | M4/release |
| KPI-C05 | Integrity | false capture claims/denials accepted / cases | `0` | exhaustive capture protocol vectors | M4 |
| KPI-C06 | Security | committed secret findings / scan | `0` | working-tree, history, archive secret scans | every release |
| KPI-R01 | Reliability | completed local six-game series / 1,000 seeded runs | `>=99.5%` | soak manifest/report | M11 |
| KPI-R02 | Reliability | completed public-tunnel fault runs / runs | `>=98%` | remote integration report | M12 |
| KPI-R03 | Reliability | duplicate message side effects / injections | `0` | idempotency fault suite | M5 |
| KPI-R04 | Reliability | deadlocks / soak+chaos runs | `0` | watchdog/state telemetry | M11 |
| KPI-R05 | Reliability | runs with a typed terminal outcome / runs | `100%` | artifact validator | M11 |
| KPI-R06 | Reliability | valid completed reports lost after restart / reports | `0` | durable-outbox recovery suite | M9 |
| KPI-P01 | Performance | algorithmic action p95 / milliseconds | `<=250 ms` | baseline-CPU benchmark | M12 |
| KPI-P02 | Performance | algorithmic action hard deadline / seconds | `<=2 s` | runtime deadline evidence | M7 |
| KPI-P03 | Performance | legal fallback latency / milliseconds | `<=50 ms` | microbenchmark | M7 |
| KPI-P04 | Performance | SDK cold start / seconds | `<=3 s` | clean-process benchmark | M11 |
| KPI-P05 | Performance | 35-step replay verification / seconds | `<=2 s` | verifier benchmark | M10 |
| KPI-COST01 | Cost | default language tokens / series | `0` | token ledger | M7/M12 |
| KPI-COST02 | Cost | optional language tokens / series | `<=200,000` or signed lower value | report token totals | each series |
| KPI-S01 | Strategy | official-score uplift vs greedy / percentage points | `>=20` | paired role-swapped holdout | M12 |
| KPI-S02 | Strategy | Police capture rate vs baseline / percent | `>=70%` | seeded holdout tournament | M12 |
| KPI-S03 | Strategy | Thief survival rate vs baseline / percent | `>=70%` | seeded holdout tournament | M12 |
| KPI-S04 | Strategy | illegal final actions / decisions | `0` | property/fuzz tests | M7 |
| KPI-S05 | Strategy | deterministic decisions for same inputs / percent | `100%` | replayed-decision tests | M7 |
| KPI-S06 | Strategy | worst fixture-family drop from aggregate / points | `<=15` | holdout family report | M12 |
| KPI-Q01 | Quality | global statement/branch policy coverage / percent | `>=85%` global | coverage XML/HTML | every CI/release |
| KPI-Q02 | Quality | critical config/crypto/protocol branch coverage / percent | `100% where practical; exceptions ADR-backed` | targeted coverage report | release |
| KPI-Q03 | Quality | Ruff violations / findings | `0` | `uv run ruff check .` | every CI/release |
| KPI-Q04 | Quality | type-check failures / findings | `0` | locked type-check command | every CI/release |
| KPI-Q05 | Quality | documented public SDK APIs / percent | `100%` | docs/API inventory validator | release |
| KPI-Q06 | Quality | public functions/methods with tests / percent | `100%` | API-test traceability | release |
| KPI-Q07 | Quality | source files over 150 actual code lines without ADR / files | `0` | source metrics report | every CI/release |

## 3. Acceptance evidence policy

- Unit and property tests prove deterministic domain invariants.
- Contract/integration tests prove SDK, protocol, storage, Gatekeeper, and adapter boundaries.
- Fault injection proves retry, idempotency, deadline, recovery, and fail-closed behavior.
- Artifacts prove canonical bytes, digests, phase history, results, and reproducibility.
- Benchmarks prove latency, throughput, resource, token, and cost goals under a declared environment.
- Screenshots prove required GUI/replay state and accessibility only when linked to a deterministic sample manifest.
- Manual reviews cover source interpretation, architecture, threat model, UX, license/credits, and submission layout.
- External confirmations cover tunnel reachability, opponent agreement, Gmail dry run, repository access, and Moodle submission where applicable.

An acceptance item is `PASS` only when its evidence is linked, reproducible, current for the candidate revision, and free of unresolved severity-0/1 findings.

