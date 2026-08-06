# Implementation Backlog

## Distributed Cops-and-Robbers over a Peer-to-Peer Network

| Field | Value |
|---|---|
| Backlog version | 1.0.0 |
| Date | 2026-07-25 |
| Total planned subtasks | 645 |
| Status vocabulary | `[ ]` not started, `[-]` in progress, `[x]` complete, `[!]` blocked |
| Priorities | P0 release/compliance blocker, P1 competitive/core quality, P2 enhancement |
| Requirements | `docs/PRD.md` |
| Architecture | `docs/PLAN.md` |

## Working rules

- Tasks are ordered by dependency within each milestone unless an explicit dependency is shown.
- A task is not complete merely because code exists. Its stated evidence must exist and pass.
- P0 tasks block milestone exit and final release.
- Every implementation task follows Red -> Green -> Refactor when practical.
- All Python dependency operations use `uv`.
- All GUI, CLI, MCP, replay, and integration entry points use `SimulationSdk`.
- All MCP, Gmail, and optional remote LLM calls use the central Gatekeeper.
- New public functions and methods require tests and docstrings.
- Global coverage must stay at or above 85%; critical rule, crypto, state-machine, and config code targets 100% branch coverage.
- Source files should stay at or below 150 actual code lines unless an ADR explicitly justifies an exception.
- Evidence belongs in `results/`, charts/screenshots in `assets/`, and mechanism documentation in `docs/`.

## Global Definition of Done

A checked task has:

1. A linked PRD requirement or documented architecture rationale.
2. Passing tests for success, boundaries, invalid input, failure, and external-dependency failure as applicable.
3. Ruff and strict type checks passing.
4. No secret, unsafe path, unbounded wait, hard-coded configurable value, or local-truth leak.
5. SDK and Gatekeeper boundaries preserved.
6. Documentation, examples, and schemas updated.
7. Reproducible evidence committed in the correct location.

## Milestone map

| Milestone | Task range | Count | Exit outcome |
|---|---:|---:|---|
| M0 Governance and traceability | T001-T040 | 40 | Normative implementation contract approved |
| M1 Foundation and tooling | T041-T075 | 35 | Clean clone installs, lints, types, and tests |
| M2 Configuration and contracts | T076-T120 | 45 | Signed/private config and schemas are unambiguous |
| M3 Domain physics and scoring | T121-T165 | 45 | Deterministic local game core passes properties |
| M4 Peer protocol and negotiation | T166-T215 | 50 | Two isolated localhost peers interoperate |
| M5 Cryptography and audit | T216-T265 | 50 | Valid games verify; mutations fail closed |
| M6 Scent and belief | T266-T310 | 45 | Calibrated local belief works without truth leakage |
| M7 Competitive strategy | T311-T380 | 70 | Advanced role policies beat baseline on holdout |
| M8 Orchestration and reliability | T381-T425 | 45 | Faults terminate or recover without deadlock |
| M9 Artifacts, reporting, Gatekeeper | T426-T470 | 45 | Four artifacts and safe durable reporting work |
| M10 GUI and replay | T471-T510 | 40 | Local-truth live view and tamper-aware replay pass |
| M11 QA, security, and performance | T511-T570 | 60 | Full quality and adversarial gates pass |
| M12 Experiments and league optimization | T571-T615 | 45 | Frozen policy and remote dress rehearsal succeed |
| M13 Documentation and submission | T616-T645 | 30 | Two tagged repositories and submission package ready |

---

## M0 - Governance and traceability (T001-T040)

**Exit gate:** all source rules, assumptions, sanctions, requirement IDs, ownership, and evidence methods are reviewable before implementation.

- [x] **T001 [P0]** Record the SHA-256 checksum, page count, version, and filesystem path of the supplied PDF in `docs/SOURCES.md`; evidence: reproducible checksum command and output.
- [x] **T002 [P0]** Record the root `system prompt.txt` as the engineering authority in `docs/SOURCES.md`; evidence: precedence statement matches PRD section 2.
- [x] **T003 [P0]** Record reference repository URL, inspected commit `960499fd5e8777b4929625f5d8fdcf2ab4677b54`, and informative-only status; evidence: source ledger entry.
- [x] **T004 [P0]** Build a page-to-topic map for all 160 PDF pages; evidence: every page range is assigned to a chapter/appendix.
- [x] **T005 [P0]** Transcribe all 55 Appendix E rules into a machine-checkable traceability table; evidence: unique rule numbers 1-55 with no gaps.
- [x] **T006 [P0]** Transcribe every Appendix F parameter, default, status, and config key into the traceability table; evidence: peer review against rendered pages 152-155.
- [x] **T007 [P0]** Define the normative precedence rule for PDF examples versus Appendix F values; evidence: decision recorded in PRD and ADR register.
- [x] **T008 [P0]** Create `docs/ASSUMPTIONS.md` with every implementation assumption from PRD section 8; evidence: owner and validation date per assumption.
- [x] **T009 [P0]** Create `docs/AMBIGUITIES.md` and seed barrier/STAY, scent-kernel, role-alternation, recovery, and LLM-move ambiguities; evidence: chosen interpretation and rationale per item.
- [x] **T010 [P0]** Define the controlled vocabulary for peer, group, role, series, sub-game, local truth, and objective state; evidence: glossary used consistently across documents.
- [x] **T011 [P0]** Assign stable IDs to every functional and non-functional requirement; evidence: duplicate-ID check passes.
- [x] **T012 [P0]** Map every PRD requirement to one planned component in PLAN; evidence: no orphan requirement in traceability report.
- [x] **T013 [P0]** Map every PRD requirement to at least one TODO task; evidence: automated link report has zero missing requirements.
- [x] **T014 [P0]** Define stakeholders and approval roles for architecture, QA, security, strategy, and submission; evidence: RACI table.
- [x] **T015 [P0]** Define change-control rules for shared config/protocol/schema changes; evidence: versioning and approval workflow.
- [x] **T016 [P0]** Define the violation severity taxonomy: invalid input, technical loss, tamper forfeit, project disqualification; evidence: mapping to Appendix E sanctions.
- [x] **T017 [P0]** Define data classifications for public, shared-signed, local-private, secret, and post-audit evidence; evidence: classification matrix.
- [x] **T018 [P0]** Define retention rules for operational logs, official artifacts, nonces, OAuth files, and tournament outputs; evidence: lifecycle table.
- [x] **T019 [P0]** Define the local-truth invariant in a standalone architecture rule; evidence: forbidden-field examples and enforcement strategy.
- [x] **T020 [P0]** Define the "no shared live state" invariant for development and league runs; evidence: permitted/prohibited communication table.
- [x] **T021 [P0]** Create the initial threat model with assets, actors, boundaries, threats, and controls; evidence: STRIDE-style coverage of all remote boundaries.
- [x] **T022 [P0]** Create the initial risk register with probability, impact, owner, mitigation, trigger, and contingency; evidence: all critical PRD risks included.
- [x] **T023 [P0]** Define measurable compliance, reliability, strategy, performance, cost, and quality KPIs; evidence: units and evidence source for each KPI.
- [x] **T024 [P0]** Define acceptance evidence types: automated test, artifact, screenshot, benchmark, manual inspection, or external confirmation; evidence: each requirement uses one.
- [x] **T025 [P0]** Create `docs/DECISIONS.md` with ADR template and index; evidence: template includes context, options, decision, consequences, status.
- [x] **T026 [P0]** Draft ADR-001 for SDK-only business logic access; evidence: accepted boundary and consequences.
- [x] **T027 [P0]** Draft ADR-002 for ports-and-adapters architecture; evidence: dependency direction diagram.
- [x] **T028 [P0]** Draft ADR-003 for two standalone exported role repositories; evidence: drift and isolation trade-offs documented.
- [x] **T029 [P0]** Draft ADR-004 for canonical JSON and SHA-256; evidence: exact byte rules identified.
- [x] **T030 [P0]** Draft ADR-005 for at-least-once delivery with exactly-once effects; evidence: idempotency strategy documented.
- [x] **T031 [P0]** Create outlines for all seven required mechanism PRDs; evidence: scope, inputs, outputs, invariants, acceptance placeholders.
- [x] **T032 [P0]** Create an academic-integrity and reference-code usage policy; evidence: permitted reuse and required attribution documented.
- [x] **T033 [P0]** Define the two-repository release and cross-linking policy; evidence: naming, branch, tag, access, and export rules.
- [x] **T034 [P0]** Define the counted-match ledger policy, including warmups and one-counted-match-per-opponent; evidence: state model.
- [x] **T035 [P0]** Define the exact final readiness decision rubric (`READY`, `CONDITIONALLY READY`, `NOT READY`); evidence: root checklist fields match system prompt.
- [x] **T036 [P1]** Define competitive baseline agents and official comparison metrics; evidence: reference, random, scripted, and previous-version baselines listed.
- [x] **T037 [P1]** Define train, validation, and holdout fixture separation; evidence: seed/adversary leakage policy.
- [x] **T038 [P1]** Define experiment reproducibility metadata; evidence: required commit, config, seed, hardware, runtime, and metrics fields.
- [x] **T039 [P0]** Conduct a formal PRD/PLAN consistency review; evidence: closed review checklist with all discrepancies resolved.
- [x] **T040 [P0]** Freeze documentation baseline v1.0.0 and record approval; evidence: changelog entry and no unresolved P0 specification issue.

---

## M1 - Foundation and tooling (T041-T075)

**Exit gate:** a clean clone uses `uv` to install, lint, type-check, test, and build the SDK shell on supported systems.

