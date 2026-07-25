# Product Requirements Document

## Distributed Cops-and-Robbers over a Peer-to-Peer Network

| Field | Value |
|---|---|
| Document status | Baseline for implementation |
| Version | 1.0.0 |
| Last updated | 2026-07-25 |
| Product codename | `police_thief_p2p` |
| Primary language | Python 3.13+ |
| Package manager | `uv` only |
| Owners | Project team |
| Intended readers | Developers, QA, security reviewers, course staff, league opponents |

## 1. Executive summary

This project delivers two autonomous, symmetric, independently deployed agents - Police and Thief - that compete in a distributed pursuit-evasion game over a public peer-to-peer network. Each agent runs as both a FastMCP server and client, possesses only local truth, and must make decisions under partial observability. There is no central game server, no shared memory, no trusted referee, and no process with access to the objective world state during live play.

The product is not merely a game or an AI demo. It is a production-quality distributed system whose correctness depends on:

1. Coordinating two mutually distrustful peers over unreliable networks.
2. Enforcing a shared physical model without a central authority.
3. Preserving local epistemic boundaries.
4. Making competitive decisions from uncertain scent and language evidence.
5. Preventing retrospective cheating through SHA-256 Commit-Reveal.
6. Producing machine-verifiable logs, replay evidence, league reports, and reproducible releases.
7. Remaining functional when an LLM, tunnel, API, or peer is slow, malformed, or unavailable.

The implementation will use a deterministic, algorithmic move engine. LLMs are optional and limited by default to generating or classifying natural-language hints. The competitive advantage will come from a stronger belief filter, role-specific receding-horizon policies, graph-aware barrier tactics, opponent modeling, self-play, and rigorous measurement rather than from expensive model calls.

The project is successful only when both agents can complete a six-sub-game series against an unknown remote opponent, audit every sealed step, render lawful local-truth views, send separate signed JSON reports, and reproduce the played code/configuration from Git history.

## 2. Authority and requirement precedence

### 2.1 Normative sources

The following source order governs implementation decisions:

1. `system prompt.txt` at the project root governs engineering process, structure, quality, testing, security, SDK usage, Gatekeeper usage, and readiness reporting.
2. Appendix F of `police_thief_p2p.pdf` is the sole source of truth for quantitative game values and their status (`fixed`, `minimum`, or `negotiable`).
3. Appendix E of the PDF is the consolidated source for mandatory behavior, prohibitions, recommendations, and sanctions.
4. Explicitly mandatory statements elsewhere in the PDF supplement Appendix E.
5. A byte-identical, mutually signed per-match `game.json` is the runtime constitution, but it may never weaken a fixed or minimum PDF rule.
6. This PRD records implementation choices for unspecified behavior.
7. The public reference repository at commit `960499fd5e8777b4929625f5d8fdcf2ab4677b54` is informative only. If it conflicts with the PDF or this project's stricter engineering contract, it does not prevail.

### 2.2 Conflict policy

If two non-quantitative instructions conflict:

1. Prefer the interpretation that preserves decentralization, mutual verifiability, local truth, and league interoperability.
2. Record the conflict and selected interpretation in `docs/DECISIONS.md`.
3. Add a regression test that captures the selected behavior.
4. Disclose the decision in the academic README.

If a quantitative example conflicts with Appendix F, Appendix F wins without exception.

Examples:

- a board-size, move-count, scoring, rate-limit, or token number shown in explanatory prose is illustrative when it differs from Appendix F;
- `scoring.technical_loss = 0` is an implementation representation of a mandatory terminal sanction, not an additional Appendix F parameter row;
- a signed match config may choose another negotiable origin or start, but it cannot change a fixed score or make a minimum threshold/protection weaker;
- for Gatekeeper rows labeled `Minimum`, the minimum applies to protection: maximum request rate/concurrency may be made more restrictive, while delay/assurance/capacity may be increased.

The source ledger, rendered-page map, and independent transcription review are maintained in `docs/SOURCES.md` and `docs/TRACEABILITY.md`. Architecture/protocol interpretations with cross-cutting consequences are recorded in `docs/DECISIONS.md`.

### 2.3 Terminology

The controlled definitions and prohibited synonyms in `docs/GOVERNANCE.md` are normative. The concise definitions below are aliases for that glossary.

- **Agent / peer**: One autonomous process representing the current Police or Thief role.
- **Group**: A student team and its stable league identity.
- **Role**: Police or Thief for a particular sub-game.
- **Series / match**: The agreed collection of sub-games between two groups.
- **Sub-game**: One pursuit-evasion run with one group as Police and one as Thief.
- **Local truth**: The agent's own position/state, public barriers, received hints, observable opponent scent, and locally computed beliefs.
- **Objective state**: Both true positions and all private states together. It must not exist in a live component.
- **Shared constitution**: The canonical, signed `game.json`.
- **Private configuration**: Per-peer `game.toml`, never negotiated or transmitted.
- **Commit**: A SHA-256 digest that seals a canonical step payload while the nonce is secret.
- **Reveal**: Disclosure of the move and hint after commitments are locked.
- **Final reveal / audit**: Post-game disclosure of nonces and verification of all commitments.
- **Gatekeeper**: Central outbound external-API guard for limits, concurrency, retries, queues, monitoring, backpressure, and circuit breaking.
- **SDK**: The only public business-logic entry point used by CLI, GUI, MCP handlers, replay, tests, and integrations.

## 3. Critical product understanding

### 3.1 The real problem

The visible problem is pursuit on a grid. The actual engineering problem is maintaining a consistent, fair, recoverable interaction between two independent systems that:

- cannot see each other's true position;
- cannot share memory or a database;
- may lie only through natural-language hints;
- must not lie about physical actions, barriers, capture, configuration, or audit evidence;
- may run different private strategies, models, operating systems, and hardware;
- may communicate through high-latency or unstable public tunnels;
- have an incentive to alter historical claims after seeing the opponent's behavior;
- must independently reach the same game result and report it.

### 3.2 Product thesis

A winning solution has two equal priorities:

- **Never lose outside the board**: protocol, timeout, schema, secret, report, replay, or submission failures must be engineered out.
- **Win on the board efficiently**: use fast deterministic algorithms, calibrated uncertainty, graph structure, opponent adaptation, and self-play.

### 3.3 Symmetry and asymmetry

The distributed architecture is symmetric: each peer is server and client, holds local truth, emits scent, receives opponent scent, sends hints, commits, reveals, audits, and reports.

The roles are strategically asymmetric:

- Police seeks capture, may replace movement with placement of an irreversible adjacent barrier, and receives the largest capture score.
- Thief seeks survival through the threshold and cannot place barriers.
- Police optimizes interception and space reduction.
- Thief optimizes time-to-capture, mobility, uncertainty, and route diversity.

The implementation must share verified mechanisms without sharing live state. Role-specific strategies plug into the same SDK contracts.

## 4. Users and stakeholders

### 4.1 Primary users

| User | Need |
|---|---|
| Student developer | Build, debug, test, tune, and submit a compliant agent |
| League operator | Configure, start, monitor, stop, replay, audit, and report a match |
| Opposing team | Negotiate compatible terms and interact through stable public MCP tools |
| Lecturer / grader | Reproduce the release, validate rules, audit evidence, compare reports, and assess engineering quality |

### 4.2 Secondary stakeholders

| Stakeholder | Interest |
|---|---|
| Security reviewer | Secrets, scopes, untrusted input, replay integrity, abuse controls |
| QA reviewer | Determinism, edge cases, network faults, coverage, reproducibility |
| Future maintainer | Clear modules, ADRs, schemas, small files, stable SDK |
| Tournament organizer | Interoperability, fair defaults, consistent reporting, operational playbook |

### 4.3 User capabilities

The product assumes users can run terminal commands and edit configuration files. It must not assume expertise in cryptography, MCP internals, or Bayesian filtering. Validation errors and documentation must make those areas operable without weakening safety.

## 5. Goals

### G-01 - Formal compliance

Implement every mandatory Appendix E rule and every Appendix F parameter rule, with automated evidence wherever technically possible.

