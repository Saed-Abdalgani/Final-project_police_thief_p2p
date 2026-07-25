# Changelog

All notable project changes are documented here. The project follows semantic versioning for documentation, package, protocol, config, and schema contracts, with compatibility recorded separately when those versions diverge.

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