- [x] **T041 [P0]** Initialize Git in the canonical workspace without modifying user-owned external files; evidence: clean repository root and initial status.
- [x] **T042 [P0]** Create `.gitignore` before credentials or runtime artifacts exist; evidence: `.env`, `credentials.json`, `token.json`, keys, logs, caches, results, and IDE files covered.
- [x] **T043 [P0]** Initialize the Python project with `uv` and package name `police_thief_p2p`; evidence: valid `pyproject.toml`.
- [x] **T044 [P0]** Set Python requirement to 3.13+ and document supported interpreters; evidence: `requires-python` and README agree.
- [x] **T045 [P0]** Create the complete root directory skeleton required by `system prompt.txt`; evidence: structure audit passes.
- [x] **T046 [P0]** Create `src/police_thief_p2p/__init__.py` with package docstring and public version export; evidence: import test.
- [x] **T047 [P0]** Create `sdk`, `services`, `adapters`, and `shared` package boundaries; evidence: architecture import test.
- [x] **T048 [P0]** Create `tests/unit`, `integration`, `contract`, `property`, `security`, `performance`, `chaos`, and `fixtures`; evidence: pytest discovers placeholders.
- [x] **T049 [P0]** Add runtime dependencies only through `uv add`; evidence: dependency rationale recorded and lockfile updated.
- [x] **T050 [P0]** Add pytest, pytest-cov, Hypothesis, Ruff, and mypy through `uv add --dev`; evidence: frozen sync succeeds.
- [x] **T051 [P0]** Configure Ruff lint rules, format settings, Python target, and exclusions; evidence: `uv run ruff check .` passes.
- [x] **T052 [P0]** Configure strict mypy for source and typed test helpers; evidence: `uv run mypy src tests` passes.
- [x] **T053 [P0]** Configure pytest markers, deterministic defaults, and coverage threshold 85%; evidence: intentional sub-threshold run fails.
- [x] **T054 [P0]** Create `shared/version.py` with semantic package/protocol/schema versions; evidence: unit tests for valid formatting.
- [x] **T055 [P0]** Create `constants.py` containing only true non-configurable constants; evidence: config-value audit finds no runtime tunables.
- [x] **T056 [P0]** Create the initial `SimulationSdk` facade with typed no-op readiness method; evidence: CLI-style caller uses SDK only.
- [x] **T057 [P0]** Create SDK DTO and typed error modules; evidence: serialization/repr tests confirm safe output.
- [x] **T058 [P0]** Define service port protocols for clock, RNG, transport, repository, language, email, and system info; evidence: mypy structural-conformance tests.
- [x] **T059 [P0]** Implement injectable system and fake monotonic clocks; evidence: deadline tests run without sleeping.
- [x] **T060 [P0]** Implement injectable cryptographic and deterministic test random sources; evidence: production source cannot be seeded accidentally.
- [x] **T061 [P0]** Create structured logging configuration with correlation context; evidence: JSON log fixture validates.
- [x] **T062 [P0]** Implement central redaction helpers for secrets, tokens, URLs, email, and payload fields; evidence: parameterized leakage tests.
- [x] **T063 [P0]** Create `.env-example` with safe placeholders and descriptions; evidence: secret scanner reports no credential-like values.
- [x] **T064 [P0]** Add pre-commit configuration for Ruff, formatting, secret scan, and basic file hygiene; evidence: hook suite passes.
- [x] **T065 [P0]** Add CI workflow for frozen `uv` sync, lint, format, types, unit tests, and coverage; evidence: workflow syntax validation.
- [x] **T066 [P0]** Add a Windows CI matrix with a macOS smoke job where available; evidence: platform matrix documented.
- [x] **T067 [P0]** Add repository-structure validation script invoked through `uv run python`; evidence: missing required file causes failure.
- [x] **T068 [P0]** Add source-file code-line counter with 150-line warnings/fail policy; evidence: synthetic oversized fixture detected.
- [x] **T069 [P0]** Add requirement/task ID validator for docs and tests; evidence: duplicate/missing synthetic IDs detected.
- [x] **T070 [P0]** Create `README.md` skeleton with install, usage, config, examples, troubleshooting, contribution, credits, and license sections.
- [x] **T071 [P0]** Add `LICENSE`, `CREDITS.md`, and `CHANGELOG.md` placeholders with reference-code attribution policy.
- [x] **T072 [P0]** Create package build configuration using `uv_build`; evidence: wheel builds and installs in a clean temporary environment.
- [x] **T073 [P0]** Add an import-boundary test preventing domain/services imports from CLI, GUI, FastMCP, or Gmail adapters.
- [x] **T074 [P0]** Run the foundation command suite from a clean clone; evidence: archived CI-equivalent transcript.
- [x] **T075 [P0]** Tag the foundation milestone internally and update readiness status; evidence: M1 exit checklist signed.

---

## M2 - Configuration and contracts (T076-T120)

**Exit gate:** shared/private configuration, identifiers, canonicalization, and all external schemas are strict, versioned, and backed by golden vectors.

- [x] **T076 [P0]** Write `docs/PRD_BASE_LOGIC.md` configuration assumptions section before config code; evidence: reviewed parameter ownership.
- [x] **T077 [P0]** Define typed `GroupId` with exact eight-character submission mode and safe general development mode; evidence: boundary tests.
- [x] **T078 [P0]** Define safe `GameId` slug grammar and maximum length; evidence: traversal and Unicode-confusable tests.
- [x] **T079 [P0]** Define UUID-backed `GameUid`, `MessageId`, and `CorrelationId`; evidence: parsing and generation tests.
- [x] **T080 [P0]** Define typed `SubGameNumber` and `StepNumber` with valid ranges; evidence: zero/negative/overflow rejection tests.
- [x] **T081 [P0]** Create JSON Schema for shared `game.json`; evidence: every Appendix F key is required.
- [x] **T082 [P0]** Set `additionalProperties: false` outside namespaced extensions; evidence: unknown-key rejection test.
- [x] **T083 [P0]** Encode board/coordinate/start fields and constraints in schema; evidence: default 7x7 example validates.
- [x] **T084 [P0]** Encode world/map-area/hint-cap fields in schema; evidence: length and word-cap boundaries.
- [x] **T085 [P0]** Encode movement/barrier/step/survival fields in schema; evidence: diagonal move-set fixture rejected.
- [x] **T086 [P0]** Encode fixed scoring fields in schema; evidence: each one-field mutation rejected by semantic validation.
- [x] **T087 [P0]** Encode scent center/decay/window fields in schema; evidence: fixed-value mutations rejected.
- [x] **T088 [P0]** Encode league count/diversity/token/max-match fields in schema; evidence: six-game default example.
- [x] **T089 [P0]** Encode Gatekeeper rate/concurrency/backoff/retry/queue/timeout fields in schema; evidence: positive-range tests.
- [x] **T090 [P0]** Implement typed shared-config models separate from JSON parsing; evidence: model construction tests.
- [x] **T091 [P0]** Implement fixed-parameter enforcement table from Appendix F; evidence: table-driven tests cover every fixed key.
- [x] **T092 [P0]** Implement minimum-parameter direction rules per key; evidence: below-threshold rejection and stricter-value acceptance.
- [x] **T093 [P0]** Implement negotiable defaults exactly as Appendix F; evidence: omitted values resolve to documented defaults.
- [x] **T094 [P0]** Implement cross-field validation for starts within board and distinct/legal initial state; evidence: invalid-start matrix.
- [x] **T095 [P0]** Implement coordinate-origin and start-index conversion model; evidence: all four origin corners and indexes 0/1 round-trip.
- [x] **T096 [P0]** Define the exact signed 5x5 scent kernel/formula representation; evidence: golden numeric example reviewed.
- [x] **T097 [P0]** Add shared config field for scent interoperability/rounding policy; evidence: two independent implementations match vectors.
- [x] **T098 [P0]** Create private `game.toml` typed model; evidence: example covers identity, network, paths, strategy, language, email, and GUI.
- [x] **T099 [P0]** Ensure private model rejects shared game-rule fields in unsafe sections; evidence: weakening attempt fails.
- [x] **T100 [P0]** Implement shared JSON loader with duplicate-key, size, depth, NaN, and encoding rejection; evidence: hostile fixture suite.
- [x] **T101 [P0]** Implement private TOML loader with source-path-aware errors; evidence: malformed TOML reports safe location.
- [x] **T102 [P0]** Implement `EffectiveConfig` merge where shared values always win; evidence: provenance assertions per merged field.
- [x] **T103 [P0]** Implement environment-variable resolution for secrets only; evidence: ordinary game rules cannot be overridden by environment.
- [x] **T104 [P0]** Implement config error codes and exact JSON/TOML path messages; evidence: snapshot tests contain no secret values.
- [x] **T105 [P0]** Specify canonical JSON: UTF-8, sorted keys, fixed separators, finite values, normalized types; evidence: ADR-004 finalized.
- [x] **T106 [P0]** Implement canonical JSON serializer; evidence: byte-for-byte golden vectors pass across repeated runs.
- [x] **T107 [P0]** Implement config SHA-256 digest helper using canonical bytes; evidence: expected digest vector.
- [x] **T108 [P0]** Implement byte-identical raw-file comparison alongside canonical semantic digest; evidence: whitespace-only mismatch behavior documented/tested.
- [x] **T109 [P0]** Create `game.example.json` with all binding defaults and six sub-games; evidence: schema and semantic validation pass.
- [x] **T110 [P0]** Create `game.example.toml` with safe local defaults and comments; evidence: loader and redacted display pass.
- [x] **T111 [P0]** Create `rate_limits.example.json` for per-service Gatekeeper profiles; evidence: no rate is hard-coded in source.
- [x] **T112 [P0]** Create declaration JSON Schema draft; evidence: valid/invalid example fixtures.
- [x] **T113 [P0]** Create per-sub-game config artifact JSON Schema draft; evidence: config digest and role fields required.
- [x] **T114 [P0]** Create log artifact JSON Schema draft; evidence: ordered sealed-step and audit fields required.
- [x] **T115 [P0]** Create final result JSON Schema draft; evidence: commits, tokens, scores, links, and agreement required.
- [x] **T116 [P0]** Create common protocol-envelope schema; evidence: version, IDs, sender, sequence, and payload enforced.
- [x] **T117 [P0]** Create configuration conformance-vector directory with canonical bytes/digests; evidence: manifest lists every vector.
- [x] **T118 [P0]** Add property tests for config round-trip and canonicalization idempotence; evidence: Hypothesis campaign passes.
- [x] **T119 [P0]** Add config compatibility report to SDK readiness command; evidence: human and JSON outputs.
- [x] **T120 [P0]** Complete M2 contract review with Appendix F rendered pages; evidence: independent reviewer signs no omissions.

---

## M3 - Domain physics and scoring (T121-T165)

**Exit gate:** the deterministic, network-free domain engine enforces all board, barrier, capture, survival, and scoring rules through the SDK.