### G-02 - Fully decentralized live play

Run two peers in separate processes and, for league play, separate machines and repositories, with no shared runtime state or central referee.

### G-03 - Interoperable public MCP

Complete full matches over public tunnel URLs using documented, versioned, idempotent FastMCP tool contracts.

### G-04 - Cryptographic integrity

Make every agreed term and every move immutable through canonical serialization, SHA-256 commitments, nonce secrecy, mutual acknowledgements, and final audit.

### G-05 - Strong competitive intelligence

Outperform the reference greedy policy through probabilistic state estimation, graph-aware planning, adaptive opponent models, and measured self-play.

### G-06 - Operational resilience

Finish or terminate cleanly under delays, duplicate messages, restarts, malformed payloads, LLM failures, rate limits, and controlled peer loss.

### G-07 - Evidence-rich UX

Provide a live local-truth GUI and a post-game replay/audit application that make uncertainty, state, timing, and integrity understandable.

### G-08 - Reproducible league reporting

Emit the four standardized JSON artifacts, send separate Gmail reports from each group, and bind every result to exact configuration and Git commits.

### G-09 - Professional engineering quality

Use an SDK-first modular architecture, `uv`, Ruff, tests, at least 85% global coverage, security controls, CI, documentation, and release gates.

## 6. Non-goals

- A centralized authoritative game server.
- Shared memory, shared files, shared databases, or in-process object sharing between live peers.
- A live "god view" that shows both true positions.
- Blockchain, public-key infrastructure, or zero-knowledge proofs beyond the required Commit-Reveal construction.
- LLM-controlled movement by default.
- A general-purpose tournament platform for arbitrary games.
- Mobile-native applications.
- Paid cloud infrastructure as a requirement for basic operation.
- Reusing the reference repository as an unmodified submission skeleton.
- Guaranteeing victory against every possible opponent.

## 7. Success metrics and KPIs

### 7.1 Compliance and integrity

| KPI | Target | Evidence |
|---|---:|---|
| Mandatory rule coverage | 55/55 mapped and tested or manually evidenced | Compliance matrix |
| Fixed parameter violations | 0 | Config validator tests |
| Minimum parameter weakening | 0 | Negotiation tests |
| Undetected tamper scenarios | 0 | Mutation and audit tests |
| False capture acceptance | 0 | Capture protocol tests |
| Secret files committed | 0 | Secret scan and Git audit |

### 7.2 Reliability

| KPI | Target | Evidence |
|---|---:|---|
| Local six-sub-game completion | >= 99.5% across 1,000 deterministic runs | Soak report |
| Public-tunnel completion | >= 98% across controlled network-fault runs | Integration report |
| Duplicate message side effects | 0 | Idempotency tests |
| Deadlocks | 0 in soak and fault campaigns | Watchdog/state-machine telemetry |
| Clean terminal outcome | 100% of runs | Artifact validation |
| Report loss after completed valid series | 0 with durable outbox | Outbox recovery tests |

### 7.3 Performance and cost

| KPI | Target | Evidence |
|---|---:|---|
| Algorithmic move p95 | <= 250 ms on declared baseline CPU | Benchmark |
| Algorithmic move hard deadline | <= 2 s | Runtime guard |
| Default LLM tokens | 0 per series | Token ledger |
| Optional LLM token budget | <= negotiated 200,000 | Signed report |
| SDK cold start | <= 3 s | Benchmark |
| Replay verification | <= 2 s for a 35-step sub-game | Benchmark |

### 7.4 Strategy

| KPI | Target | Evidence |
|---|---:|---|
| Win-score improvement vs reference | >= 20 percentage points over greedy baseline across symmetric fixtures | Evaluation report |
| Police capture rate vs baseline Thief | >= 70% across seeded boards/configs | Tournament matrix |
| Thief survival rate vs baseline Police | >= 70% across seeded boards/configs | Tournament matrix |
| Illegal strategy outputs | 0; safety layer always returns legal action | Property tests |
| Policy decision reproducibility | 100% for same seed, config, and observations | Determinism tests |
| Generalization | No fixture family loses >15 points from aggregate rate | Holdout report |

### 7.5 Quality

| KPI | Target | Evidence |
|---|---:|---|
| Global test coverage | >= 85% |
| Critical crypto/config/protocol coverage | 100% branch coverage where practical |
| Ruff violations | 0 |
| Type-check failures | 0 |
| Public SDK API documentation | 100% |
| Public functions/methods with tests | 100% |
| Source files over 150 code lines | 0 unless justified in ADR |

## 8. Constraints and assumptions

### 8.1 Hard constraints

- Python dependencies are managed only through `uv`.
- Each live peer runs in an independent process.
- League peers run on separate machines and use public tunnel URLs.
- Police and Thief are submitted in two separate GitHub repositories.
- Both repositories are accessible to the lecturer and cross-link each other.
- Shared per-match configuration is byte-identical and cryptographically locked.
- All movement is one orthogonal cell or stay.
- Natural-language hints are the only legal deception channel.
- No direct numeric position protocol may replace the verbal game in competitive mode.
- Nonces remain secret until the final audit.
- Gmail OAuth scope is send-only.
- Results are attached JSON, not free-form report text.
- Every group independently sends its own report.

### 8.2 Engineering assumptions

- Development uses a canonical workspace and produces two standalone release repositories.
- Both deliverables may use the same reviewed core package source, but each release is independently installable and contains no live shared state.
- FastMCP 3.4.3 or a compatible tested release is available.
- A public tunnel can carry MCP HTTP traffic and expose a health endpoint.
- System clocks may drift; protocol ordering uses sequence numbers and monotonic local deadlines, not wall-clock equality.
- The agreed config defines axis semantics and start cells.
- Opponent inputs are hostile until schema, identity, sequence, state, and phase validation succeed.
- The default language provider is a zero-token template.
- A full league series contains six sub-games, despite the reference repository shipping one for demonstration.

### 8.3 Known ambiguity decisions

| Topic | Decision |
|---|---|
| Police barrier on its own current cell | Legal by the book, but treated as a terminal self-block risk by strategy; engine still implements it exactly |
| Thief "no legal move" when `STAY` exists | A blocked Thief is captured when no legal spatial escape exists; `STAY` does not negate enclosure |
| Scent radial kernel | Make the exact normalized 5x5 kernel part of the signed constitution and include a signed numeric example |
| Commit payload | Seal a versioned canonical JSON record containing all outcome-relevant fields, not string concatenation |
| Message delivery | At-least-once transport with application-level idempotency |
| State recovery | Resume only from mutually acknowledged checkpoints; otherwise terminate and audit as technical failure |
| LLM movement exception | Disabled unless an explicit signed negotiated capability enables it for both peers |
| Live GUI manual input | Operator controls lifecycle only; the autonomous strategy selects moves |
| Replay god view | Allowed only after final reveal and only in the offline replay application |

## 9. Quantitative rules from Appendix F

The following defaults are binding according to their status. `Minimum` may be changed only in a stricter direction by mutual agreement. `Fixed` may never change. `Negotiable` may change by mutual agreement; the listed value is the required default in the absence of agreement.

### 9.1 Board, coordinates, and starts

| Config key | Default | Status | Requirement |
|---|---:|---|---|
| `board_and_agents.grid_size` | `7` | Minimum | Square board side length >= 7 |
| `board_and_agents.num_agents` | `2` | Fixed | Exactly two agents |
| `board_and_agents.axis_origin_corner` | `top-left` | Negotiable | Default origin is upper-left |
| `board_and_agents.axis_start_index` | `0` | Negotiable | Default zero-based axes |
| `board_and_agents.thief_start` | `[3,3]` | Negotiable | Default center for 7x7 |
| `board_and_agents.cop_start` | `[0,0]` | Negotiable | Default corner for 7x7 |

### 9.2 World and hints

| Config key | Default | Status | Requirement |
|---|---|---|---|
| `world.map_area` | `""` | Negotiable | Empty means generic landmarks |
| `world.hint_max_words` | `15` | Negotiable | Hard cap applied to all providers |

### 9.3 Movement and barriers

