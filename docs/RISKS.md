# Risk Register

**Baseline:** `1.0.0`
**Scale:** Probability and impact are Low/Medium/High/Critical. P0 risks block the applicable exit gate when triggered.

| ID | Risk | Probability | Impact | Owner | Mitigation | Trigger / leading indicator | Contingency | Status |
|---|---|---|---|---|---|---|---|---|
| RSK-001 | PDF/reference implementation mismatch | Medium | High | Product Owner | Source precedence, traceability, independent conformance vectors | Example behavior differs from rule/parameter | Follow PDF; ADR and compatibility note | Open |
| RSK-002 | Peers implement different scent kernels/decay order | Medium | Critical | Belief Lead | Signed model/example, digest, golden vectors | Config digest or numeric vector differs | Fail negotiation before counted start | Open |
| RSK-003 | Canonical commitment bytes differ across peers/platforms | Medium | Critical | Security Lead | ADR-004, schemas, cross-platform byte/hash vectors | Same logical payload hashes differently | Block protocol release; version/fix both exports | Open |
| RSK-004 | Public tunnel is unreachable or unstable | High | High | Operations Lead | Preflight, deadlines, reconnect policy, external rehearsal | readiness/latency/error threshold fails | Switch documented endpoint before count or void pre-Step-0 | Open |
| RSK-005 | Duplicate/reordered delivery mutates state twice | High | High | Protocol Lead | Atomic idempotency, phases, sequences, persisted response | conflicting journal/effect count | Stop, audit, restore acknowledged checkpoint | Open |
| RSK-006 | Strategy overfits reference or one adversary | High | High | Strategy Lead | diverse pool, train/validation/holdout split, ablations | large validation gap or family collapse | Reject candidate; revert previous frozen policy | Open |
| RSK-007 | Barrier search misses deadline | Medium | Medium | Strategy Lead | candidate pruning, graph caches, iterative deadline, fallback | p95/deadline regression | deterministic legal fallback; reduce depth | Open |
| RSK-008 | Live GUI/LLM/log leaks opponent truth or nonce | Low | Critical | Security Lead | local DTOs, phase gates, redaction, privacy tests | forbidden field scan hit | stop release/match; incident and regression | Open |
| RSK-009 | Gmail credentials/token enter Git or logs | Low | Critical | Security Lead | send-only scope, ignores, history scan, protected store | secret scanner or log detector hit | revoke, purge safely, rotate, audit history | Open |
| RSK-010 | Gmail quota/provider failure loses report | Medium | High | Reporting Lead | Gatekeeper, durable idempotent outbox, dry-run | pending age/retry/circuit threshold | retain agreed result and retry within runbook | Open |
| RSK-011 | Police/Thief exports drift | High | High | Release Lead | canonical export, manifests, cross-role suite | source/schema/lock digest mismatch | discard exports and regenerate both | Open |
| RSK-012 | Crash loses audit data or acknowledges unlogged action | Medium | Critical | Reliability Lead | write-ahead/atomic ordering, fsync policy, crash matrix | journal gap/checkpoint disagreement | technical terminal; preserve stores for audit | Open |
| RSK-013 | Too few eligible opponents are available | Medium | High | League Owner | schedule early, warmups, signed ledger | calendar does not contain 2 distinct opponents | escalate scheduling; do not fabricate counts | Open |
| RSK-014 | Submission form/tag/access/README failure | Medium | High | Submission Owner | early dry-run checklist and independent review | missing field/link/access or layout difference | delay submission until corrected | Open |
| RSK-015 | Remote request flood exhausts event loop/memory | Medium | Critical | Security Lead | size/rate/concurrency/queue bounds, backpressure/circuit | queue/latency/memory threshold | isolate endpoint, degrade, technical handling | Open |
| RSK-016 | Malicious game ID escapes artifact root | Low | Critical | Security Lead | sanitized IDs, path containment, symlink tests | resolved path outside root | reject, quarantine evidence, security incident | Open |
| RSK-017 | Clock skew produces incorrect timeout/order | Medium | High | Reliability Lead | monotonic deadlines and sequences | wall-clock jump/skew fault fails | rely on monotonic checkpoint; controlled terminal | Open |
| RSK-018 | Optional LLM exceeds tokens/latency or returns illegal/protocol text | High | Medium | Strategy Lead | default template, strict parser, cap/deadline, legal fallback | budget/deadline/parser alarm | disable provider for series | Open |
| RSK-019 | Dependency or tunnel/provider version breaks clean clone | Medium | High | Release Lead | `uv.lock`, compatibility matrix, clean-clone CI | resolution/import/contract failure | pin known-good or remove optional dependency | Open |
| RSK-020 | Fixed/minimum semantics are weakened by negotiation | Medium | Critical | Protocol Lead | status-aware validator and truth table | accepted invalid config vector | fail closed, correct config, no counted consumption | Open |
| RSK-021 | Counted-match ledger permits duplicate opponent or false total | Medium | Critical | League Owner | immutable state model and mutual declarations | total/opponent conflict | block Step-0 and preserve discrepancy | Open |
| RSK-022 | Performance evidence is incomparable across hardware/configs | Medium | Medium | QA Lead | experiment manifests and declared baseline | missing commit/config/hardware/seed | invalidate run and repeat | Open |
| RSK-023 | Documentation and implementation diverge | High | High | Architecture Lead | mechanism PRDs, traceability, docs-as-code gate | changed contract lacks docs/test link | block merge/release | Open |
| RSK-024 | Unresolved ambiguity reaches counted play | Low | Critical | Product Owner | ambiguity register and P0 gate | open P0 or peer interpretation conflict | stop; decide/ADR/version before play | Open |

## Review rules

- Review at each milestone entry/exit and after every incident or incompatible change.
- A triggered Critical risk is a P0 blocker until its contingency and regression evidence are complete.
- Owners update probability, impact, mitigation effectiveness, residual risk, and evidence link.
- Risks are never closed because implementation began; closure requires objective evidence or removal of exposure.

## M11 disposition

The M11 adversarial, chaos, soak, dependency, license, history/archive-secret,
mutation, performance, and full regression campaigns found no unresolved P0/P1
defect. RSK-003, RSK-005, RSK-008, RSK-009, RSK-010, RSK-012, RSK-015,
RSK-016, RSK-017, RSK-018, RSK-019, RSK-020, RSK-021, RSK-022, and RSK-023
have exercised controls with passing M11 evidence.

The register intentionally stays open for future exposure. RSK-004, RSK-010,
and RSK-013 block counted play until the M12 external rehearsal/schedule gates;
RSK-011 and RSK-014 block release until the M12/M13 export and experiment gates;
RSK-001, RSK-002, RSK-006, RSK-007, RSK-022, RSK-023, and RSK-024 block any
candidate whose future inputs trigger them. None was triggered by the M11
candidate, and none is silently accepted.