- [x] **T121 [P0]** Finalize `docs/PRD_BASE_LOGIC.md` before domain implementation; evidence: accepted inputs, outputs, invariants, and acceptance cases.
- [x] **T122 [P0]** Define immutable `Position` value object with row/column semantics; evidence: equality, hashing, and bounds-independent tests.
- [x] **T123 [P0]** Define `Direction` enum containing only N, S, E, W; evidence: diagonal/unknown parsing fails.
- [x] **T124 [P0]** Define `ActionType` and immutable `Action` for MOVE, STAY, and BARRIER; evidence: invalid field combinations rejected.
- [x] **T125 [P0]** Define `Role` enum and opponent-role helper; evidence: symmetry tests.
- [x] **T126 [P0]** Implement board coordinate normalization for negotiated origin/index; evidence: conversion golden matrix.
- [x] **T127 [P0]** Implement board bounds and cell iteration; evidence: property count equals `grid_size^2`.
- [x] **T128 [P0]** Implement orthogonal neighbor generation; evidence: corner/edge/interior cardinalities.
- [x] **T129 [P0]** Implement public immutable barrier set; evidence: duplicate insertion is idempotent and removal unavailable.
- [x] **T130 [P0]** Implement legal movement generation including STAY; evidence: barriers and edges filter moves correctly.
- [x] **T131 [P0]** Reject diagonal, multi-cell, out-of-bounds, and barrier-crossing actions; evidence: table-driven invalid-action tests.
- [x] **T132 [P0]** Implement shortest-path distance over current public barriers; evidence: BFS golden boards.
- [x] **T133 [P1]** Implement connected-component and reachable-region helpers; evidence: graph fixtures.
- [x] **T134 [P1]** Implement articulation-point detection for board graph; evidence: known graph cases.
- [x] **T135 [P1]** Implement vertex-disjoint escape-route approximation; evidence: corridor and open-board fixtures.
- [x] **T136 [P0]** Define immutable local game-state model with no opponent true-position field; evidence: type/API privacy inspection.
- [x] **T137 [P0]** Implement initial local state for Police profile; evidence: negotiated start and zero barriers used.
- [x] **T138 [P0]** Implement initial local state for Thief profile; evidence: negotiated start and no barrier capability.
- [x] **T139 [P0]** Implement deterministic movement transition for own state; evidence: pre/post invariants.
- [x] **T140 [P0]** Implement Police barrier candidate generation for current/adjacent cells; evidence: exact legal target sets.
- [x] **T141 [P0]** Enforce "barrier instead of movement" as one action; evidence: combined action rejected.
- [x] **T142 [P0]** Enforce configured Police barrier quota; evidence: quota boundary and over-quota rejection.
- [x] **T143 [P0]** Enforce barrier permanence and universal impassability; evidence: both roles' move generation respects barrier.
- [x] **T144 [P0]** Implement public barrier event carrying exact target; evidence: event serialization test.
- [x] **T145 [P0]** Implement direct landing capture predicate; evidence: equal/different position cases.
- [x] **T146 [P0]** Implement barrier-on-Thief-cell capture predicate for audit/offline resolution; evidence: Appendix E rule 46 test.
- [x] **T147 [P0]** Implement enclosure capture using spatial escape actions excluding STAY; evidence: Appendix E rule 47 edge/corner/corridor tests.
- [x] **T148 [P0]** Implement survival-threshold terminal predicate; evidence: threshold-1, threshold, threshold+1 cases.
- [x] **T149 [P0]** Implement maximum-step terminal predicate; evidence: exact configured ceiling behavior.
- [x] **T150 [P0]** Define typed terminal reasons: capture, barrier capture, enclosure, survival, step ceiling, technical, tamper, stopped.
- [x] **T151 [P0]** Implement fixed capture scoring 20/5; evidence: immutable table tests.
- [x] **T152 [P0]** Implement fixed survival scoring 5/10; evidence: immutable table tests.
- [x] **T153 [P0]** Implement technical/tamper zero-score mapping without conflating reasons; evidence: outcome tests.
- [x] **T154 [P0]** Implement fixed series tie score 2/2; evidence: equal/non-equal totals.
- [x] **T155 [P0]** Implement per-group score aggregation across six sub-games; evidence: role alternation does not swap group totals.
- [x] **T156 [P0]** Implement role assignment schedule for balanced six-sub-game series; evidence: each group receives three games per role.
- [x] **T157 [P0]** Implement one deterministic domain transition API returning state plus public events; evidence: no adapter imports.
- [x] **T158 [P0]** Expose domain simulation use cases only through `SimulationSdk`; evidence: boundary test blocks direct adapter access.
- [x] **T159 [P0]** Add unit tests for every public domain function and method; evidence: public-API inventory reaches 100%.
- [x] **T160 [P0]** Add Hypothesis properties for legal action closure and state invariants; evidence: >=10,000 generated examples.
- [x] **T161 [P0]** Add metamorphic tests for coordinate-origin/index transformations; evidence: equivalent games produce equivalent normalized transitions.
- [x] **T162 [P0]** Add deterministic one-process sub-game simulator for tests only; evidence: same seed/config produces byte-identical event sequence.
- [x] **T163 [P0]** Add golden scenarios for direct capture, barrier capture, enclosure, survival, technical loss, and tie.
- [x] **T164 [P0]** Benchmark board transitions and path helpers on legal minimum/expanded boards; evidence: results under `results/benchmarks/`.
- [x] **T165 [P0]** Complete M3 domain review against Appendix E rules 11-16 and 46-48; evidence: signed exit checklist.

---

## M4 - Peer protocol and negotiation (T166-T215)

**Exit gate:** two independently rooted processes negotiate and complete a basic sub-game over localhost through versioned FastMCP tools, with idempotent effects and no shared state.

- [x] **T166 [P0]** Finalize `docs/PRD_MCP_INFRASTRUCTURE.md` before protocol code; evidence: tool contracts, phases, idempotency, and failure semantics approved.
- [x] **T167 [P0]** Freeze the minimal FastMCP tool inventory and semantic versions; evidence: `docs/PROTOCOL.md` lists request/response ownership.
- [x] **T168 [P0]** Implement common immutable protocol envelope DTO; evidence: round-trip tests for all IDs, versions, sender, sub-game, step, and payload.
- [x] **T169 [P0]** Implement strict envelope parsing with size, depth, string, collection, and finite-number limits; evidence: hostile payload tests.
- [x] **T170 [P0]** Implement the FastMCP server adapter as a thin SDK caller; evidence: import test shows no domain-service access.
- [x] **T171 [P0]** Implement the FastMCP client adapter behind the transport port; evidence: fake-transport contract tests.
- [x] **T172 [P0]** Implement `health_v1` liveness response; evidence: it exposes no game/private state.
- [x] **T173 [P0]** Implement capability/readiness response with protocol, schema, tool, and role versions; evidence: compatibility fixture.
- [x] **T174 [P0]** Route every outbound MCP call through an initial Gatekeeper facade; evidence: direct client calls outside Gatekeeper fail boundary test.
- [x] **T175 [P0]** Implement inbound handler pipeline for parse, session, identity, idempotency, phase, persist, SDK, and response; evidence: pipeline-order test.
- [x] **T176 [P0]** Implement in-memory session registry interface keyed by validated `GameUid`; evidence: unknown-session request fails safely.
- [x] **T177 [P0]** Define match-proposal request/response schema; evidence: includes identities, repositories, commits, URLs, counted totals, config/scent digests, and versions.
- [x] **T178 [P0]** Implement `propose_match_v1` SDK command and MCP handler; evidence: accepted proposal is durably represented without starting play.
- [x] **T179 [P0]** Implement `accept_match_v1` SDK command and MCP handler; evidence: exact proposal digest required.
- [x] **T180 [P0]** Validate eight-character league group IDs during counted negotiation; evidence: invalid ID prevents counted mode.
- [x] **T181 [P0]** Validate truthful counted-game declaration shape and local-ledger consistency; evidence: mismatch is flagged before play.
- [x] **T182 [P0]** Require exact played Git commit hashes for both group artifacts; evidence: missing/dirty/invalid values reject counted proposal.
- [x] **T183 [P0]** Validate all four repository URLs required for the two groups; evidence: malformed or incomplete link set rejected.
- [x] **T184 [P0]** Validate both public MCP URLs and prohibit credential-bearing URLs; evidence: redaction and scheme tests.
- [x] **T185 [P0]** Compare raw shared-config bytes where exchanged; evidence: one-byte mismatch refuses the match.
- [x] **T186 [P0]** Compare canonical shared-config digest; evidence: semantic mismatch identifies `config_sha256`.
- [x] **T187 [P0]** Compare signed scent-model digest and numeric-vector version; evidence: mismatched kernel refuses play.
- [x] **T188 [P0]** Define Step-0 declaration payload contract for later cryptographic sealing; evidence: all PRD FR-NEG-006 fields represented.
- [x] **T189 [P0]** Implement deterministic shared `game_id` proposal and UUID `game_uid` agreement; evidence: both peers converge or fail closed.
- [x] **T190 [P0]** Negotiate and persist the six-sub-game role schedule; evidence: each group gets three Police and three Thief assignments.
- [x] **T191 [P0]** Model warmup versus counted match as an explicit signed term; evidence: warmup cannot update counted ledger.
- [x] **T192 [P0]** Reject counted negotiation after ten prior counted opponents; evidence: boundary tests at 9, 10, and 11.
- [x] **T193 [P0]** Reject a second counted match against the same group while allowing named warmups; evidence: ledger tests.
- [x] **T194 [P0]** Implement protocol-version compatibility negotiation; evidence: compatible minor and incompatible major fixtures.
- [x] **T195 [P1]** Implement namespaced optional-capability negotiation without weakening mandatory rules; evidence: unknown optional extension ignored/rejected per version policy.
- [x] **T196 [P0]** Define idempotency repository port and record model; evidence: key includes game, sender, and message ID.
- [x] **T197 [P0]** Implement durable file-backed idempotency repository; evidence: response survives process restart.
- [x] **T198 [P0]** Reject reuse of one message ID with a different request digest; evidence: conflict produces protocol violation without mutation.
- [x] **T199 [P0]** Implement monotonic per-sender sequence validation; evidence: duplicate, gap, old, and future sequence cases.
- [x] **T200 [P0]** Implement phase/precondition validator callable before every mutating SDK command; evidence: illegal phase matrix.
- [x] **T201 [P0]** Persist mutating request intent and result before returning acknowledgement; evidence: crash-boundary integration test.
- [x] **T202 [P0]** Configure FastMCP request body and concurrency ceilings from config; evidence: oversize/overload requests reject safely.
- [x] **T203 [P0]** Define stable protocol error codes for validation, identity, phase, sequence, conflict, timeout, and internal failure.
- [x] **T204 [P0]** Map unexpected exceptions to correlation-safe responses without stack traces or secrets; evidence: redaction snapshot test.
- [x] **T205 [P0]** Apply monotonic request deadlines to every outbound MCP call; evidence: fake clock timeout test without sleep.
- [x] **T206 [P0]** Ensure mutation retries reuse the same idempotency key and request bytes; evidence: transport retry creates one effect.
- [x] **T207 [P0]** Implement bounded handling for out-of-order messages according to documented policy; evidence: no unbounded buffer.
- [x] **T208 [P0]** Create a dual-process localhost test runner using separate commands and environments; evidence: OS process IDs differ.
- [x] **T209 [P0]** Assign separate config, artifact, cache, and temporary roots to each test peer; evidence: path audit proves isolation.
- [x] **T210 [P0]** Make peer startup order independent through bounded health/readiness retries; evidence: A-first and B-first tests.
- [x] **T211 [P0]** Run one basic localhost sub-game entirely through MCP/SDK; evidence: both event sequences reach the same public outcome.
- [x] **T212 [P0]** Add negotiation mismatch integration tests for config, scent, version, group, role schedule, and game UID.
- [x] **T213 [P0]** Add duplicate/reordered/delayed delivery integration tests; evidence: exactly-once effects and correct errors.
- [x] **T214 [P0]** Publish protocol examples and interoperability checklist in `docs/PROTOCOL.md`; evidence: examples validate against schemas.
- [x] **T215 [P0]** Complete M4 review against Appendix E rules 1-6, 10-12, 31, 37-38, and 52; evidence: signed exit checklist.