| Config key | Default | Status | Requirement |
|---|---:|---|---|
| `movement_and_barriers.move_set` | `N,S,E,W,STAY` | Fixed | No diagonals |
| `movement_and_barriers.max_barriers` | `14` | Minimum | Police maximum barrier budget >= 14 |
| `movement_and_barriers.max_moves` | `35` | Minimum | Per-sub-game step ceiling >= 35 |
| `movement_and_barriers.survival_threshold` | `35` | Minimum | Thief survival threshold >= 35 |

### 9.4 Pheromones

| Config key | Default | Status | Requirement |
|---|---:|---|---|
| `pheromones.pheromone_center_intensity` | `0.9` | Fixed | Center emission intensity |
| `pheromones.pheromone_decay` | `0.10` | Fixed | Decay per full turn |
| `pheromones.pheromone_grid_size` | `5` | Fixed | 5x5 emission window |

### 9.5 Scoring

| Config key | Default | Status |
|---|---:|---|
| `scoring.capture_cop` | `20` | Fixed |
| `scoring.capture_thief` | `5` | Fixed |
| `scoring.survival_cop` | `5` | Fixed |
| `scoring.survival_thief` | `10` | Fixed |
| `scoring.tie_score` | `2` | Fixed |

Technical-loss and tamper outcomes remain typed and score zero where mandated by the behavioral rules, but `scoring.technical_loss` is not one of the quantitative parameter rows on Appendix F physical pages 152-155. It shall not be represented as a negotiable/shared Appendix F key unless a later normative source explicitly adds it.

### 9.6 League

| Config key | Default | Status | Requirement |
|---|---:|---|---|
| `network_and_league.num_games` | `6` | Fixed | Six sub-games per scored series |
| `network_and_league.diversity_reward` | `10` | Fixed | New-opponent reward |
| `network_and_league.min_games_to_pass` | `2` | Fixed | At least two different opponents |
| `network_and_league.token_budget_per_series` | `200000` | Negotiable | Estimated series budget |
| `network_and_league.max_games_per_team` | `10` | Fixed | Scored match maximum |

### 9.7 Gatekeeper and reliability

| Config key | Default | Status | Interpretation |
|---|---:|---|---|
| `rate_limiter_gatekeeper.requests_per_minute` | `30` | Minimum | Must be at least as restrictive as the agreed safe rate |
| `rate_limiter_gatekeeper.concurrent_requests` | `2` | Minimum | Do not allow more without a stricter agreed safety model |
| `rate_limiter_gatekeeper.retry_backoff_sec` | `5` | Minimum | Backoff >= 5 seconds |
| `rate_limiter_gatekeeper.max_retries` | `3` | Minimum | At least three controlled attempts before terminal handling |
| `rate_limiter_gatekeeper.queue_depth` | `100` | Minimum | Capacity >= 100 with explicit overflow behavior |
| `network_and_league.response_timeout_sec` | `30` | Negotiable | Default request timeout |
| `network_and_league.watchdog_timeout_sec` | `60` | Negotiable | Default inactivity threshold |

For Gatekeeper parameters, `Minimum` is interpreted as a minimum protection level, not blindly as a larger numeric value. A maximum request rate or concurrency may be made more restrictive locally or by agreement, while retry delay, retry assurance, and bounded queue capacity may be increased. This safety-first interpretation resolves the tension between the Appendix F status label and the table's description of RPM/concurrency as maxima; it must be disclosed in the academic ambiguity register and enforced identically for shared game-facing behavior.

## 10. Primary user journeys

### UJ-01 - Install and validate a peer

1. Developer clones one role repository.
2. Developer runs `uv sync`.
3. Developer copies `.env-example` values into a local untracked environment.
4. Developer validates private TOML, shared JSON, secrets, ports, and dependencies.
5. CLI prints a redacted readiness report.
6. Developer runs unit and local smoke tests.

**Success:** the peer is ready without contacting an opponent or external API.

### UJ-02 - Negotiate a match

1. Both groups exchange public MCP URLs, identities, repositories, played commit hashes, and proposed shared config.
2. Each validates Appendix F status rules and schema compatibility.
3. Each canonicalizes the exact same shared document.
4. Each computes and exchanges `config_sha256`.
5. Each signs its Step-0 declaration and scent model example.
6. A shared `game_id` and `game_uid` are agreed.
7. Any mismatch refuses play before a move occurs.

**Success:** both peers hold byte-identical terms and mutually acknowledged declarations.

### UJ-03 - Play one autonomous turn

1. The state machine confirms that the peer may act.
2. The peer updates local scent observation and belief.
3. The role strategy selects a legal algorithmic action.
4. The hint subsystem creates a bounded natural-language hint and truth/lie verdict.
5. The peer creates a fresh cryptographic nonce.
6. The peer canonicalizes and hashes the full step payload.
7. The peer sends only the commitment.
8. The opponent acknowledges the commitment.
9. The peer reveals move and hint, but not the nonce.
10. The opponent validates phase, schema, action legality, and public effects.
11. Both persist an append-only event and advance state.

**Success:** both peers can later prove exactly what was committed without knowing the nonce now.

### UJ-04 - Place a Police barrier

1. Police elects `BARRIER` instead of movement.
2. Target is current or orthogonally adjacent, in bounds, within quota, and not already blocked.
3. The action is sealed like any other move.
4. On reveal, the exact target is public and applied by both peers.
5. If the target is the Thief's true cell, the capture protocol runs.
6. If the barrier leaves the Thief with no spatial escape, capture is resolved.

**Success:** public board topology remains identical at both peers.

### UJ-05 - Resolve capture

1. Police emits a sealed `capture_claim`.
2. Thief validates the public claim context against its local true position.
3. Thief returns a sealed truthful verdict.
4. Both store the claim and response.
5. Contradiction discovered at audit causes immediate tamper forfeiture.

**Success:** capture is resolved without revealing the Thief's position before a legitimate claim.

### UJ-06 - Finish and audit a sub-game

1. A capture, enclosure, survival threshold, step ceiling, or technical terminal condition occurs.
2. Both stop accepting gameplay messages for that sub-game.
3. Each reveals its nonces for all committed steps.
4. Each reconstructs every opponent digest with constant-time comparison.
5. Each replays transitions, scoring, barriers, claims, and token accounting.
6. Any mismatch marks the sub-game tampered and applies the prescribed sanction.
7. Both persist audit results and a sub-game summary.

**Success:** independent audits reach the same verifiable outcome.

### UJ-07 - Replay a match

1. Reviewer loads a standardized log.
2. Application validates schema and linkage.
3. It recomputes every commitment and transition.
4. It allows play, pause, restart, next, previous, and go-to-step.
5. It displays `Verified OK` per valid step or `TAMPERED` at first invalid step.
6. After final reveal, it may combine both logs into an objective retrospective view.

**Success:** the replay is both understandable evidence and an independent verifier.

### UJ-08 - Report a series

1. Both groups compare independently computed final summaries.
2. Each signs the agreed result digest.
3. Each creates its own `result_<game_id>.json`.
4. Each queues the attachment in a durable outbox.
5. Gatekeeper checks quota, token bucket, concurrency, circuit state, and destination allowlist.
6. Gmail sender uses send-only OAuth to transmit the attachment.
7. Delivery metadata is persisted without leaking tokens.

**Success:** the lecturer receives two consistent, machine-readable reports.

## 11. Functional requirements

### 11.1 SDK and boundaries

- **FR-SDK-001**: All business logic shall be callable through a versioned `SimulationSdk`.
- **FR-SDK-002**: CLI, GUI, FastMCP handlers, replay, and reporting integrations shall call the SDK, not domain services directly.
- **FR-SDK-003**: The SDK shall expose configuration validation, match negotiation, peer lifecycle, match execution, audit, replay verification, artifact export, and report dispatch.
- **FR-SDK-004**: Public SDK methods shall return typed result objects and typed domain errors.
- **FR-SDK-005**: SDK calls that mutate match state shall require a match/session identifier.
- **FR-SDK-006**: SDK interfaces shall support dependency injection for clock, RNG, transport, storage, LLM, email, and system information.
- **FR-SDK-007**: The SDK shall never expose opponent private state during live play.
- **FR-SDK-008**: SDK version compatibility shall be declared in negotiation.

