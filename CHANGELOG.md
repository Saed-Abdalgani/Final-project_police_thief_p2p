# Changelog

All notable project changes are documented here. The project follows semantic versioning for documentation, package, protocol, config, and schema contracts, with compatibility recorded separately when those versions diverge.

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