---

## M5 - Cryptography and mutual audit (T216-T265)

**Exit gate:** negotiation, each step, capture response, configuration, and final result are digest-bound; valid logs verify and every mutation family fails closed.

- [x] **T216 [P0]** Finalize `docs/PRD_CRYPTO_AUDIT.md` before crypto code; evidence: payloads, nonce lifecycle, audit order, and sanctions approved.
- [x] **T217 [P0]** Finalize ADR-004 canonical JSON/hash decision with golden bytes; evidence: no unresolved serialization choice.
- [x] **T218 [P0]** Implement production nonce generator using OS CSPRNG through `secrets`; evidence: no use of `random` in crypto modules.
- [x] **T219 [P0]** Enforce at least 128 bits of nonce entropy; evidence: length/format tests and static assertion.
- [x] **T220 [P0]** Define opaque `SecretNonce` type whose repr/string is redacted; evidence: logging/repr tests.
- [x] **T221 [P0]** Add global log filter for nonce and signing-key field names; evidence: nested payload leakage tests.
- [x] **T222 [P0]** Define versioned immutable commitment payload model containing every outcome-relevant field.
- [x] **T223 [P0]** Implement canonical commitment payload serialization; evidence: field-order and platform-independent vectors.
- [x] **T224 [P0]** Implement SHA-256 commitment digest creation; evidence: golden expected hash.
- [x] **T225 [P0]** Implement constant-time digest comparison with `secrets.compare_digest`; evidence: code-path assertion.
- [x] **T226 [P0]** Publish cross-repository commitment conformance vectors; evidence: both role builds calculate identical digests.
- [x] **T227 [P0]** Implement local sealed-step store separating secret payload from public commitment; evidence: access-control tests.
- [x] **T228 [P0]** Implement acknowledgement lock that makes committed payload immutable; evidence: post-ack mutation attempt fails.
- [x] **T229 [P0]** Implement reveal DTO exposing action/hint/verdict/public effects but not nonce; evidence: schema forbids nonce.
- [x] **T230 [P0]** Enforce commit -> acknowledge -> reveal phase order; evidence: full illegal-order matrix.
- [x] **T231 [P0]** Implement final-reveal manifest containing each step's nonce and linkage; evidence: only terminal/auditing phase allows creation.
- [x] **T232 [P0]** Bind each commitment to a pre-action local-state digest; evidence: replaying a valid move in a different state fails audit.
- [x] **T233 [P0]** Bind negotiation to exact shared-config digest and protocol versions; evidence: config substitution test.
- [x] **T234 [P0]** Bind negotiation to scent formula, kernel, numeric example, and float policy digest; evidence: one-value mutation test.
- [x] **T235 [P0]** Implement system-information probe port and redacted DTO; evidence: unavailable fields degrade to explicit `unknown`.
- [x] **T236 [P0]** Implement CPU model/core/frequency collection with platform-safe fallbacks; evidence: Windows/Linux unit fixtures.
- [x] **T237 [P0]** Implement RAM collection with unit normalization; evidence: impossible/negative values rejected.
- [x] **T238 [P0]** Implement GPU/VRAM optional collection without mandatory vendor SDK; evidence: no-GPU path passes.
- [x] **T239 [P0]** Implement OS/platform/runtime version collection; evidence: normalized declaration output.
- [x] **T240 [P0]** Include model/provider and negotiated token estimate in Step-0; evidence: template mode declares zero operational tokens.
- [x] **T241 [P0]** Resolve and validate exact Git commit/dirty status for Step-0; evidence: counted mode rejects unknown/dirty unless explicitly documented policy permits.
- [x] **T242 [P0]** Implement Step-0 declaration model and canonical bytes; evidence: full declaration golden fixture.
- [x] **T243 [P0]** Load Step-0 signing material from secret environment/file handle only; evidence: missing key fails safely and key never serializes.
- [x] **T244 [P0]** Implement HMAC-SHA-256 or approved keyed signature for Step-0 per course key semantics; evidence: verify/tamper vectors and ADR.
- [x] **T245 [P0]** Implement sealed capture-claim message tied to committed action and step; evidence: invalid context rejected.
- [x] **T246 [P0]** Implement sealed truthful capture response without premature position disclosure; evidence: true/false cases.
- [x] **T247 [P0]** Detect false capture claim or false denial during audit and apply mandatory tamper outcome.
- [x] **T248 [P0]** Add local event-journal hash chaining for corruption detection; evidence: removal/reorder/modification test.
- [x] **T249 [P0]** Implement `AuditService` as a pure verifier over artifacts/events; evidence: no GUI/network imports.
- [x] **T250 [P0]** Verify shared config, Step-0, scent model, and role schedule before step audit; evidence: failure category tests.
- [x] **T251 [P0]** Recompute every opponent commitment from final payload and nonce; evidence: first mismatch localized.
- [x] **T252 [P0]** Verify unique monotonic step order and complete actor sequences; evidence: duplicate/gap/reorder fixtures.
- [x] **T253 [P0]** Replay every physical action through domain legality; evidence: valid hash with illegal action still fails.
- [x] **T254 [P0]** Recompute disclosed scent frames from revealed path/model; evidence: forged scent fails audit.
- [x] **T255 [P0]** Recompute capture, terminal reason, per-sub-game scores, totals, and tie; evidence: result substitution fails.
- [x] **T256 [P0]** Return structured first-failure details plus aggregate findings; evidence: deterministic finding order.
- [x] **T257 [P0]** Map any integrity mismatch to immutable `TAMPERED` state and prescribed zero/tamper sanction.
- [x] **T258 [P0]** Define serializable audit report with verified counts, digests, findings, and evidence links.
- [x] **T259 [P0]** Implement mutual exchange of audit-manifest digests; evidence: peers detect inconsistent audit inputs.
- [x] **T260 [P0]** Implement final result agreement digest over both independent audit outcomes; evidence: disagreement blocks reporting.
- [x] **T261 [P0]** Generate mutation tests that alter every commitment payload field individually; evidence: 100% detected.
- [x] **T262 [P0]** Test missing, duplicate, reordered, truncated, and foreign-game records; evidence: typed audit failures.
- [x] **T263 [P0]** Detect nonce reuse within a sub-game and across commitment identities; evidence: reuse security test.
- [x] **T264 [P0]** Run a complete valid localhost sub-game through final nonce reveal and mutual audit; evidence: both report `Verified OK`.
- [x] **T265 [P0]** Complete M5 review against Appendix E rules 17-24, 36, 46-48, and 53; evidence: signed exit checklist.

---

## M6 - Scent and Bayesian belief (T266-T310)

**Exit gate:** both peers compute interoperable scent evidence and normalized local beliefs that affect decisions without ever receiving live opponent truth.

- [x] **T266 [P0]** Finalize `docs/PRD_LANGUAGE_SCENT.md` before implementation; evidence: exact update order, likelihoods, and privacy boundaries approved.
- [x] **T267 [P0]** Finalize ADR-014 for float/quantization interoperability; evidence: tolerance and serialization rules fixed.
- [x] **T268 [P0]** Implement the exact signed 5x5 radial scent kernel/formula; evidence: center is 0.9 and all golden cells match.
- [x] **T269 [P0]** Create center, edge, corner, overlap, repeated-stay, and decay conformance vectors; evidence: both peers pass independently.
- [x] **T270 [P0]** Implement scent emission centered on the actor's local true position; evidence: center/shape tests.
- [x] **T271 [P0]** Implement board-edge clipping without kernel wraparound; evidence: corner mass fixture.
- [x] **T272 [P0]** Implement repeated emission accumulation/clamping exactly as signed; evidence: repeated-stay vector.
- [x] **T273 [P0]** Implement 0.10 decay for every cell; evidence: multi-turn numeric vector.
- [x] **T274 [P0]** Apply decay only after a complete Police-plus-Thief turn; evidence: ordering integration test.
- [x] **T275 [P0]** Implement agreed numeric quantization only at serialization/audit boundaries; evidence: internal precision and cross-platform digest tests.
- [x] **T276 [P0]** Define bounded opponent-facing `ScentFrame` DTO with game/step/model linkage.
- [x] **T277 [P0]** Bind each scent frame to the step commitment through its digest; evidence: substitution fails audit.
- [x] **T278 [P0]** Persist own hidden scent/path history in the secret local store; evidence: unavailable through live SDK view.
- [x] **T279 [P0]** Accept only opponent scent frames matching expected game, step, dimensions, range, and digest; evidence: invalid frames rejected.
- [x] **T280 [P0]** Prevent manual remote scent injection outside the actor reveal workflow; evidence: no public SDK method can set arbitrary belief evidence.
- [x] **T281 [P0]** Recompute scent history from revealed audited paths; evidence: forged frame and wrong-decay tests.
- [x] **T282 [P0]** Implement immutable `BeliefGrid` with finite non-negative cell probabilities.
- [x] **T283 [P0]** Initialize belief uniformly over legal opponent start/reachable cells; evidence: normalized prior tests.
- [x] **T284 [P0]** Mask barriers and provably impossible cells to zero; evidence: topology-change tests.
- [x] **T285 [P0]** Implement uniform legal opponent transition kernel as baseline; evidence: row-stochastic property.
- [x] **T286 [P1]** Implement mixture transition features for chase/evade, boundary, revisit, and cycle tendencies.
- [x] **T287 [P0]** Implement prediction step over board cells and local legal transitions; evidence: mass conservation property.
- [x] **T288 [P0]** Implement scent likelihood from frame/history/model with bounded noise floor; evidence: peak and contradictory observations.
- [x] **T289 [P0]** Define hint-parser port returning bounded semantic likelihood evidence, never commands.
- [x] **T290 [P1]** Implement deterministic template cue parser for direction/region/landmark categories; evidence: locale-safe fixtures.
- [x] **T291 [P0]** Treat unparseable or injection-like hints as neutral evidence; evidence: adversarial strings do not alter config/tools.
- [x] **T292 [P1]** Implement Beta-prior hint reliability state; evidence: update math vectors.
- [x] **T293 [P1]** Track reliability separately by cue category and recency; evidence: category-isolation tests.
- [x] **T294 [P0]** Cap hint likelihood ratios so one phrase cannot overwhelm scent; evidence: extreme-input bound test.
- [x] **T295 [P0]** Implement Bayesian fusion of prediction, scent, and hint evidence; evidence: hand-calculated posterior fixture.
- [x] **T296 [P1]** Use log-space normalization for very small likelihoods; evidence: long-run underflow test.
- [x] **T297 [P0]** Implement deterministic reachable-prior recovery for all-zero posterior; evidence: no NaN/empty belief.
- [x] **T298 [P0]** Normalize posterior within declared tolerance; evidence: Hypothesis invariant.
- [x] **T299 [P1]** Compute belief entropy; evidence: uniform and point-mass limits.
- [x] **T300 [P1]** Compute configurable credible region with cumulative probability target; evidence: deterministic ordering.
- [x] **T301 [P0]** Expose most-likely cell only as a diagnostic, not the sole advanced-policy input.
- [x] **T302 [P1]** Compute calibration metrics from post-audit truth for offline analysis only; evidence: no live feedback path.
- [x] **T303 [P0]** Implement one `BeliefService.update` pipeline with injectable motion/hint models.
- [x] **T304 [P0]** Add redacted belief summary to `LocalView`; evidence: heatmap/entropy present, opponent truth absent.
- [x] **T305 [P0]** Add property tests for normalization, finiteness, masks, determinism, and transition mass.
- [x] **T306 [P0]** Add contradictory scent-versus-hint scenarios and assert scent-dominant bounded update.
- [x] **T307 [P0]** Add edge/corner/barrier/topology-change belief tests.
- [x] **T308 [P0]** Add source/DTO/log scan proving live belief code never accepts opponent true position.
- [x] **T309 [P1]** Benchmark 35-step belief updates on minimum and expanded boards; evidence: p95 stored in results.
- [x] **T310 [P0]** Complete M6 review against Appendix E rules 8-9 and 23 plus PRD FR-BEL; evidence: signed exit checklist.