### 11.2 Configuration and validation

- **FR-CFG-001**: Shared terms shall be stored as JSON and private peer settings as TOML.
- **FR-CFG-002**: Shared JSON shall have a versioned JSON Schema.
- **FR-CFG-003**: Private TOML shall have a typed validation model.
- **FR-CFG-004**: Shared JSON shall include every Appendix F parameter.
- **FR-CFG-005**: Validation shall reject changes to fixed values.
- **FR-CFG-006**: Validation shall reject minimum values that make the game easier than the binding threshold.
- **FR-CFG-007**: Negotiable values shall default to Appendix F examples when absent.
- **FR-CFG-008**: Shared JSON shall override any duplicate private setting.
- **FR-CFG-009**: Unknown shared keys shall be rejected unless namespaced as negotiated extensions.
- **FR-CFG-010**: Config canonicalization shall use UTF-8, sorted keys, fixed separators, no insignificant whitespace, finite numeric values, and a declared schema version.
- **FR-CFG-011**: The exact played config shall be copied into a unique per-sub-game artifact.
- **FR-CFG-012**: Secret values shall not be accepted in shared JSON.
- **FR-CFG-013**: Configuration errors shall identify the exact JSON path and violated rule.

### 11.3 Identity, negotiation, and Step-0

- **FR-NEG-001**: Each group shall use a unique eight-character, no-space identifier for submission identity.
- **FR-NEG-002**: Negotiation shall exchange group names, IDs, members, both repository URLs, public MCP URLs, role capabilities, and exact Git commit hashes.
- **FR-NEG-003**: Each side shall declare its actual counted-game total before a match.
- **FR-NEG-004**: Negotiation shall reject duplicate counted opponents.
- **FR-NEG-005**: Negotiation shall reject participation beyond ten counted matches.
- **FR-NEG-006**: Step-0 shall capture OS, CPU model, core count, frequency when available, RAM, GPU, VRAM, model/provider, token estimate, timezone, and code version.
- **FR-NEG-007**: Hardware declaration shall be cryptographically sealed before play.
- **FR-NEG-008**: The played Git commit shall appear in declaration and final result artifacts.
- **FR-NEG-009**: The full scent emission/decay model and a numeric example shall be included in the signed agreement.
- **FR-NEG-010**: Both peers shall prove byte-identical shared config digests before play.
- **FR-NEG-011**: A mismatch shall fail closed without consuming a counted match.
- **FR-NEG-012**: Negotiation messages shall be idempotent and replay-protected.

### 11.4 Board, physics, and scoring

- **FR-GAME-001**: The board shall be square with side length from validated config.
- **FR-GAME-002**: Coordinate conversion shall honor negotiated origin and starting index.
- **FR-GAME-003**: Legal movement shall be exactly N, S, E, W, or STAY.
- **FR-GAME-004**: Diagonal, multi-cell, out-of-bounds, and barrier-crossing movement shall be rejected.
- **FR-GAME-005**: Public barriers shall be immutable once placed.
- **FR-GAME-006**: Police may place a barrier instead of movement.
- **FR-GAME-007**: Barrier target shall be Police's current cell or one orthogonally adjacent cell.
- **FR-GAME-008**: Barrier quota shall be enforced from shared config.
- **FR-GAME-009**: Every barrier placement and exact target shall be disclosed.
- **FR-GAME-010**: Barrier placement on the Thief's current cell shall trigger capture resolution.
- **FR-GAME-011**: A Thief with no spatial escape shall be captured.
- **FR-GAME-012**: Police landing on the Thief's cell shall trigger capture claim.
- **FR-GAME-013**: The Thief shall answer a valid capture claim truthfully and seal the answer.
- **FR-GAME-014**: Survival shall occur when the configured threshold is reached without capture.
- **FR-GAME-015**: Step ceiling shall terminate the sub-game deterministically.
- **FR-GAME-016**: Scoring shall exactly match Appendix F.
- **FR-GAME-017**: Equal series totals shall award the fixed tie score to both groups.
- **FR-GAME-018**: Technical loss and tamper sanctions shall be distinct typed outcomes, both scoring zero where mandated.
- **FR-GAME-019**: The physics engine shall be deterministic for a given state and action.
- **FR-GAME-020**: Live code shall never instantiate an objective board containing both true positions.

### 11.5 Scent and belief

- **FR-BEL-001**: Each role shall emit scent after movement or staying.
- **FR-BEL-002**: Center emission intensity shall be exactly 0.9.
- **FR-BEL-003**: Emission shall use the mutually signed 5x5 radial kernel.
- **FR-BEL-004**: Scent shall decay by 0.10 after each full Police-plus-Thief turn.
- **FR-BEL-005**: Values shall be clamped to a valid non-negative range.
- **FR-BEL-006**: An agent shall observe only opponent scent, never an opponent true position.
- **FR-BEL-007**: Scent may not be manually forged, moved, suppressed, or emitted remotely.
- **FR-BEL-008**: Each peer shall maintain a normalized belief distribution over legal opponent cells.
- **FR-BEL-009**: Barriers and impossible cells shall have zero posterior probability.
- **FR-BEL-010**: Belief prediction shall apply the opponent motion model before observation updates.
- **FR-BEL-011**: Belief update shall fuse scent likelihood and bounded hint evidence.
- **FR-BEL-012**: Hint reliability shall be calibrated from observed consistency and never treated as ground truth.
- **FR-BEL-013**: Degenerate all-zero posterior updates shall fall back to a valid documented prior.
- **FR-BEL-014**: Belief entropy, peak probability, and calibration diagnostics shall be logged.
- **FR-BEL-015**: Strategy decisions shall use the full posterior or sampled particles, not only the argmax, in the advanced policy.

### 11.6 Strategy and natural-language game

- **FR-STR-001**: Police and Thief movement shall be chosen algorithmically by default.
- **FR-STR-002**: The final legality guard shall accept only engine-provided legal actions.
- **FR-STR-003**: Police strategy shall choose between movement, hold, and legal barrier placement.
- **FR-STR-004**: Thief strategy shall never produce a barrier action.
- **FR-STR-005**: Strategies shall be loaded through typed plugin selectors in private config.
- **FR-STR-006**: Strategy failure or deadline miss shall fall back to a deterministic legal baseline.
- **FR-STR-007**: Strategy RNG shall be injectable and seedable.
- **FR-STR-008**: Opponent behavior features shall be learned only from legally observed match data.
- **FR-STR-009**: Cross-sub-game adaptation shall never leak the opponent's hidden truth from replay data into a live sub-game.
- **FR-STR-010**: Hints shall be free natural language, not direct numeric coordinate protocols.
- **FR-STR-011**: Every hint shall be capped at negotiated `hint_max_words`.
- **FR-STR-012**: Each hint shall be sealed with a `truth` or `lie` intent verdict.
- **FR-STR-013**: A template provider shall support fully offline, zero-token play.
- **FR-STR-014**: Optional LLM providers shall have hard deadlines, token accounting, strict output parsing, and template fallback.
- **FR-STR-015**: LLM prompts and outputs shall not include opponent private state or secrets.
- **FR-STR-016**: LLM-driven moves shall require explicit mutually signed enablement and shall still pass the legality guard.
- **FR-STR-017**: Strategy explanations logged for audit shall be concise and shall not expose secrets.

### 11.7 FastMCP and protocol

