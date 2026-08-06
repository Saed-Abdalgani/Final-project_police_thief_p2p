# Changelog

All notable project changes are documented here. The project follows semantic versioning for documentation, package, protocol, config, and schema contracts, with compatibility recorded separately when those versions diverge.

## Package [0.11.0] - 2026-08-06

### Added

- Deterministic Police/Thief role exports (`scripts/export_role_repo.py`),
  release manifests, sibling repositories, schema catalog, and M13 submission
  checklist with a CONDITIONALLY READY exit record.
- Offline experiment arena that plays paired role-swapped sub-games through the
  real domain engine, belief service, scent emission, and strategy guard, with
  deterministic observation delay and scent dropout.
- Baseline and adversary roster covering reference-greedy, random-legal,
  scripted, evader, pursuer, and hint-profile families plus immutable regression
  checkpoints.
- Frozen train/validation/sealed-holdout split manifests whose seeds, opponents,
  and fixtures are disjoint and digested, with holdout access gated on a
  candidate freeze digest.
- Official scoring, separate zero-tolerance reliability accounting, bootstrap and
  paired-uplift intervals, and Bradley-Terry ranking on the Elo scale.
- Bounded Police, Thief, belief, and hint search spaces with seeded random search,
  Gaussian-kernel surrogate refinement, and two-tier early stopping that persists
  every attempted configuration.
- Ablation, board-geometry robustness, degraded-observation, and adversarial
  sweep studies; overfitting gate; and a one-shot holdout evaluation.
- Per-campaign resource accounting for wall time, peak resident memory, calls,
  payload bytes, and tokens, excluded from the manifest digest so replays on
  different hardware keep the same manifest identity.
- League dress rehearsal driving two independently rooted peer processes through
  warmups and a counted six-sub-game series with mutual audits.
- `scripts/run_tournament.py` and an SDK simulation facade for ad-hoc tournaments.

### Fixed

- The deterministic fallback baselines ran one breadth-first search per supported
  posterior cell, so the safety path invoked after a deadline overrun cost far
  more than the search it protected. They now derive every distance from a single
  single-source sweep, which cut p95 decision latency on an 8x8 board from 860 ms
  to 224 ms and brought every measured geometry inside the 250 ms budget.

## Package [0.10.0] - 2026-07-26

### Added

- Exhaustive source-module/public-API and FR/NFR/Appendix E/F executable-test
  inventories with machine-checked exact-set coverage.
- Deterministic adversarial suites for Unicode, paths, symlinks, redirects,
  prompt/log injection, every protocol phase/tool, every lifecycle transition,
  crash boundaries, worker freezes, and collection/resource limits.
- Repeatable 1,000-series/6,000-sub-game soak, percentile/hardware/profile
  benchmark, history/archive secret audit, dependency/license audit, and
  semantic mutation campaigns with committed evidence.
- Full six-game local audit, artifact, replay, and report-validation exercise
  plus clean-clone and cross-platform CI release procedures.

### Changed

- Protocol session caches and anomaly-signature retention now have explicit
  configurable bounds, preserving durable recovery while preventing unbounded
  long-running process growth.
- Competition tunnel URLs reject query-bearing endpoints and redirect targets
  must remain on the already validated origin.
- Package advances to `0.10.0`; protocol remains `0.7.0` and schemas remain
  `0.2.0`.

## Package [0.9.0] - 2026-07-26

### Added

- Immutable comprehensive SDK `LocalView` with own truth, public topology,
  normalized belief, uncertainty, hints, lifecycle status, metrics, and
  recursive forbidden-field privacy enforcement.
- Dependency-injected Tk live/replay shells with resizable coordinate-aware
  boards, fixed-scale heatmaps, role/trail/barrier rendering, complete
  text/icon/color states, keyboard operation, scalable text, safe confirmations,
  and correlation-ID error boundaries.
- Bounded thread-safe snapshot channel with intermediate coalescing, essential
  final/terminal preservation, and background gameplay worker support.
- Schema-first `SimulationSdk.verify_log` and full-manifest replay selection,
  per-step nonce/commitment/state/scent/effect/terminal/score verification,
  single-log belief mode, and final-audit-gated objective dual-log mode.
- Immutable replay navigation, six-game selection support, explicit
  missing/frozen-track banners, canonical JSON and standalone escaped HTML audit
  exports, and prominent accessible `Verified OK`/`TAMPERED` presentation.
- Deterministic live, verified replay, and tampered replay SVG fixtures with
  mutation, privacy, accessibility, linkage, resource-bound, and CLI tests.

### Changed

- Package advances to `0.9.0`. Protocol remains `0.7.0`; artifact/config and
  replay-report schemas remain in the compatible `0.2.0` family.

## Package [0.8.0] - 2026-07-26

### Added