---

## M7 - Competitive strategy and language policy (T311-T380)

**Exit gate:** frozen Police and Thief policies are safe, deterministic under seed, deadline-bounded, and materially stronger than the reference greedy strategy on held-out role-swapped fixtures.

- [x] **T311 [P0]** Finalize `docs/PRD_STRATEGY.md` before advanced strategy code; evidence: interfaces, safety, evaluation, and anti-overfitting gates approved.
- [x] **T312 [P0]** Define abstract `StrategyBrain` interface using only legal actions, local state, belief, public history, config, RNG, and deadline.
- [x] **T313 [P0]** Define immutable `Decision` contract for action, hint intent, hint, reason code, metrics, and fallback flag.
- [x] **T314 [P0]** Implement role-aware strategy resolver behind the SDK; evidence: default and custom profiles load without engine edits.
- [x] **T315 [P0]** Parse `police_class` and `thief_class` selectors only from private TOML; evidence: shared/opponent input cannot set a class.
- [x] **T316 [P0]** Constrain dynamic imports to validated local package namespaces and `StrategyBrain` subclasses; evidence: arbitrary module/type rejection.
- [x] **T317 [P0]** Pass a monotonic hard deadline into every strategy call; evidence: fake-clock expiry test.
- [x] **T318 [P0]** Implement deterministic legal fallback policy for exceptions, timeout, invalid score, or empty candidate result.
- [x] **T319 [P0]** Inject seeded strategy RNG and record seed/profile version in experiment manifests.
- [x] **T320 [P0]** Implement final legality guard that can only return a domain-engine legal action; evidence: malicious strategy output tests.
- [x] **T321 [P1]** Implement posterior-expected-distance Police baseline instead of argmax-only Manhattan; evidence: hand-calculated scenario.
- [x] **T322 [P1]** Implement lower-quantile threat-distance Thief baseline instead of argmax-only distance; evidence: multimodal-belief scenario.
- [x] **T323 [P1]** Add revisit/cycle penalties to both baselines; evidence: scripted loop is broken deterministically.
- [x] **T324 [P0]** Emit safe strategy telemetry for latency, candidates, reason code, depth, fallback, and score summary.
- [x] **T325 [P1]** Define opponent-feature model for movement direction, boundary use, revisit rate, hint behavior, and barrier timing.
- [x] **T326 [P1]** Implement normalized mixture weights for uniform, chase/evade, boundary, revisit, and cycle motion models.
- [x] **T327 [P1]** Update opponent mixture weights online from legally observed revealed actions; evidence: convergence fixture.
- [x] **T328 [P1]** Add recency/change-point decay so old opponent behavior can be forgotten; evidence: strategy-switch fixture.
- [x] **T329 [P1]** Persist opponent profile between audited sub-games with exact opponent/version key; evidence: unrelated opponents remain isolated.
- [x] **T330 [P0]** Prevent unaudited hidden truth from updating opponent profiles; evidence: taint/privacy test.
- [x] **T331 [P1]** Define compact search state with own state, public topology, posterior summary/particles, role, barrier budget, and horizon.
- [x] **T332 [P1]** Define pluggable role evaluation interface and score-breakdown DTO.
- [x] **T333 [P1]** Implement iterative-deepening search that always preserves the best completed depth.
- [x] **T334 [P0]** Enforce search deadline with guard margin for commitment/persistence; evidence: no overrun in timing tests.
- [x] **T335 [P1]** Implement bounded transposition cache keyed by public/search state; evidence: deterministic hit/eviction tests.
- [x] **T336 [P1]** Implement stratified posterior/particle sampling with deterministic seed; evidence: distribution and repeatability tests.
- [x] **T337 [P1]** Sample opponent actions from the learned mixture while enforcing their legal move model.
- [x] **T338 [P1]** Implement depth-limited risk-sensitive expectimax over action/opponent-response samples.
- [x] **T339 [P1]** Add downside-tail/CVaR-style risk term to avoid high-variance suicidal choices.
- [x] **T340 [P1]** Generate all legal Police movement/stay candidates from the domain engine.
- [x] **T341 [P1]** Generate all legal Police barrier candidates from the domain engine.
- [x] **T342 [P1]** Prune barrier candidates to credible corridors, articulation candidates, frontier cuts, and immediate capture targets.
- [x] **T343 [P1]** Compute expected Thief reachable-region reduction for each Police candidate.
- [x] **T344 [P1]** Compute graph cut/corridor value and change in disjoint escape routes for barriers.
- [x] **T345 [P0]** Compute and heavily penalize Police self-isolation/loss-of-access risk.
- [x] **T346 [P1]** Compute barrier opportunity cost based on remaining quota and expected future closure value.
- [x] **T347 [P0]** Give proven immediate barrier/direct capture priority over all non-capture heuristic scores.
- [x] **T348 [P1]** Implement configurable Police score from capture, distance, escape, cut, information, self-trap, budget, and risk terms.
- [x] **T349 [P1]** Store Police tuning weights only in private strategy config with typed ranges and profile version.
- [x] **T350 [P1]** Add Police golden scenarios for interception, multimodal pursuit, corridor closure, self-trap avoidance, and quota conservation.
- [x] **T351 [P1]** Generate all legal Thief move/stay candidates from the domain engine.
- [x] **T352 [P1]** Compute risk-adjusted distance from the full Police posterior for each candidate.
- [x] **T353 [P1]** Compute future reachable-region size over a bounded horizon.
- [x] **T354 [P1]** Compute count/quality of disjoint future escape routes.
- [x] **T355 [P1]** Estimate likely Police barrier placements and resulting trap probability.
- [x] **T356 [P1]** Penalize scent concentration, revisits, and path predictability without attempting illegal scent suppression.
- [x] **T357 [P1]** Penalize corners/boundaries when future exits are insufficient rather than treating raw distance as safety.
- [x] **T358 [P1]** Reward actions expected to preserve/increase the Police's uncertainty when survival is not reduced.
- [x] **T359 [P1]** Add bounded stochastic tie-breaking only among near-equivalent safe actions.
- [x] **T360 [P1]** Implement configurable Thief score from survival, risk distance, space, routes, entropy, traps, scent, corner, and cycle terms.
- [x] **T361 [P1]** Implement prevalidated Thief behavior modes (mobility, deception, escape, anti-trap) with deterministic switch rules.
- [x] **T362 [P1]** Add Thief golden scenarios for open-board mobility, false-far corner, barrier funnel, scent loop, and multimodal threat.
- [x] **T363 [P1]** Define hint-intent policy separate from movement and surface realization.
- [x] **T364 [P1]** Compute strategic value of an honest hint under current trust/posterior context.
- [x] **T365 [P1]** Compute plausible deceptive semantic region that pulls belief away without numeric coordinate encoding.
- [x] **T366 [P1]** Implement trust-aware lie scheduling that avoids repetitive impossible deception.
- [x] **T367 [P0]** Implement deterministic map-area-aware natural-language templates for each semantic cue.
- [x] **T368 [P0]** Enforce negotiated word cap after every template or model output; evidence: punctuation/Unicode tokenization cases documented.
- [x] **T369 [P0]** Bind chosen `truth`/`lie` verdict and semantic intent into the commitment.
- [x] **T370 [P2]** Implement optional LLM paraphrasing of an already selected intent without movement authority.
- [x] **T371 [P0]** Strictly parse optional LLM response into bounded text only; evidence: prose, tool-call, malformed JSON, and oversize outputs fall back.
- [x] **T372 [P0]** Quote/sanitize opponent hint data in prompts and block instruction/tool authority; evidence: prompt-injection corpus.
- [x] **T373 [P0]** Fall back to deterministic template on LLM timeout, provider error, budget exhaustion, or invalid output.
- [x] **T374 [P0]** Ensure each exported role repository includes valid strategies for all negotiated role assignments while defaulting to its named role.
- [x] **T375 [P0]** Add deterministic decision snapshot tests for each strategy/profile/seed.
- [x] **T376 [P0]** Integrate advanced strategy between belief update and commitment packing through the SDK/Orchestrator.
- [x] **T377 [P1]** Run initial paired tournament against reference greedy/random/scripted baselines; evidence: role-swapped result matrix.
- [x] **T378 [P0]** Benchmark strategy p50/p95/max latency and fallback rate under minimum hardware profile.
- [x] **T379 [P1]** Run ablations for belief, search, opponent model, barrier graph terms, deception, and risk term; evidence: contribution chart.
- [x] **T380 [P0]** Complete M7 review against PRD FR-STR and Appendix E rules 25-27; evidence: safe baseline and competitive exit report.

---

## M8 - Orchestration, persistence, and reliability (T381-T425)