- **FR-MCP-001**: Every peer shall run one FastMCP server and one client.
- **FR-MCP-002**: Competitive play shall use a public, remotely reachable URL.
- **FR-MCP-003**: MCP tools shall use versioned request/response schemas.
- **FR-MCP-004**: Required tools shall cover health/capabilities, negotiation, commit, acknowledge, reveal, capture claim/response, final nonce reveal, audit agreement, status, and result agreement.
- **FR-MCP-005**: Each request shall include protocol version, `game_uid`, sub-game number, sequence number, sender group, role, message ID, and correlation ID.
- **FR-MCP-006**: Handlers shall validate identity, game, phase, sequence, payload, and replay status before mutation.
- **FR-MCP-007**: Repeated message IDs shall return the prior idempotent response.
- **FR-MCP-008**: Out-of-order messages shall be rejected or buffered only within a bounded documented window.
- **FR-MCP-009**: Unknown peers and games shall be rejected without revealing state.
- **FR-MCP-010**: Network calls shall use deadlines, bounded retries, jitter, and backpressure.
- **FR-MCP-011**: Retry behavior shall never duplicate a move or barrier.
- **FR-MCP-012**: Transport errors shall map to typed protocol outcomes.
- **FR-MCP-013**: Public endpoints shall have request-size and concurrency limits.
- **FR-MCP-014**: Logs shall redact tunnel credentials and authentication material.
- **FR-MCP-015**: A startup connectivity test shall validate bidirectional reachability before counted play.

### 11.8 Orchestration and reliability

- **FR-ORC-001**: The Orchestrator shall be the single entry point to peer subsystems.
- **FR-ORC-002**: The Orchestrator shall coordinate but not contain physics, strategy, crypto, transport, or persistence logic.
- **FR-ORC-003**: A formal state machine shall reject all illegal transitions.
- **FR-ORC-004**: At minimum, the machine shall model initialization, negotiation, waiting, computing, committing, awaiting acknowledgement, revealing, verifying, auditing, reporting, completed, and technical terminal states.
- **FR-ORC-005**: Terminal states shall be immutable.
- **FR-ORC-006**: Every external wait shall have a monotonic deadline.
- **FR-ORC-007**: A background Watchdog shall monitor heartbeats and state progress.
- **FR-ORC-008**: Watchdog intervention shall persist a redacted recovery snapshot and close resources.
- **FR-ORC-009**: Recovery shall not invent acknowledgement or advance a protocol phase.
- **FR-ORC-010**: Cancellation and shutdown shall be cooperative and bounded.
- **FR-ORC-011**: State mutations and event persistence shall be ordered to prevent acknowledged-but-unlogged actions.
- **FR-ORC-012**: The runtime shall tolerate process start order.
- **FR-ORC-013**: Health reporting shall distinguish alive, ready, degraded, and failed.

### 11.9 Commit-Reveal and audit

- **FR-CRY-001**: SHA-256 shall be used for commitments.
- **FR-CRY-002**: A fresh nonce shall be generated with `secrets` for every commitment.
- **FR-CRY-003**: A nonce shall provide at least 128 bits of entropy.
- **FR-CRY-004**: Nonces shall never be transmitted or logged in readable live logs before final reveal.
- **FR-CRY-005**: Commitment payloads shall use versioned canonical JSON.
- **FR-CRY-006**: Payload shall include game/sub-game/step identity, role, pre-action state commitment, move, hint, verdict, public barrier effects, token metrics, model metadata, and nonce.
- **FR-CRY-007**: Only the commitment digest and public envelope shall be sent at commit phase.
- **FR-CRY-008**: Reveal shall occur only after the required acknowledgement lock.
- **FR-CRY-009**: Reveal shall disclose action and hint but retain nonce until final audit.
- **FR-CRY-010**: Digest comparisons shall use constant-time comparison.
- **FR-CRY-011**: Final audit shall verify every digest and every state transition.
- **FR-CRY-012**: One mismatch shall mark the sub-game tampered and stop normal scoring.
- **FR-CRY-013**: Config, scent model, Step-0 declaration, and result agreement shall also be digest-bound.
- **FR-CRY-014**: Audit shall detect missing, duplicate, reordered, truncated, or substituted steps.
- **FR-CRY-015**: Audit evidence shall be independently reproducible through the SDK and replay app.

### 11.10 Artifacts, logging, and schemas

- **FR-ART-001**: Every series shall emit one declaration, one result, and one config/log pair per sub-game.
- **FR-ART-002**: Filenames shall follow Appendix F naming rules using sanitized `game_id` and two-digit sub-game number.
- **FR-ART-003**: All artifacts shall share `game_uid`.
- **FR-ART-004**: Artifact writes shall be atomic.
- **FR-ART-005**: Artifacts shall be schema-versioned and validated before acceptance or send.
- **FR-ART-006**: Logs shall be append-only event records during play and finalized after audit.
- **FR-ART-007**: Log entries shall carry sequence, timestamps, commitment, revealed payload, metrics, and audit status.
- **FR-ART-008**: Private pre-audit logs shall use restricted permissions where supported.
- **FR-ART-009**: Operational logs shall be structured JSON with redaction.
- **FR-ART-010**: No secret, raw OAuth token, environment value, or unrevealed opponent nonce shall enter operational logs.
- **FR-ART-011**: Artifact linkage shall be verified before replay and report.
- **FR-ART-012**: Result artifacts shall include both groups' repository URLs, played commits, per-sub-game roles/results/scores/tokens, totals, winner/tie, and audit evidence.
- **FR-ART-013**: Each played config shall be committed to the relevant repository.

### 11.11 GUI and replay

- **FR-UI-001**: Each live peer shall have an optional local GUI.
- **FR-UI-002**: Live GUI shall show only local truth.
- **FR-UI-003**: Opponent true position shall never be rendered live.
- **FR-UI-004**: GUI shall visualize normalized belief as an accessible heatmap.
- **FR-UI-005**: GUI shall show own position, public barriers, own visited cells, step, role, hint, belief summary, barrier usage, latency, token count, and audit/status messages.
- **FR-UI-006**: Turn banner shall clearly distinguish actionable, thinking, waiting, locked, degraded, terminal, and error states.
- **FR-UI-007**: GUI controls shall not bypass the SDK or state machine.
- **FR-UI-008**: Headless mode shall provide full game functionality.
- **FR-UI-009**: Replay shall validate the entire log before or during navigation.
- **FR-UI-010**: Replay shall expose play, pause, next, previous, restart, go-to-step, and sub-game selection.
- **FR-UI-011**: Replay shall show `Verified OK` or `TAMPERED` prominently.
- **FR-UI-012**: Offline replay may show both true tracks only after final reveal and artifact linkage validation.
- **FR-UI-013**: Color shall not be the sole status channel.
- **FR-UI-014**: Keyboard operation, readable contrast, scalable text, and text alternatives shall be supported.
- **FR-UI-015**: Screenshots required for submission shall be reproducible from a deterministic sample run.

### 11.12 Gmail reporting and Gatekeeper

- **FR-RPT-001**: Each group shall independently send its result after mutual agreement.
- **FR-RPT-002**: The recipient shall default to `rmisegal+uoh26finalgame@gmail.com`.
- **FR-RPT-003**: The report shall be a JSON attachment; free-form text shall not substitute for it.
- **FR-RPT-004**: Gmail OAuth shall request only `https://www.googleapis.com/auth/gmail.send`.
- **FR-RPT-005**: `credentials.json`, `token.json`, `.env`, PEM/key files, and tokens shall be ignored by Git.
- **FR-RPT-006**: All external email API calls shall go through Gatekeeper.
- **FR-RPT-007**: Gatekeeper shall implement quota manager, token bucket, concurrency semaphore, bounded queue, retries, exponential backoff with jitter, monitoring, backpressure, and circuit breaker/DOS detector.
- **FR-RPT-008**: Rate limits shall come from config, never hard-coded.
- **FR-RPT-009**: HTTP 429 shall honor provider retry guidance and shall not trigger immediate retry loops.
- **FR-RPT-010**: A durable outbox shall preserve unsent valid reports across restarts.
- **FR-RPT-011**: Idempotency shall prevent duplicate logical reports.
- **FR-RPT-012**: Destination allowlisting shall prevent arbitrary recipient injection in competition mode.
- **FR-RPT-013**: Email failure shall be visible, recoverable, and shall not rewrite game results.

### 11.13 League and submission