- Appendix F artifact filename/path confinement, classified official/private/
  diagnostic storage, immutable atomic JSON writes, and restrictive permission
  handling.
- Series declaration, exact played-config, sealed finalized-log, final-result,
  and artifact-manifest models with JSON Schemas and full digest/linkage
  verification.
- Exact per-step, per-sub-game, and per-series group token accounting plus
  independently recomputed score, win, tie, and winner totals.
- Verified-manifest-only standard JSON report construction, deterministic MIME,
  recipient allowlisting, mutual digest confirmation, credential-free archive,
  and SDK/CLI dry-run validation.
- Atomic restart-safe outbox with six explicit states, logical-report
  idempotency, interrupted-send recovery, and durable provider outcome recording.
- Installed-app PKCE authorization and refresh with exact Gmail send-only scope,
  private atomic token storage, and a result-agnostic Gmail provider adapter.
- Config-driven provider profiles, continuous monotonic token buckets, durable
  daily/session quotas, priority/concurrency admission, exponential jitter,
  Retry-After handling, anomaly detection, circuit recovery/manual reset, and
  redacted metrics for MCP, Gmail, and optional external LLM calls.
- M9 artifact, fake-Gmail, OAuth, restart, duplicate, 429, 5xx, malformed,
  backpressure, quota, anomaly, circuit, and dry-run test coverage.

### Changed

- Package advances to `0.8.0`. Protocol remains `0.7.0` and the compatible
  artifact/config schema family remains `0.2.0`.

## Package [0.7.0] - 2026-07-25

### Added

- Private-only typed Police/Thief strategy selectors and weights, stable
  `StrategyBrain`/`Decision` contracts, final legality guard, deterministic
  posterior baselines, and fake-clock deadline fallback.
- Stratified posterior sampling, bounded iterative risk search and transposition
  cache, graph-aware Police barriers, Thief survival/mode scoring, and
  opponent/version-isolated audited adaptation.
- Zero-token semantic hint templates, Unicode word caps, trust-aware deception,
  strict Gatekeeper-only optional paraphrasing, and commitment-bound semantic
  intent.
- Formal CAS lifecycle phase machine, SDK-owned policy-free Orchestrator,
  operation deadlines, transport-only retry/backoff, circuit breaker,
  cancellation, independent Watchdog, and redacted health states.
- Hash-chained durable orchestration journal, exact mutual checkpoints,
  persist-before-ack crash hooks, bounded priority queues, tunnel preflight, and
  ordered cooperative shutdown.
- Competitive latency/paired-role evidence and a 1,000-sub-game persistence plus
  Watchdog soak with zero deadlocks.

### Changed

- Package and protocol advance to `0.7.0`; commitment bodies advance to `1.1.0`
  to bind the semantic hint intent. Artifact schema family remains `0.2.0`.

## Package [0.6.0] - 2026-07-25

### Added

- Exact unrounded Decimal scent fields with signed 5x5 emission, clipping,
  accumulation/clamp, full Police-plus-Thief turn decay, private restart-safe
  history, and expanded cross-peer conformance vectors.
- Commitment-linked bounded `ScentFrame`, reveal-gated validation, and schemas
  that structurally exclude live opponent truth.
- Immutable normalized `BeliefGrid`, reachable priors, public topology masks,
  uniform and behavioral-mixture transition kernels, and log-space scent fusion.
- Command-free semantic hint parsing, category-isolated recency-aware Beta
  reliability, likelihood-ratio caps, deterministic degenerate recovery, entropy,
  credible regions, redacted local views, and post-audit-only calibration.
- Property, privacy, adversarial, interoperability, persistence, and 35-step
  minimum/expanded board performance campaigns.

### Changed

- Package and peer payload protocol advance to `0.6.0`; the compatible artifact
  schema family remains `0.2.0`.
- Quantization now occurs only at scent wire/audit and belief diagnostic
  boundaries under accepted ADR-014.

## Package [0.5.0] - 2026-07-25

### Added

- Opaque OS-CSPRNG nonces, immutable canonical commitment bodies, constant-time
  SHA-256 verification, sealed lifecycle storage, and phase-gated nonce manifests.
- Portable CPU/RAM/optional GPU/runtime and exact Git probes plus canonical
  HMAC-SHA-256 Step-0 declarations loaded only from secret environment/file handles.
- Context-bound sealed capture claims/responses and corruption-detecting local
  event-journal hash chains.
- Pure audit service that validates constitution/declarations/evidence, recomputes
  commitments/state/scent, replays domain legality, resolves capture/scoring, and
  applies an immutable zero-point tamper sanction.
- Mutual audit-manifest/result agreement, six-game score recomputation, JSON
  schemas, golden conformance vectors, every-field mutation tests, and full
  dual-process localhost final-reveal evidence.