**Exit gate:** the Orchestrator drives a formal durable state machine; every wait is bounded; crashes, stalls, and network faults either recover from a mutually acknowledged checkpoint or terminate cleanly without deadlock.

- [x] **T381 [P0]** Finalize ADRs for Orchestrator gateway, event journal, deadline policy, and mutual-checkpoint recovery.
- [x] **T382 [P0]** Define complete `GamePhase` enum for initialization through reporting, completion, refusal, technical loss, and tamper.
- [x] **T383 [P0]** Implement explicit transition table with reason-specific allowed targets; evidence: every state has reviewed successors.
- [x] **T384 [P0]** Implement compare-and-set phase transition using expected current state; evidence: concurrent transition race test.
- [x] **T385 [P0]** Make terminal phases immutable; evidence: every attempted exit from terminal state fails.
- [x] **T386 [P0]** Implement `PeerOrchestrator` constructor with injected service ports and no concrete adapters.
- [x] **T387 [P0]** Add architecture test proving Orchestrator contains no physics, strategy scoring, hash implementation, or transport parsing.
- [x] **T388 [P0]** Implement initialization/readiness lifecycle through the SDK.
- [x] **T389 [P0]** Implement negotiation lifecycle coordinating config, Step-0, identities, and agreement.
- [x] **T390 [P0]** Implement one sub-game lifecycle coordinating wait, belief, strategy, commit, ack, reveal, verify, and terminal detection.
- [x] **T391 [P0]** Implement six-sub-game series lifecycle with role schedule and clean per-sub-game resets.
- [x] **T392 [P0]** Implement terminal audit, result agreement, artifact finalization, and report-queue handoff lifecycle.
- [x] **T393 [P0]** Implement reusable monotonic `DeadlineTracker` with remaining/expired operations.
- [x] **T394 [P0]** Define config-driven deadlines for negotiation, MCP call, acknowledgement, reveal, strategy, LLM, audit, and reporting.
- [x] **T395 [P0]** Define retry classification and attempt budget per operation; evidence: semantic errors never retry.
- [x] **T396 [P0]** Implement exponential backoff with bounded jitter and fake-clock support.
- [x] **T397 [P0]** Apply the binding/default response timeout to every network operation; evidence: missing timeout static test.
- [x] **T398 [P0]** Implement independent Watchdog worker that does not share the blocked gameplay execution path.
- [x] **T399 [P0]** Emit heartbeat with phase, step, monotonic timestamp, and progress token.
- [x] **T400 [P0]** Detect both absent heartbeat and unchanged progress beyond configured threshold.
- [x] **T401 [P0]** Persist a redacted recovery snapshot on Watchdog intervention; evidence: no nonce/key leakage.
- [x] **T402 [P0]** Implement controlled shutdown ordering for transport, journal, artifact writer, GUI, and worker resources.
- [x] **T403 [P0]** Implement cooperative cancellation tokens for strategy, optional LLM, transport, and report dispatch.
- [x] **T404 [P0]** Implement journal-based state restoration with chain/config/session validation.
- [x] **T405 [P0]** Implement recovery handshake that compares last mutually acknowledged checkpoint before resume.
- [x] **T406 [P0]** Terminate safely when peers disagree on recovery checkpoint; evidence: no invented state or silent rollback.
- [x] **T407 [P0]** Support either peer starting first with bounded readiness retries and clear timeout outcome.
- [x] **T408 [P0]** Expose `alive`, `ready`, `degraded`, and `failed` health states through redacted SDK/MCP views.
- [x] **T409 [P0]** Integrate MCP Gatekeeper policy with deadline/retry/idempotency context supplied by Orchestrator.
- [x] **T410 [P0]** Implement circuit breaker state machine for repeated transport failures.
- [x] **T411 [P0]** Define durable session-state repository port and typed checkpoint record.
- [x] **T412 [P0]** Implement append-only JSON event journal with monotonic sequence and local hash chain.
- [x] **T413 [P0]** Implement atomic write/replace/flush helper with platform-specific error handling.
- [x] **T414 [P0]** Enforce persist-before-acknowledge for every mutating inbound protocol event.
- [x] **T415 [P0]** Add crash-injection hooks at every journal/write/ack transition boundary.
- [x] **T416 [P0]** Implement bounded internal work queues with config-driven capacities.
- [x] **T417 [P0]** Define explicit queue-overflow/backpressure outcomes rather than unbounded memory growth.
- [x] **T418 [P0]** Prioritize gameplay/audit work over optional banter and post-game reporting.
- [x] **T419 [P0]** Implement public-tunnel preflight checking remote health, capabilities, round trip, payload size, and bidirectionality.
- [x] **T420 [P0]** Validate tunnel URLs for allowed schemes, credentials absence, normalization, and competition-mode public reachability.
- [x] **T421 [P0]** Run deterministic network-fault tests for latency, timeout, reset, refused connection, 5xx, and malformed response at each phase.
- [x] **T422 [P0]** Run 1,000 seeded local sub-games with Watchdog and persistence enabled; evidence: completion/terminal statistics.
- [x] **T423 [P0]** Prove no deadlock through state-machine model coverage and soak-test progress assertions.
- [x] **T424 [P0]** Document startup, timeout, recovery, tunnel, and controlled-shutdown operations in `docs/OPERATIONS.md`.
- [x] **T425 [P0]** Complete M8 review against Appendix E rules 3-7 and PRD FR-ORC/NFR-REL; evidence: signed exit checklist.

---

## M9 - Artifacts, Gmail reporting, and full Gatekeeper (T426-T470)

**Exit gate:** every series emits schema-valid linked artifacts and independently queues/sends exactly one safe JSON report through a durable Gatekeeper-protected outbox.

- [x] **T426 [P0]** Finalize `docs/PRD_REPORTING_UI_REPLAY.md` artifact/reporting sections before implementation.
- [x] **T427 [P0]** Implement Appendix F filename builder for declaration, config, log, and result artifacts.
- [x] **T428 [P0]** Resolve every artifact path under a configured root and reject traversal, reserved names, and unsafe lengths.
- [x] **T429 [P0]** Define `ArtifactManifest` with file digests, schemas, game UID, config, commit, journal, and audit linkage.
- [x] **T430 [P0]** Implement declaration artifact model from negotiated identities, repos, URLs, Step-0, tokens, timing, and digests.
- [x] **T431 [P0]** Implement per-sub-game config artifact containing exact played shared config, roles, agreement, and `config_sha256`.
- [x] **T432 [P0]** Implement sealed log-entry model containing sequence, commitment, reveal, public effects, metrics, and audit status.
- [x] **T433 [P0]** Derive finalized per-sub-game log from append-only events without mutating source evidence.
- [x] **T434 [P0]** Implement final result artifact with all sub-games, group scores, wins, ties, tokens, commits, links, audits, and agreement.
- [x] **T435 [P0]** Enforce semantic schema versions and compatibility rules on every artifact.
- [x] **T436 [P0]** Implement atomic artifact writer using temporary file, validation, flush, and replace.
- [x] **T437 [P0]** Apply restrictive permissions to pre-audit secret stores and best-effort documented permissions to finalized artifacts.
- [x] **T438 [P0]** Validate every artifact against JSON Schema before it is accepted, replayed, committed, or attached.
- [x] **T439 [P0]** Verify `game_uid`, game ID, sub-game, role, config, commit, and log linkage across the full artifact set.
- [x] **T440 [P0]** Implement exact per-step, per-sub-game, and per-series token accounting by group.
- [x] **T441 [P0]** Compute and persist SHA-256 digest for every finalized artifact in the manifest.
- [x] **T442 [P0]** Separate official immutable artifacts from rotating operational diagnostics in storage and APIs.
- [x] **T443 [P1]** Implement per-game artifact archive/export without credentials, private TOML, or unrevealed secrets.
- [x] **T444 [P0]** Implement final report builder from verified artifact manifest only.
- [x] **T445 [P0]** Require mutual result digest confirmation before a report can enter the production outbox.
- [x] **T446 [P0]** Define durable outbox item with logical report ID, attachment digest, recipient, state, attempts, and provider ID.
- [x] **T447 [P0]** Implement outbox transitions `PENDING`, `VALIDATED`, `SENDING`, `RETRY_WAIT`, `SENT`, and `FAILED_PERMANENT`.
- [x] **T448 [P0]** Implement atomic file-backed outbox repository resilient to restart during any transition.
- [x] **T449 [P0]** Enforce logical-report idempotency so a completed series cannot be sent twice accidentally.
- [x] **T450 [P0]** Build MIME email with final JSON as attachment and concise non-authoritative body.
- [x] **T451 [P0]** Enforce competition recipient allowlist defaulting to `rmisegal+uoh26finalgame@gmail.com`.
- [x] **T452 [P0]** Assert OAuth scopes equal send-only Gmail scope and reject read/modify/full-mail scopes.
- [x] **T453 [P0]** Load `credentials.json` and `token.json` only from private configured paths outside artifacts.
- [x] **T454 [P0]** Implement first-run OAuth authorization/refresh workflow without logging tokens.
- [x] **T455 [P0]** Implement Gmail sender adapter behind the email port; evidence: it has no result-building logic.
- [x] **T456 [P0]** Complete central Gatekeeper abstraction for MCP, Gmail, and optional external LLM profiles.
- [x] **T457 [P0]** Implement config-driven continuous token-bucket limiter with monotonic clock.
- [x] **T458 [P0]** Implement daily/session quota manager with durable counters and reset semantics.
- [x] **T459 [P0]** Implement per-service concurrency semaphores using configured limits.
- [x] **T460 [P0]** Implement bounded priority queues with explicit rejection/backpressure results.
- [x] **T461 [P0]** Implement retry/backoff/jitter using service-specific retry classification and attempt caps.
- [x] **T462 [P0]** Handle HTTP 429 by honoring retry guidance and forbidding immediate retry loops.
- [x] **T463 [P0]** Implement DOS/anomaly detector for burst, loop, repeated identical send, and sustained error patterns.
- [x] **T464 [P0]** Implement circuit breaker open, half-open probe, recovery, and manual-safe reset.
- [x] **T465 [P0]** Emit redacted Gatekeeper metrics for quota, tokens, queue, concurrency, retries, rejections, and circuit state.
- [x] **T466 [P0]** Implement outbox dispatcher through Gatekeeper with durable success/failure recording.
- [x] **T467 [P0]** Add fake Gmail tests for success, auth error, timeout, 429, 5xx, malformed response, and duplicate dispatch.
- [x] **T468 [P0]** Add `validate` dry-run mode that builds and validates report/MIME without external state change.
- [ ] **T469 [P0]** Run a controlled real OAuth/send rehearsal to a safe test recipient, never the lecturer during routine testing; evidence: redacted receipt.
- [x] **T470 [P0]** Complete M9 review against Appendix E rules 28-35, 39-40, 51, and 54; evidence: signed exit checklist.