- **FR-LGE-001**: A scored match against a group shall be counted at most once.
- **FR-LGE-002**: Warmups shall be explicitly marked non-counted.
- **FR-LGE-003**: At least two counted matches against different groups are required for project completion.
- **FR-LGE-004**: No group shall exceed ten counted matches.
- **FR-LGE-005**: Six sub-games shall run per scored series.
- **FR-LGE-006**: Police/Thief roles shall be balanced across the series.
- **FR-LGE-007**: Both role repositories shall be separately installable and runnable.
- **FR-LGE-008**: Each repository README shall link to the sibling repository.
- **FR-LGE-009**: Each repository shall include README, config, PRDs, PLAN, TODO, tests, license, credits, and reproducible commands.
- **FR-LGE-010**: Final submission shall be identified by an annotated Git tag, default `v1.0-submission`.
- **FR-LGE-011**: The academic README shall document Dec-POMDP, FastMCP dilemmas, strategies, experiments/learning curves when relevant, required screenshots, installation, usage, troubleshooting, contributions, credits, and license.
- **FR-LGE-012**: Every team member shall complete the required individual Moodle submission.
- **FR-LGE-013**: The provided submission form shall be filled without moving fields and exported to PDF.
- **FR-LGE-014**: Self-assessment shall grade code quality, not league outcome.

## 12. MCP tool contract inventory

Exact schemas are defined in PLAN, but the public semantic surface shall remain small:

| Tool | Purpose | Mutating |
|---|---|---|
| `health_v1` | Liveness/readiness and protocol capabilities | No |
| `propose_match_v1` | Submit identity, declaration, config digest, and match proposal | Yes |
| `accept_match_v1` | Accept exact proposal and shared identifiers | Yes |
| `commit_step_v1` | Register sealed digest for one step | Yes |
| `ack_commit_v1` | Lock receipt of a valid commitment | Yes |
| `reveal_step_v1` | Reveal move/hint without nonce | Yes |
| `capture_claim_v1` | Submit capture/enclosure claim | Yes |
| `capture_response_v1` | Return sealed truthful response | Yes |
| `final_reveal_v1` | Reveal nonces after terminal state | Yes |
| `audit_result_v1` | Exchange audit digest and findings | Yes |
| `agree_result_v1` | Confirm final series result digest | Yes |
| `peer_status_v1` | Optional non-game-changing operational status | No |

Each mutating call shall be idempotent, phase-bound, authenticated by negotiated identity context, size-limited, and persisted before success is returned.

## 13. Data product requirements

### 13.1 Declaration artifact

`declaration_<game_id>.json` shall contain:

- schema/report versions;
- `game_id`, `game_uid`, timezone, counted/warmup mode;
- both group identities, members, public URLs, repository URLs, played commits;
- both hardware declarations and their digests;
- LLM/provider declarations and token budget;
- series size and planned timing;
- shared config digest and scent model digest;
- counted-game declarations;
- mutual acknowledgement evidence.

### 13.2 Per-sub-game config artifact

`config_<game_id>_g<NN>.json` shall contain:

- exact shared config played;
- schema version;
- sub-game number and role assignment;
- `config_sha256`;
- agreement identities/timestamps;
- no private TOML values or secrets.

### 13.3 Per-sub-game log artifact

`log_<game_id>_g<NN>.json` shall contain:

- linkage and role metadata;
- initial public conditions;
- ordered sealed step records;
- public board effects;
- hint, verdict, bounded reasoning, token and latency metrics;
- commitment and eventually revealed nonce;
- capture claims/responses;
- terminal reason and score;
- mutual audit summary and first failure if any.

### 13.4 Final result artifact

`result_<game_id>.json` shall contain:

- all linkage and group IDs;
- sub-game role, times, result, winner/tie, scores, tokens, commits, log references, and audit status;
- total scores, wins, ties, token totals, series winner/tie;
- both repository pairs;
- mutual result digest and confirmation;
- sender identity so each group's independent report is attributable.

## 14. Non-functional requirements

### 14.1 Reliability

- **NFR-REL-001**: No external wait may be unbounded.
- **NFR-REL-002**: All mutating remote operations shall be idempotent.
- **NFR-REL-003**: Application state shall remain consistent after process termination at any persistence boundary.
- **NFR-REL-004**: Corrupt artifacts shall fail closed and remain preserved for diagnosis.
- **NFR-REL-005**: Default gameplay shall not depend on any LLM or paid service.
- **NFR-REL-006**: Headless and GUI modes shall use identical business logic.
- **NFR-REL-007**: Network fault injection shall cover loss, duplication, reordering, latency, disconnect, reconnect, and malformed responses.

### 14.2 Security

- **NFR-SEC-001**: All remote input is untrusted and schema-validated.
- **NFR-SEC-002**: Paths derived from game IDs shall be sanitized and confined to configured artifact roots.
- **NFR-SEC-003**: JSON parsing shall reject excessive depth/size and non-finite numbers.
- **NFR-SEC-004**: Logs and errors shall not disclose secrets or opponent private state.
- **NFR-SEC-005**: OAuth uses least privilege and local protected storage.
- **NFR-SEC-006**: Secret scanning shall run pre-commit and in CI.
- **NFR-SEC-007**: Dependency vulnerabilities shall be audited before release.
- **NFR-SEC-008**: Public service exposure shall be minimized to required MCP and health surfaces.
- **NFR-SEC-009**: DOS controls shall bound requests, concurrency, memory, queues, and error amplification.
- **NFR-SEC-010**: Cryptographic randomness shall come only from `secrets`/OS CSPRNG.

### 14.3 Maintainability

- **NFR-MNT-001**: Files should remain <=150 actual code lines when practical.
- **NFR-MNT-002**: Components shall have one responsibility.
- **NFR-MNT-003**: Public modules, classes, methods, and functions shall have docstrings.
- **NFR-MNT-004**: Comments explain why, invariants, and threat assumptions.
- **NFR-MNT-005**: No configurable URL, path, timeout, rate, model, or feature flag shall be hard-coded.
- **NFR-MNT-006**: Domain code shall not import GUI, CLI, FastMCP, Gmail, or concrete persistence modules.
- **NFR-MNT-007**: Strategy interfaces shall be stable and separately testable.

### 14.4 Performance

- **NFR-PERF-001**: A legal fallback action shall always be available within 50 ms.
- **NFR-PERF-002**: Advanced search shall obey a strict iterative-deepening deadline.
- **NFR-PERF-003**: Belief updates shall be O(board cells x local transition degree), or documented otherwise.
- **NFR-PERF-004**: Logging shall not block the event loop on remote I/O.
- **NFR-PERF-005**: GUI rendering shall not mutate or stall gameplay state.

### 14.5 Observability

- **NFR-OBS-001**: Structured events shall include game, sub-game, phase, step, correlation, peer, duration, and outcome.
- **NFR-OBS-002**: Metrics shall cover request counts, errors, retries, queue depth, deadlines, circuit state, strategy latency, belief entropy, token use, and audit findings.
- **NFR-OBS-003**: Logs shall distinguish protocol evidence from operational diagnostics.
- **NFR-OBS-004**: A readiness command shall produce a redacted machine-readable report.
- **NFR-OBS-005**: Deterministic run manifests shall record seeds and versions.

### 14.6 Portability and reproducibility

- **NFR-REP-001**: Supported environments shall include Windows, Linux, and macOS where FastMCP and Tk are available.
- **NFR-REP-002**: Dependencies shall be locked in `uv.lock`.
- **NFR-REP-003**: Tests and simulations shall be seedable.
- **NFR-REP-004**: Every experiment shall write config, seed, commit, environment, metrics, and result to `results/`.
- **NFR-REP-005**: Release commands shall work from a clean clone.

### 14.7 Accessibility and usability

- **NFR-UX-001**: Status shall be visible, specific, and actionable.
- **NFR-UX-002**: Destructive or terminal controls shall require confirmation where operator-initiated.
- **NFR-UX-003**: Errors shall explain recovery without exposing internals.
- **NFR-UX-004**: Keyboard and headless alternatives shall exist.
- **NFR-UX-005**: Color, icons, and text shall redundantly encode critical states.

## 15. Competitive strategy requirements

### 15.1 Shared intelligence layer

The advanced policy shall maintain:

- a full normalized posterior over opponent position;
- a motion-model prediction based on legal transitions;
- scent likelihood from the exact emission/decay model;
- an adaptive hint reliability model;
- posterior entropy and credible regions;
- opponent behavior features such as turn preference, revisit rate, boundary preference, apparent deception rate, and Police barrier style;
- a risk-aware simulation model for short receding-horizon search.

### 15.2 Police policy

Police shall evaluate actions using a weighted objective that includes:

- expected capture probability;
- expected graph distance across the full posterior;
- reduction in Thief reachable region;
- reduction in posterior entropy where information-gathering is useful;
- cut/corridor value of a barrier;
- risk of self-isolation;
- remaining barrier scarcity;
- robustness to multiple likely Thief moves;
- avoidance of predictable cycles.

Barrier candidates shall be evaluated as graph modifications, including connected components, articulation points, min-cut approximations, escape corridor widths, and expected time-to-capture. A barrier shall not be placed by a fixed random probability.

### 15.3 Thief policy

Thief shall evaluate actions using:

- survival probability over the planning horizon;
- distance from the Police posterior and risk quantiles, not only its peak;
- size and connectivity of future reachable region;
- number of disjoint escape routes;
- risk from likely Police barrier placements;
- revisit and scent-concentration cost;
- boundary/corner trap risk;
- unpredictability without suicidal randomness;
- value of honest versus deceptive hints under current opponent trust.

### 15.4 Search and safety

- Search shall use iterative deepening with a deterministic fallback.
- Candidate actions shall come only from the domain legality engine.
- Evaluation shall support a fast heuristic path and a deeper optional path.
- Exact minimax is not required; risk-sensitive expectimax or Monte Carlo belief search is acceptable.
- Strategy output shall never delay protocol handling beyond the signed/default deadline.

### 15.5 Training and evaluation

The project shall implement deterministic self-play and tournament harnesses covering:

- reference greedy agents;
- random legal agents;
- scripted corner/loop/barrier adversaries;
- current and previous policy versions;
- noise and hint-reliability variations;
- negotiated parameter variations at or above legal minima;
- held-out seeds and adversary families.

Parameter tuning shall use a documented search method and a held-out validation set. No parameter shall be selected solely on training fixtures.

## 16. Security threat model

| Threat | Control | Verification |
|---|---|---|
| Modify move after seeing opponent | Commit before reveal; acknowledgement lock | Commit-Reveal integration tests |
| Guess sealed move from small action space | 128+ bit nonce | Entropy and dictionary-resistance tests |
| Replay an old message | Game UID, phase, sequence, message ID | Replay tests |
| Duplicate side effect on retry | Idempotency store | Duplicate-delivery tests |
| Alter historical log | Digest re-computation and state replay | Mutation tests |
| Lie about capture | Sealed claim/response and final audit | Capture tamper tests |
| Weaken game terms | Appendix F validator and config digest | Negotiation tests |
| Leak opponent position in live UI | Local-view DTOs and no objective live model | UI privacy tests |
| Path traversal via game ID | Strict identifier grammar and resolved-path guard | Security tests |
| Oversized/malformed MCP payload | Schema and size limits | Fuzz tests |
| Request flood | Gatekeeper, server concurrency/size limits, circuit breaker | Load/DOS tests |
| Gmail account abuse | Send-only scope, recipient allowlist, quota/token bucket/outbox | OAuth/Gatekeeper tests |
| Secret committed to Git | `.gitignore`, pre-commit, CI secret scan | Repository audit |
| LLM prompt injection | Treat opponent hint as quoted data; no tool authority; strict output schema | Adversarial prompt tests |
| Supply-chain compromise | Lockfile, audit, minimal dependencies | Release audit |

## 17. Compliance matrix for Appendix E rules

| Rule | Type | Product requirement / evidence |
|---:|---|---|
| 1 | Must | Separate live processes; integration isolation test |
| 2 | Must not | No shared memory/state; architecture and privacy tests |
| 3 | Must | Orchestrator is single subsystem entry |
| 4 | Must | Formal phase state machine |
| 5 | Must | Illegal transitions rejected |
| 6 | Must | Deadline tracker on every external wait |
| 7 | Must | Independent Watchdog and controlled persistence |
| 8 | Must | Live UI uses local-view DTO only |
| 9 | Must not | No objective live board |
| 10 | Must | Public tunnel readiness test |
| 11 | Must | Byte-identical config digest |
| 12 | Must | Minimums change only in stricter agreed direction |
| 13 | Must | Orthogonal/stay legality |
| 14 | Must not | Diagonals rejected |
| 15 | Must | Exact barrier publicly revealed |
| 16 | Must not | Barrier location covered by audit |
| 17 | Must | SHA-256 Commit-Reveal |
| 18 | Must | Nonce secret until final audit |
| 19 | Must | Any mismatch creates tamper forfeit |
| 20 | Must | Replay verifier application |
| 21 | Must | Truthful capture response |
| 22 | Must not | False capture assertion/denial fails audit |
| 23 | Must | Scent model and example signed before play |
| 24 | Must | Step-0 hardware declaration sealed |
| 25 | Recommend | Movement remains algorithmic; LLM only language by default |
| 26 | Must | Free natural-language hint channel |
| 27 | Must not | No numeric location protocol in competition |
| 28 | Must | Token-bucket protected Gmail reporting |
| 29 | Must | DOS/circuit-breaker protection |
| 30 | Must | Gmail send-only OAuth scope |
| 31 | Must | At least two different league opponents |
| 32 | Must | Automatic Gmail result reporting |
| 33 | Must | Standard JSON report |
| 34 | Must not | No free-text substitute |
| 35 | Must | Mutual result agreement and separate sends |
| 36 | Must | Mutual full-log audit per sub-game |
| 37 | Must | Accurate counted-game declaration |
| 38 | Must not | False declaration prohibited and detectable |
| 39 | Must not | No credentials/secrets in repository |
| 40 | Must | Secret files in `.gitignore` |
| 41 | Must | Annotated final Git tag |
| 42 | Must | Comprehensive academic README |
| 43 | Must | Unmodified form layout exported to PDF |
| 44 | Must | Individual Moodle submission per member |
| 45 | Must | Eight-character group ID |
| 46 | Must | Barrier on Thief cell captures |
| 47 | Must | Enclosed Thief captures |
| 48 | Must | All terminal scenarios use fixed scoring |
| 49 | Must | Separate Police and Thief repositories with cross-links |
| 50 | Must | README, config, PRD, PLAN, TODO in each repository |
| 51 | Must | Reports sent to required agent-report address |
| 52 | Must | One counted match per opponent |
| 53 | Must | Played Git commit in Step-0 |
| 54 | Must | Per-sub-game and series tokens in final JSON |
| 55 | Must | Self-grade code quality only |

## 18. Acceptance criteria

### AC-01 - Isolation

Given both agents run locally, when one process is paused, inspected, or terminated, then the other has no access to its memory and can observe only protocol behavior.

### AC-02 - Config mismatch

Given shared JSON files differ by one byte, when negotiation occurs, then both peers refuse counted play and record the mismatch without exposing private config.

### AC-03 - Fixed-rule rejection

Given a config proposes diagonal movement or changes fixed scent/scoring values, when validation runs, then it fails with the exact binding rule.

### AC-04 - Commit immutability

Given a committed step, when any payload field or nonce is changed before audit, then digest verification fails and the sub-game is marked tampered.

### AC-05 - Nonce secrecy

Given a live sub-game before terminal audit, when all network and operational records are inspected, then no step nonce is present in transmitted or readable operational data.

### AC-06 - Duplicate delivery

Given `commit_step_v1` is delivered three times with one message ID, when handlers process it, then exactly one state transition and event record occur and all calls return the same semantic response.

### AC-07 - Physics

Given arbitrary legal boards generated within constraints, when engine transitions are exercised, then every accepted action is legal and every illegal action is rejected without state mutation.

### AC-08 - Barrier capture

Given Police legally places a barrier on the Thief's true cell, when the capture protocol completes, then both peers score the fixed capture outcome and audit verifies it.

### AC-09 - Enclosure