### Changed

- Package and peer payload protocol advance to `0.5.0`; the compatible artifact
  schema family remains `0.2.0`.
- The dual-process interoperability campaign now carries real M5 commitments,
  nonce-free live reveals, final nonces, independent reports, and result agreement.

## Package [0.4.0] - 2026-07-25

### Added

- Immutable bounded protocol envelopes, safe response/error catalog, and frozen
  FastMCP `*_v1` tool inventory.
- Full proposal/acceptance and Step-0 contracts for identities, four repositories,
  commits, MCP URLs, counted ledgers, exact shared bytes/digests, scent vectors,
  UUID agreement, optional capabilities, and balanced role schedules.
- Persist-before-ack sessions, atomic file records, restart-safe idempotency,
  monotonic sequence/phase enforcement, and constant-memory reorder rejection.
- Thin SDK-only FastMCP server, Gatekeeper-only client, real backend, configured
  resource ceilings, and isolated peer process entry point.
- Dual-process A-first/B-first localhost interoperability, crash, duplicate,
  conflict, hostile-input, mismatch, deadline, and boundary evidence.

### Changed

- Package and peer protocol versions advance to `0.4.0`; the compatible artifact
  schema family remains `0.2.0`.
- Private network configuration now owns request byte, depth, string, collection,
  and reorder ceilings.

## Package [0.3.0] - 2026-07-25

### Added

- Immutable Position, Role, Direction, Action, barrier, local-state, event, terminal,
  scoring, outcome, and role-schedule domain contracts.
- Deterministic legal movement/barrier transitions with quota, permanence, local
  truth, survival, and step-ceiling enforcement.
- BFS distance/components, articulation points, and vertex-disjoint escape-route
  approximation over public barriers.
- Offline verified direct, barrier, and enclosure capture resolution with explicit
  terminal ordering and fixed Appendix F scoring.
- Group-identity six-game aggregation and balanced P,T,P,T,P,T schedule.
- SDK-only domain initialization, legality, transition, schedule, and aggregation
  entry points.
- 10,000-case property campaign, golden terminal/scoring scenarios, deterministic
  simulator, public API inventory, and committed performance evidence.

### Changed

- Package version advances to `0.3.0`; protocol and schema remain compatible at
  `0.2.0`.

## Package [0.2.0] - 2026-07-25

### Added

- Immutable shared JSON and private TOML configuration models with Appendix F
  fixed/minimum/default enforcement and field provenance.
- Resource-bounded hostile JSON/TOML loaders with stable safe error codes.
- Typed identifiers, four-corner coordinate normalization, exact decimal scent
  kernel, canonical JSON, SHA-256, and raw/semantic comparison primitives.
- Packaged Draft 2020-12 schemas for shared config, Gatekeeper profiles,
  declarations, per-sub-game config, sealed logs, final results, and envelopes.
- Positive/negative artifact fixtures plus canonical, digest, and scent conformance
  vectors.
- SDK configuration loading and schema/protocol compatibility readiness reporting.

### Changed

- Package, protocol, and schema compatibility versions advance to `0.2.0`.

## Package [0.1.0] - 2026-07-25

### Added

- `uv`-managed Python 3.13+ pure-Python package and locked dependencies.
- Typed `SimulationSdk` readiness facade, DTOs, errors, and service ports.
- Injectable clocks, secure/deterministic random sources, structured JSON logging,
  and central redaction.
- Repository, structure, source-size, traceability, CI, secret, and import-boundary
  quality controls.
- Unit, integration, contract, property, security, performance, and chaos test
  foundations.

### Repository hygiene

- Stopped tracking generated PDF analysis and the reference checkout under `tmp/`;
  both remain available locally and are protected from future commits by
  `.gitignore`.

## [1.0.0] - 2026-07-25

### Added

- Authoritative product requirements, architecture plan, and 645-task execution backlog.
- Source ledger with PDF SHA-256, 160-page map, root engineering authority, and informative reference revision.
- Complete traceability for 227 requirements, 55 Appendix E rules, and 32 Appendix F quantitative parameters.
- Assumption, ambiguity, governance, threat, risk, KPI/evidence, and experiment policies.
- Accepted ADR-001 through ADR-005.
- Seven per-mechanism PRD outlines with implementation entry gates.
- Formal M0 consistency review and approval record.

### Corrected

- Reclassified technical-loss zero scoring as a mandatory terminal outcome rather than a nonexistent Appendix F parameter row.
- Aligned PRD, PLAN, and TODO on the same M0-M13 milestone identities.
- Added accountable components for configuration, league, reporting, observability, experiments, release, CI, and architecture policy.

### Baseline

- Documentation baseline `1.0.0` is frozen and approved for M1 entry.
- No software implementation readiness or final project `READY` status is implied.