---

## M10 - Live GUI and replay verifier (T471-T510)

**Exit gate:** an accessible local-truth GUI operates through the SDK, and replay independently verifies valid logs, identifies tampering, and produces required deterministic screenshots.

- [x] **T471 [P0]** Finalize `docs/PRD_REPORTING_UI_REPLAY.md` UI/replay sections before implementation.
- [x] **T472 [P0]** Define immutable `LocalView` SDK DTO containing only own truth, public topology, opponent belief, hints, metrics, and status.
- [x] **T473 [P0]** Add compile/runtime privacy guard proving `LocalView` has no opponent true-position or secret-nonce field.
- [x] **T474 [P0]** Implement SDK snapshot method that builds `LocalView` from local services without adapter access.
- [x] **T475 [P1]** Implement Tkinter live-app shell with dependency-injected SDK and no business logic.
- [x] **T476 [P1]** Implement resizable board widget with coordinate labels honoring negotiated origin/index.
- [x] **T477 [P0]** Render own true position with role-specific text/icon and accessible label.
- [x] **T478 [P0]** Render public barriers identically for both roles.
- [x] **T479 [P1]** Render own visited trail without exposing opponent path.
- [x] **T480 [P0]** Render normalized opponent-belief heatmap with fixed scale and numeric legend.
- [x] **T481 [P1]** Render posterior peak, entropy, and credible-region summary without implying certainty.
- [x] **T482 [P0]** Implement text/icon/color turn banner for ready, thinking, waiting, locked, paused, degraded, terminal, and error.
- [x] **T483 [P1]** Implement info panel for step/series, hints, own verdict, barriers, latency, tokens, fallback, and audit/status text.
- [x] **T484 [P1]** Implement Start, Pause, Resume, Stop, Restart, and Quit lifecycle controls with safe confirmation where terminal.
- [x] **T485 [P0]** Route every GUI action through `SimulationSdk`; evidence: direct-service import test.
- [x] **T486 [P0]** Run gameplay outside Tk event loop and marshal immutable snapshots onto UI thread.
- [x] **T487 [P0]** Use a bounded snapshot queue and never enqueue official protocol events as disposable UI data.
- [x] **T488 [P1]** Coalesce/drop only intermediate visual snapshots under render backpressure; evidence: final/terminal snapshot always delivered.
- [x] **T489 [P0]** Verify headless and GUI modes produce identical domain/protocol artifacts for same seed/config.
- [x] **T490 [P1]** Meet contrast requirements and ensure color is never the sole critical status channel.
- [x] **T491 [P1]** Add keyboard navigation/shortcuts and focus order for controls and replay.
- [x] **T492 [P1]** Support scalable text and minimum usable window size without clipped labels.
- [x] **T493 [P0]** Display safe actionable errors with correlation IDs and no stack trace/secret.
- [x] **T494 [P0]** Create deterministic live-GUI screenshot fixture showing belief heatmap and local truth only.
- [x] **T495 [P0]** Implement replay loader through `SimulationSdk.verify_log`, not direct domain/crypto calls from UI.
- [x] **T496 [P0]** Validate replay artifact schema, size, encoding, and identifiers before rendering.
- [x] **T497 [P0]** Validate manifest/game/config/commit linkage before combining logs.
- [x] **T498 [P0]** Implement single-log replay using local track plus belief when sibling log is unavailable.
- [x] **T499 [P1]** Implement dual-log post-audit objective replay only after final reveal and linkage validation.
- [x] **T500 [P0]** Recompute every commitment during replay and expose verification status per step.
- [x] **T501 [P0]** Re-execute every domain transition, barrier, capture, terminal condition, and score during replay.
- [x] **T502 [P0]** Stop normal verification at first invalid step while preserving all diagnostic findings.
- [x] **T503 [P1]** Implement Play, Pause, Previous, Next, Restart, and Go-to-step controls.
- [x] **T504 [P1]** Implement sub-game selector across the six-game series.
- [x] **T505 [P1]** Handle unequal track lengths with explicit frozen/missing-track banner.
- [x] **T506 [P0]** Display `Verified OK` and `TAMPERED` using text, icon, and color with accessible descriptions.
- [x] **T507 [P1]** Export standalone machine-readable and human-readable replay audit report.
- [x] **T508 [P0]** Run replay mutation suite over every field, order, nonce, digest, topology, and score family.
- [ ] **T509 [P0]** Run automated GUI/view-model privacy scan and manual screenshot review for truth/secret leakage.
- [x] **T510 [P0]** Complete M10 review against Appendix E rules 8-9 and 20 plus submission screenshot rules; evidence: signed exit checklist.

---

## M11 - QA, security, chaos, and performance (T511-T570)

**Exit gate:** the full implementation passes requirement traceability, >=85% coverage, Ruff/type gates, adversarial security review, chaos/soak campaigns, and performance budgets on supported platforms.

- [x] **T511 [P0]** Complete `docs/TESTING.md` with test layers, environments, fixtures, seeds, commands, gates, and evidence locations.
- [x] **T512 [P0]** Inventory every source module and map it to direct unit/integration tests.
- [x] **T513 [P0]** Generate requirement-to-test coverage matrix for every FR, NFR, Appendix E rule, and Appendix F parameter.
- [x] **T514 [P0]** Fill unit-test gaps for every module's happy, boundary, invalid, and dependency-failure paths.
- [x] **T515 [P0]** Verify every public function/method has at least one direct test and docstring.
- [x] **T516 [P0]** Expand board/action/scoring property tests to large generated configurations at legal minima and stricter values.
- [x] **T517 [P0]** Expand config property/fuzz tests for encodings, duplicates, nesting, unknowns, boundary numbers, and overlays.
- [x] **T518 [P0]** Expand crypto property/mutation tests for canonical bytes, nonce, every payload field, order, and replay context.
- [x] **T519 [P0]** Expand belief property tests for long sequences, contradictory evidence, underflow, topology changes, and determinism.
- [x] **T520 [P0]** Cover every state-machine transition and every illegal source-target pair.
- [x] **T521 [P0]** Validate every positive/negative JSON example against declaration/config/log/result/protocol schemas in CI.
- [x] **T522 [P0]** Run MCP contract suite against independently started server/client versions and both role repositories.
- [x] **T523 [P0]** Run full two-process localhost sub-game with no shared filesystem visibility.
- [x] **T524 [P0]** Run full six-sub-game local series including final audit, artifacts, and dry-run reports.
- [x] **T525 [P0]** Inject deterministic network latency/jitter at every outbound tool and confirm deadlines remain correct.
- [x] **T526 [P0]** Inject request/response loss at each protocol phase and verify retry/terminal behavior.
- [x] **T527 [P0]** Inject duplicate messages at each mutating tool and verify exactly-once effects.
- [x] **T528 [P0]** Inject reordered/future/stale messages and verify bounded rejection/buffering.
- [x] **T529 [P0]** Disconnect/reconnect tunnel transport during each phase and verify documented outcome.
- [x] **T530 [P0]** Crash each process before/after every persist and acknowledgement boundary; evidence: recovery/termination matrix.
- [x] **T531 [P0]** Corrupt/truncate/replace each artifact and journal family; evidence: fail-closed validation.
- [x] **T532 [P0]** Freeze gameplay, strategy, persistence, and transport workers separately and verify Watchdog response.
- [x] **T533 [P0]** Load-test Gatekeeper quota, bucket, concurrency, queue, retry, DOS, and circuit behavior.
- [x] **T534 [P0]** Run >=1,000 local sub-games and a continuous soak session; evidence: no deadlock, leak, or unbounded growth.
- [x] **T535 [P0]** Complete `docs/SECURITY.md` with threat model, controls, residual risks, secret rotation, and incident process.
- [x] **T536 [P0]** Audit all remote/input boundaries for strict validation before state mutation.
- [x] **T537 [P0]** Test path traversal through game IDs, filenames, manifest links, config paths, and archive export.
- [x] **T538 [P0]** Test symlink/reparse-point escape where supported and reject resolved paths outside allowed roots.
- [x] **T539 [P0]** Test oversized, deeply nested, compressed, repeated, and collection-amplification payloads.
- [x] **T540 [P0]** Test malicious Unicode, bidi controls, nulls, separators, and homoglyphs in identifiers/hints/log fields.
- [x] **T541 [P0]** Test log injection and ensure structured logs preserve one event per record.
- [x] **T542 [P0]** Test prompt injection, data exfiltration requests, tool-like text, and schema-breaking LLM output.
- [x] **T543 [P0]** Run secret scanner over working tree, ignored-file policy, fixtures, docs, artifacts, and release archives.
- [x] **T544 [P0]** Scan complete Git history of both role repositories for credentials, tokens, keys, and `.env` content.
- [x] **T545 [P0]** Verify OAuth scope is send-only in code, tokens, docs, and controlled integration.
- [x] **T546 [P0]** Test report-recipient injection and enforce the competition allowlist.
- [x] **T547 [P0]** Test opponent/tunnel URL validation against credential URLs, unsupported schemes, loopback in league mode, and unsafe redirects.
- [x] **T548 [P0]** Test private strategy dynamic-import restrictions against arbitrary modules, files, and non-subclasses.
- [x] **T549 [P0]** Run locked dependency vulnerability audit and resolve/document all findings.
- [x] **T550 [P0]** Audit dependency and reused-code licenses for compatibility and required attribution.
- [x] **T551 [P0]** Conduct manual cryptographic design review of entropy, canonicalization, key handling, nonce lifecycle, and sanction logic.
- [x] **T552 [P0]** Update threat model and risk register from security/chaos findings; evidence: every critical/high issue closed or explicitly blocking.
- [x] **T553 [P0]** Build repeatable performance harness with warmup, sample count, hardware metadata, and percentile reporting.
- [x] **T554 [P1]** Benchmark SDK cold start/readiness and keep p95 within plan target.
- [x] **T555 [P1]** Benchmark domain transition/path/graph operations across board sizes and barrier densities.
- [x] **T556 [P1]** Benchmark belief prediction/update over 35-step sequences and multimodal posteriors.
- [x] **T557 [P0]** Benchmark baseline/advanced strategy p50/p95/max and hard deadline compliance.
- [x] **T558 [P1]** Benchmark replay schema/linkage/hash/transition verification for all six logs.
- [x] **T559 [P1]** Benchmark artifact derivation, validation, digesting, and atomic writes.
- [x] **T560 [P0]** Measure peak memory and object growth during soak; evidence: no unbounded session, queue, cache, or idempotency retention.
- [x] **T561 [P1]** Measure MCP request count, bytes, retries, and latency per completed series.
- [x] **T562 [P0]** Verify template mode consumes exactly zero LLM tokens and optional providers stay within signed budget.
- [x] **T563 [P1]** Measure outbox age, dispatch attempts, queue depth, and recovery after simulated Gmail outage.
- [x] **T564 [P1]** Profile top CPU/memory hotspots and optimize only with benchmark evidence.
- [x] **T565 [P0]** Run Ruff, strict mypy, import-boundary, file-size, schema, and task/requirement static checks.
- [x] **T566 [P1]** Run mutation testing on config rules, scoring, state transitions, crypto verification, and Gatekeeper decisions.
- [x] **T567 [P0]** Quarantine/fix all flaky tests and verify deterministic repeated CI runs.
- [x] **T568 [P0]** Complete the Windows matrix and macOS smoke, documenting platform-specific limitations.
- [x] **T569 [P0]** Run the full clean-clone quality command suite with global coverage >=85% and Ruff zero violations.
- [x] **T570 [P0]** Complete M11 independent QA/security review; evidence: no unresolved P0/P1 defect and signed exit report.