Given barriers and edges leave the Thief no spatial escape, when terminal detection runs, then capture is declared even if STAY is syntactically present.

### AC-10 - Belief validity

Given any valid observation sequence, when beliefs update, then probabilities are finite, non-negative, normalized, and zero on impossible cells.

### AC-11 - Strategy safety

Given advanced strategy timeout, exception, NaN score, or invalid candidate, when action selection completes, then a deterministic legal fallback is returned before the deadline.

### AC-12 - LLM independence

Given no network and no model installed, when template mode runs a six-sub-game series, then gameplay completes with zero LLM tokens.

### AC-13 - Local-truth GUI

Given a live match, when GUI view models and screenshots are inspected, then no opponent true position or private nonce appears.

### AC-14 - Replay tamper

Given a saved valid log, when one move, hint, nonce, ordering field, or commitment is modified, then replay displays `TAMPERED` and identifies the first invalid step.

### AC-15 - Timeout

Given an opponent remains silent past the configured deadline, when retry policy is exhausted, then the machine reaches a documented technical terminal state without deadlock.

### AC-16 - Gmail safety

Given a loop attempts excessive sends, when Gatekeeper sees quota/token/DOS thresholds, then it blocks or queues messages, opens the circuit when needed, and preserves the account and report.

### AC-17 - Reporting

Given a mutually agreed audited series, when each group dispatches its report, then two independently attributable JSON attachments contain matching game/result digests and exact commits.

### AC-18 - Clean-clone reproducibility

Given either final repository at the submission tag, when a reviewer follows README commands on a supported system, then `uv sync`, tests, headless smoke play, artifact verification, and replay all succeed.

### AC-19 - Quality

Given the final codebase, when CI runs, then Ruff has zero violations, global coverage is at least 85%, all public APIs are tested, secret scan passes, and no unjustified oversized module remains.

### AC-20 - Competitive evidence

Given the frozen candidate strategy and held-out tournament suite, when compared to the reference greedy policy, then the candidate meets the agreed win-score uplift without exceeding latency or token budgets.

## 19. Milestones

| Milestone | Outcome | Exit gate |
|---|---|---|
| M0 - Governance and traceability | Normative docs, source/rule/parameter/requirement ownership, mechanism outlines | Baseline `1.0.0`; no unresolved P0 specification issue |
| M1 - Foundation and tooling | `uv` project, SDK shell, ports, logging, CI/quality skeleton | Clean clone installs, lints, types, tests, and builds |
| M2 - Configuration and contracts | Shared/private config, identifiers, schemas, canonicalization, vectors | Appendix F and hostile config suites pass |
| M3 - Domain physics and scoring | Deterministic board, barriers, terminal resolution, fixed scoring | Property/golden/SDK-boundary tests pass |
| M4 - Peer protocol and negotiation | Two isolated localhost FastMCP peers, negotiation, idempotency | Basic end-to-end sub-game completes with no shared state |
| M5 - Cryptography and mutual audit | Step-0, Commit-Reveal, capture truth, final mutual audit | Valid evidence verifies; every mutation family fails closed |
| M6 - Scent and Bayesian belief | Interoperable scent and normalized local Bayesian belief | Numeric vectors/calibration/privacy tests pass |
| M7 - Competitive strategy and language policy | Advanced Police/Thief policies, safe language, opponent model | Holdout uplift, legality, latency, and zero-token-default gates pass |
| M8 - Orchestration, persistence, and reliability | State machine, journal, deadlines, Watchdog, full Gatekeeper | Faults recover or terminate cleanly with no deadlock/duplicate effect |
| M9 - Artifacts, Gmail reporting, and full Gatekeeper | Four artifact families, result agreement, Gmail durable outbox | Schema/linkage and safe idempotent reporting rehearsal pass |
| M10 - Live GUI and replay verifier | Local-truth live UI and verified offline replay | Privacy/accessibility tests and tamper-aware screenshots pass |
| M11 - QA, security, chaos, and performance | Full adversarial, chaos, portability, coverage, lint/type/performance gates | Release-candidate quality and security audit passes |
| M12 - Experiments, tuning, and league rehearsal | Frozen policy, untouched holdout, two-machine remote dress rehearsal | Competitive targets and complete six-game public-tunnel rehearsal pass |
| M13 - Documentation, two-repository release, and submission | Two standalone repositories, academic evidence, tags, forms | Root audit records `READY` only when every gate passes |

## 20. Risks and mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Book/reference implementation mismatch | Medium | High | PDF precedence, ADR, compatibility tests |
| Peer implementations interpret scent differently | Medium | Critical | Signed kernel, numeric example, conformance vectors |
| Commit serialization mismatch | Medium | Critical | Shared canonicalization spec and golden vectors |
| Tunnel instability | High | High | preflight, reconnect policy, deadlines, fallback endpoint playbook |
| Duplicate/reordered messages | High | High | sequence IDs, idempotency store, phase checks |
| Strategy overfits baseline | High | High | diverse adversary pool and held-out fixtures |
| Barrier planning is too slow | Medium | Medium | candidate pruning, cached graph metrics, iterative deepening |
| Live UI leaks truth | Low | Critical | local DTO boundary and automated privacy tests |
| Gmail token leak | Low | Critical | send-only scope, ignore rules, scan, rotation playbook |
| Report blocked by quota | Medium | High | durable outbox, Gatekeeper, dry-run validation |
| Two-repository drift | High | High | deterministic export/release process and shared conformance suite |
| Audit data lost on crash | Medium | Critical | write-ahead append, atomic fsync policy, recovery tests |
| Insufficient opponent availability | Medium | High | early scheduling, warmup protocol, league tracker |
| Submission paperwork failure | Medium | High | release checklist, independent review, early dry run |

## 21. Documentation deliverables

The final project shall include:

- `README.md`
- `docs/PRD.md`
- `docs/PLAN.md`
- `docs/TODO.md`
- `docs/SOURCES.md`
- `docs/TRACEABILITY.md`
- `docs/ASSUMPTIONS.md`
- `docs/AMBIGUITIES.md`
- `docs/GOVERNANCE.md`
- `docs/RISKS.md`
- `docs/EVIDENCE.md`
- `docs/EXPERIMENTS.md`
- `docs/PRD_BASE_LOGIC.md`
- `docs/PRD_MCP_INFRASTRUCTURE.md`
- `docs/PRD_STRATEGY.md`
- `docs/PRD_LANGUAGE_SCENT.md`
- `docs/PRD_PUBLIC_TUNNEL.md`
- `docs/PRD_CRYPTO_AUDIT.md`
- `docs/PRD_REPORTING_UI_REPLAY.md`
- `docs/PROTOCOL.md`
- `docs/SCHEMAS.md`
- `docs/STRATEGY.md`
- `docs/SECURITY.md`
- `docs/OPERATIONS.md`
- `docs/TESTING.md`
- `docs/RESEARCH_REPORT.md`
- `docs/DECISIONS.md`
- `docs/REVIEW_M0.md`
- `CHANGELOG.md`
- `LICENSE`
- `CREDITS.md`

## 22. Definition of product ready

The product may be called **READY** only if all of the following are true:

1. Documentation is complete and consistent.
2. Architecture preserves SDK, Orchestrator, Gatekeeper, peer isolation, and local truth.
3. All 55 mandatory rules have evidence.
4. Fixed/minimum/negotiable parameters are enforced.
5. Two standalone role repositories exist and are cross-linked.
6. Full six-sub-game play succeeds locally and over a public tunnel.
7. Commit-Reveal and final mutual audits pass; intentional mutations fail.
8. GUI and replay screenshots meet submission requirements.
9. Four JSON artifact families validate and link correctly.
10. Both groups can send independent safe Gmail reports.
11. Tests pass with >=85% coverage and Ruff zero violations.
12. No secrets or unsafe configuration are present in Git.
13. Strategy meets frozen held-out competitive gates.
14. README, license, credits, tags, played commits, and deployment instructions are complete.
15. The final Moodle form and individual submission obligations are verified.

Until implementation and evidence satisfy those gates, readiness is **NOT READY**.