---

## M12 - Experiments, tuning, and league rehearsal (T571-T615)

**Exit gate:** a frozen policy wins materially over baseline on untouched role-swapped holdout fixtures and completes a six-sub-game series between separate machines over public tunnels with verified artifacts and reports.

- [x] **T571 [P1]** Create `docs/RESEARCH_REPORT.md` structure for hypotheses, methods, hardware, costs, results, limitations, and conclusions.
- [x] **T572 [P1]** Define versioned tournament specification for board/config families, opponents, seeds, repetitions, metrics, and resource limits.
- [x] **T573 [P1]** Implement a clean reference-greedy baseline matching documented argmax-Manhattan/random-barrier behavior without importing reference runtime code.
- [x] **T574 [P1]** Implement seeded random-legal Police and Thief baselines.
- [x] **T575 [P1]** Implement shortest-path Police and maximum-distance Thief scripted baselines.
- [x] **T576 [P1]** Implement corner-hugging and boundary-following Thief adversaries.
- [x] **T577 [P1]** Implement cycle/oscillation and sudden-strategy-switch Thief adversaries.
- [x] **T578 [P1]** Implement aggressive/random-barrier Police adversary.
- [x] **T579 [P1]** Implement deterministic graph-cut/corridor Police adversary distinct from candidate policy.
- [x] **T580 [P1]** Implement always-honest, always-lie, periodic-lie, and trust-switch hint profiles.
- [x] **T581 [P1]** Register previous candidate checkpoints as regression opponents with immutable version IDs.
- [x] **T582 [P0]** Freeze training seeds and adversary instances before tuning.
- [x] **T583 [P0]** Freeze validation seeds/adversaries disjoint from training.
- [x] **T584 [P0]** Seal holdout seeds/adversary families so tuning code cannot inspect results before candidate freeze.
- [x] **T585 [P1]** Run paired role-swapped fixtures for every comparison to control start/role bias.
- [x] **T586 [P0]** Compute primary performance using official fixed scores and series tie rules.
- [x] **T587 [P0]** Treat technical/tamper failures as hard zero and separate reliability gate, never average them away.
- [x] **T588 [P1]** Compute bootstrap confidence intervals for score, capture, survival, and technical-loss rates.
- [x] **T589 [P2]** Compute secondary Elo or Bradley-Terry ranking with uncertainty.
- [x] **T590 [P1]** Define bounded Police hyperparameter space for capture, distance, cut, information, budget, risk, depth, and samples.
- [x] **T591 [P1]** Define bounded Thief hyperparameter space for survival, risk distance, space, routes, entropy, scent, corner, cycle, and modes.
- [x] **T592 [P1]** Define belief hyperparameter space for motion mixture, scent noise, trust priors, likelihood cap, and recency.
- [x] **T593 [P1]** Define hint-policy hyperparameter space for honesty cadence, plausibility, trust threshold, and template diversity.
- [x] **T594 [P1]** Run broad seeded random search and persist every attempted configuration/result.
- [x] **T595 [P1]** Run focused Bayesian/evolutionary optimization only after broad-search sanity checks.
- [x] **T596 [P1]** Add early stopping for clearly inferior or deadline-violating candidates without biasing final validation.
- [x] **T597 [P0]** Capture CPU, RAM, platform, runtime, calls, bytes, tokens, latency, and wall time for every experiment.
- [x] **T598 [P1]** Run formal ablation study for belief fusion, search, opponent model, graph barriers, risk, and deception.
- [x] **T599 [P1]** Test robustness over legal negotiated board sizes, starts, origins, indexes, barrier quotas, step ceilings, and timeouts.
- [x] **T600 [P1]** Test strategy quality under observation delay, packet jitter, and bounded missing/late scent evidence.
- [x] **T601 [P1]** Run adversarial search for failure-inducing opponent policies and add discovered cases to validation, not training holdout.
- [x] **T602 [P0]** Check train-validation gap and reject candidates showing material overfitting or one-opponent specialization.
- [x] **T603 [P0]** Freeze candidate code, private strategy profile, shared defaults, protocol/schema versions, and evaluation manifest.
- [x] **T604 [P0]** Run untouched holdout exactly once under documented procedure; evidence: immutable raw results.
- [x] **T605 [P0]** Verify >=20-point win-score uplift and role-specific >=70% target or document an explicit revised competitive gate before release.
- [x] **T606 [P0]** Verify candidate meets strategy latency, memory, zero-illegal-action, and zero-technical-loss gates.
- [x] **T607 [P1]** Compare template, Ollama, and any approved cloud paraphrasing on tokens, latency, robustness, and game score.
- [ ] **T608 [P0]** Configure two public tunnels and run bidirectional preflight from external networks.
- [ ] **T609 [P0]** Run peers on two physically/logically separate machines with separate repositories, configs, and artifact roots.
- [x] **T610 [P0]** Schedule opponent availability early enough to complete at least two different counted matches; evidence: league calendar/ledger.
- [x] **T611 [P0]** Run non-counted warmups and resolve interoperability issues without polluting counted ledger.
- [x] **T612 [P0]** Run a full six-sub-game public-tunnel dress rehearsal with no unauthorized manual move intervention.
- [x] **T613 [P0]** Complete mutual audits, matching final digests, four artifact families, and two independent safe test reports for rehearsal.
- [x] **T614 [P1]** Document experiment conclusions, failures, parameter sensitivity, costs, and remaining threats in research report.
- [x] **T615 [P0]** Complete M12 competitive/league review; evidence: frozen policy report and remote rehearsal exit checklist.

---

## M13 - Documentation, two-repository release, and submission (T616-T645)

**Exit gate:** both standalone repositories are reproducible, cross-linked, secret-free, tagged, academically documented, and accompanied by the exact Moodle submission package and final `READY` audit.

- [x] **T616 [P0]** Complete README installation prerequisites and `uv sync` clean-clone instructions for both repositories.
- [x] **T617 [P0]** Complete README headless, GUI, replay, validation, tournament, and reporting usage commands.
- [x] **T618 [P0]** Complete README shared/private configuration guide, Appendix F status explanation, and safe secret setup.
- [x] **T619 [P0]** Add minimal localhost, public-tunnel, replay, and report-dry-run examples with expected outputs.
- [x] **T620 [P0]** Complete troubleshooting for ports, tunnels, negotiation mismatch, timeout, audit failure, Tk, OAuth, 429, and pending outbox.
- [x] **T621 [P0]** Write academic README section describing the chosen Dec-POMDP state, action, transition, reward, observation, and uncertainty model.
- [x] **T622 [P0]** Write academic README section on FastMCP orchestration dilemmas, state machine, Gatekeeper, retries, and failures.
- [x] **T623 [P0]** Write academic README section on belief, Police/Thief strategy, barriers, opponent model, hint policy, and LLM boundary.
- [x] **T624 [P0]** Add experiment methodology, learning/tuning curves where relevant, holdout results, efficiency, token, and cost analysis.
- [x] **T625 [P0]** Add required live belief-heatmap and replay `Verified OK` screenshots with captions and reproduction steps.
- [x] **T626 [P0]** Add reciprocal Police/Thief repository links to both READMEs and all four links to result JSON examples.
- [x] **T627 [P0]** Complete and review all seven per-mechanism PRDs against implemented behavior.
- [x] **T628 [P0]** Complete `docs/PROTOCOL.md` with tool schemas, sequences, idempotency, phases, errors, and conformance commands.
- [x] **T629 [P0]** Complete `docs/SCHEMAS.md` with four artifact schemas, canonicalization, versions, examples, and linkage.
- [x] **T630 [P0]** Complete `docs/OPERATIONS.md` with preflight, runbook, recovery, tunnel, report, incident, and rollback procedures.
- [x] **T631 [P0]** Finalize `docs/RESEARCH_REPORT.md`, results tables, sensitivity plots, visualizations, and cost analysis.
- [x] **T632 [P0]** Finalize `docs/SECURITY.md` with threat model, review findings, residual risks, secret rotation, and OAuth least privilege.
- [x] **T633 [P0]** Finalize changelog/version compatibility for package, protocol, schemas, config, strategy, and guidelines.
- [x] **T634 [P0]** Finalize license, credits, reused-code attribution, reference repository acknowledgement, and asset provenance.
- [x] **T635 [P0]** Export the standalone Police repository deterministically from the frozen candidate state.
- [x] **T636 [P0]** Export the standalone Thief repository deterministically from the same reviewed state without runtime linkage.
- [ ] **T637 [P0]** Run full clean-clone install/test/headless/replay/release verification independently in both repositories.
- [x] **T638 [P0]** Conduct final UI accessibility and screenshot review at common scaling settings.
- [x] **T639 [P0]** Commit every played per-match config and exact evidence manifest to the relevant repositories without secrets.
- [ ] **T640 [P0]** Create and push annotated `v1.0-submission` tags pointing to verified clean commits in both repositories.
- [ ] **T641 [P0]** Verify lecturer access to both repositories/tags and verify sibling links from an unauthenticated or invited-reviewer perspective.
- [ ] **T642 [P0]** Fill the provided Moodle form without moving fields, export it to PDF, and visually compare layout to the template.
- [x] **T643 [P0]** Prepare individual Moodle submission checklist for every team member with group ID and both repository links.
- [x] **T644 [P0]** Run the root final readiness checklist covering docs, architecture, SDK, Gatekeeper, duplication, modularity, tests, Ruff, secrets, `uv`, README, results, UI, Git, license, credits, and deployment.
- [x] **T645 [P0]** Record final decision as `READY` only if every release gate and mandatory evidence item passes; otherwise record `CONDITIONALLY READY` or `NOT READY` with blocking owners.
