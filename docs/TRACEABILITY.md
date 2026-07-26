# Normative Traceability Matrix

**Baseline:** `1.0.0`
**Sources:** `docs/SOURCES.md`
**Machine-check convention:** rule IDs are `E-001..E-055`; parameter IDs are `F-001..F-032`; requirement ranges use inclusive `PREFIX-001..NNN` notation. A range expands within the unchanged prefix.

## 1. Appendix E rules

| ID | Rule | Force | Requirement / interpretation | Owner | Primary evidence | Task anchors |
|---|---:|---|---|---|---|---|
| E-001 | 1 | Must | Live peers run as separate OS processes. | Architecture Lead | TEST | T208, T209, T557 |
| E-002 | 2 | Must not | No shared memory, mutable file, database, or hidden live-state channel. | Security Lead | TEST | T209, T555, T556 |
| E-003 | 3 | Must | PeerOrchestrator is the single subsystem coordinator behind the SDK. | Architecture Lead | TEST | T391, T397, T552 |
| E-004 | 4 | Must | Runtime uses a formal phase state machine. | Reliability Lead | TEST | T382, T383, T385 |
| E-005 | 5 | Must | Illegal phase transitions fail without mutation. | Reliability Lead | TEST | T384, T386, T415 |
| E-006 | 6 | Must | Every external wait has a monotonic deadline. | Reliability Lead | TEST | T205, T403, T529 |
| E-007 | 7 | Must | Independent Watchdog monitors progress and performs controlled persistence/closure. | Reliability Lead | TEST | T404, T405, T413 |
| E-008 | 8 | Must | Live UI consumes a local-view DTO only. | UX Lead | TEST | T473, T474, T505 |
| E-009 | 9 | Must not | Live runtime/UI never exposes an objective board with both true positions. | Security Lead | TEST | T136, T480, T555 |
| E-010 | 10 | Must | Public tunnel connectivity/readiness is proven before counted play. | Operations Lead | EXTERNAL | T204, T608, T612 |
| E-011 | 11 | Must | Both peers prove byte-identical shared configuration. | Protocol Lead | TEST | T108, T185, T186 |
| E-012 | 12 | Must | Minimum parameters change only in a stricter mutually agreed direction. | Configuration Lead | TEST | T092, T186, T212 |
| E-013 | 13 | Must | Legal movement is one orthogonal step or `STAY`. | Domain Lead | TEST | T123, T130, T131 |
| E-014 | 14 | Must not | Diagonal movement is rejected. | Domain Lead | TEST | T131, T160 |
| E-015 | 15 | Must | Every barrier and exact target are public. | Domain Lead | TEST | T144, T336 |
| E-016 | 16 | Must not | Barrier location is never hidden from live protocol/audit. | Protocol Lead | TEST | T222, T229, T253 |
| E-017 | 17 | Must | Commit-Reveal uses SHA-256. | Security Lead | TEST | T224, T226, T251 |
| E-018 | 18 | Must | Nonces remain secret until final audit. | Security Lead | TEST | T220, T221, T229, T231 |
| E-019 | 19 | Must | Any commitment/audit mismatch creates a tamper outcome. | Audit Lead | TEST | T257, T261, T262 |
| E-020 | 20 | Must | An independent offline replay verifier validates evidence. | Audit Lead | TEST | T249, T491, T506 |
| E-021 | 21 | Must | Thief answers a valid capture claim truthfully. | Domain Lead | TEST | T245, T246, T247 |
| E-022 | 22 | Must not | False capture assertion or denial passes audit. | Audit Lead | TEST | T247, T255, T261 |
| E-023 | 23 | Must | Exact scent model and numeric example are signed before play. | Belief Lead | TEST | T096, T187, T234 |
| E-024 | 24 | Must | Step-0 hardware/software declaration is sealed before play. | Security Lead | ARTIFACT | T235-T244 |
| E-025 | 25 | Recommend | Movement is algorithmic by default; LLM use is confined to language unless signed capability enables moves. | Strategy Lead | TEST | T315, T365, T371 |
| E-026 | 26 | Must | Hints remain a free natural-language channel. | Strategy Lead | TEST | T359, T361 |
| E-027 | 27 | Must not | Competitive hints cannot encode a direct numeric location protocol. | Strategy Lead | TEST | T360, T373 |
| E-028 | 28 | Must | Gmail calls are token-bucket/Gatekeeper protected. | Reporting Lead | TEST | T451, T459, T465 |
| E-029 | 29 | Must | DOS and circuit-breaker controls protect external services. | Security Lead | TEST | T417, T458, T545 |
| E-030 | 30 | Must | Gmail OAuth requests send-only scope. | Security Lead | TEST | T452, T462 |
| E-031 | 31 | Must | Project completes counted matches against at least two distinct opponents. | League Owner | EXTERNAL | T610, T643 |
| E-032 | 32 | Must | Agreed results are automatically sent through Gmail. | Reporting Lead | TEST | T450, T466, T613 |
| E-033 | 33 | Must | Result report is standard schema-valid JSON. | Artifact Lead | ARTIFACT | T442, T453, T467 |
| E-034 | 34 | Must not | Free-form email text cannot substitute for the JSON result. | Reporting Lead | TEST | T453, T467 |
| E-035 | 35 | Must | Peers mutually agree result; each group sends independently. | Reporting Lead | TEST | T260, T450, T466 |
| E-036 | 36 | Must | Both peers perform full-log audit for each sub-game. | Audit Lead | TEST | T249-T260, T613 |
| E-037 | 37 | Must | Counted-game declaration matches immutable local ledger. | League Owner | TEST | T181, T191, T193 |
| E-038 | 38 | Must not | A false counted-game declaration is accepted. | League Owner | TEST | T181, T193, T546 |
| E-039 | 39 | Must not | Credentials/secrets enter source control. | Security Lead | TEST | T042, T062-T064, T539 |
| E-040 | 40 | Must | Sensitive file patterns are present in `.gitignore`. | Security Lead | MANUAL | T042, T539 |
| E-041 | 41 | Must | Final submission is identified by an annotated Git tag. | Release Lead | ARTIFACT | T640 |
| E-042 | 42 | Must | Each repository contains the comprehensive academic README. | Submission Owner | MANUAL | T616-T626 |
| E-043 | 43 | Must | The supplied form layout is preserved and exported to PDF. | Submission Owner | SCREENSHOT | T642 |
| E-044 | 44 | Must | Every member completes the individual Moodle submission. | Submission Owner | EXTERNAL | T643 |
| E-045 | 45 | Must | Counted/submission identity uses an eight-character group ID. | League Owner | TEST | T077, T180 |
| E-046 | 46 | Must | Barrier placement on the Thief's cell resolves capture. | Domain Lead | TEST | T146, T163 |
| E-047 | 47 | Must | A Thief with no legal spatial escape is captured; `STAY` does not negate enclosure. | Domain Lead | TEST | T147, T163 |
| E-048 | 48 | Must | Every terminal scenario uses fixed scoring. | Domain Lead | TEST | T148-T155, T255 |
| E-049 | 49 | Must | Police and Thief ship in separate, cross-linked repositories. | Release Lead | EXTERNAL | T635, T636, T641 |
| E-050 | 50 | Must | Each repository contains README, config, PRD, PLAN, and TODO. | Release Lead | TEST | T635-T637 |
| E-051 | 51 | Must | Reports use the required agent-report recipient. | Reporting Lead | TEST | T454, T463 |
| E-052 | 52 | Must | At most one counted match is recorded per opponent. | League Owner | TEST | T193, T610 |
| E-053 | 53 | Must | Step-0 records the exact played Git commit. | Security Lead | ARTIFACT | T182, T241, T242 |
| E-054 | 54 | Must | Final JSON records per-sub-game and series token use. | Reporting Lead | ARTIFACT | T368, T442, T467 |
| E-055 | 55 | Must | Self-grade evaluates code quality, not league result. | Submission Owner | MANUAL | T621-T624, T644 |

Rule coverage assertion: 55 unique rows, rule numbers `1..55`, no gaps. Appendix E physical pages: `142..150`.

## 2. Appendix F quantitative parameters

The rendered binding tables on physical pages 152-155 contain 32 quantitative/configuration parameters. `scoring.technical_loss = 0` remains a mandatory typed outcome requirement, but it is not an Appendix F table row and is therefore intentionally excluded here.

| ID | Physical page | Config key | Default | Status | Enforcement interpretation | Owner | Primary evidence / tasks |
|---|---:|---|---|---|---|---|---|
| F-001 | 152 | `board_and_agents.grid_size` | `7` | Minimum | square side >=7 | Configuration Lead | TEST T083, T092 |
| F-002 | 152 | `board_and_agents.num_agents` | `2` | Fixed | exactly two live agents | Configuration Lead | TEST T083, T091 |
| F-003 | 152 | `board_and_agents.axis_origin_corner` | `top-left` | Negotiable | default upper-left; signed alternative | Domain Lead | TEST T083, T093, T095 |
| F-004 | 152 | `board_and_agents.axis_start_index` | `0` | Negotiable | default zero-based; signed alternative | Domain Lead | TEST T083, T093, T095 |
| F-005 | 152 | `board_and_agents.thief_start` | `[3,3]` | Negotiable | default center on 7x7, must be legal | Domain Lead | TEST T083, T094 |
| F-006 | 152 | `board_and_agents.cop_start` | `[0,0]` | Negotiable | default corner on 7x7, must be legal | Domain Lead | TEST T083, T094 |
| F-007 | 152 | `world.map_area` | `""` | Negotiable | empty selects generic landmarks | Strategy Lead | TEST T084, T093 |
| F-008 | 152 | `world.hint_max_words` | `15` | Negotiable | hard cap for all language providers | Strategy Lead | TEST T084, T361 |
| F-009 | 153 | `movement_and_barriers.move_set` | `N,S,E,W,STAY` | Fixed | no diagonal or multi-cell action | Domain Lead | TEST T085, T091, T131 |
| F-010 | 153 | `movement_and_barriers.max_barriers` | `14` | Minimum | Police budget >=14 | Domain Lead | TEST T085, T092, T142 |
| F-011 | 153 | `movement_and_barriers.max_moves` | `35` | Minimum | sub-game ceiling >=35 | Domain Lead | TEST T085, T092, T149 |
| F-012 | 153 | `movement_and_barriers.survival_threshold` | `35` | Minimum | survival threshold >=35 | Domain Lead | TEST T085, T092, T148 |
| F-013 | 153 | `pheromones.pheromone_center_intensity` | `0.9` | Fixed | exact center emission | Belief Lead | TEST T087, T091, T269 |
| F-014 | 153 | `pheromones.pheromone_decay` | `0.10` | Fixed | exact full-turn decay | Belief Lead | TEST T087, T091, T273 |
| F-015 | 153 | `pheromones.pheromone_grid_size` | `5` | Fixed | exact 5x5 emission window | Belief Lead | TEST T087, T091, T268 |
| F-016 | 154 | `scoring.capture_cop` | `20` | Fixed | Police score on capture | Domain Lead | TEST T086, T151 |
| F-017 | 154 | `scoring.capture_thief` | `5` | Fixed | Thief score on capture | Domain Lead | TEST T086, T151 |
| F-018 | 154 | `scoring.survival_cop` | `5` | Fixed | Police score on Thief survival | Domain Lead | TEST T086, T152 |
| F-019 | 154 | `scoring.survival_thief` | `10` | Fixed | Thief score on survival | Domain Lead | TEST T086, T152 |
| F-020 | 154 | `scoring.tie_score` | `2` | Fixed | each group receives 2 on tied series total | Domain Lead | TEST T086, T154 |
| F-021 | 154 | `network_and_league.num_games` | `6` | Fixed | six sub-games per scored series | League Owner | TEST T088, T156, T190 |
| F-022 | 154 | `network_and_league.diversity_reward` | `10` | Fixed | reward for a new opponent | League Owner | TEST T088, T586 |
| F-023 | 154 | `network_and_league.min_games_to_pass` | `2` | Fixed | two different counted opponents | League Owner | TEST T088, T610 |
| F-024 | 154 | `network_and_league.token_budget_per_series` | `200000` | Negotiable | default estimated series cap | Strategy Lead | TEST T088, T369 |
| F-025 | 154 | `network_and_league.max_games_per_team` | `10` | Fixed | counted-series maximum | League Owner | TEST T088, T192 |
| F-026 | 155 | `rate_limiter_gatekeeper.requests_per_minute` | `30` | Minimum | minimum protection: maximum rate may be made more restrictive | Security Lead | TEST T089, T092, T417 |
| F-027 | 155 | `rate_limiter_gatekeeper.concurrent_requests` | `2` | Minimum | minimum protection: concurrency may be made more restrictive | Security Lead | TEST T089, T092, T418 |
| F-028 | 155 | `rate_limiter_gatekeeper.retry_backoff_sec` | `5` | Minimum | delay >=5 seconds | Reliability Lead | TEST T089, T092, T420 |
| F-029 | 155 | `rate_limiter_gatekeeper.max_retries` | `3` | Minimum | at least three controlled attempts before terminal policy | Reliability Lead | TEST T089, T092, T420 |
| F-030 | 155 | `rate_limiter_gatekeeper.queue_depth` | `100` | Minimum | bounded capacity >=100 with explicit overflow behavior | Reliability Lead | TEST T089, T092, T419 |
| F-031 | 155 | `network_and_league.response_timeout_sec` | `30` | Negotiable | default per-request timeout | Reliability Lead | TEST T089, T093, T403 |
| F-032 | 155 | `network_and_league.watchdog_timeout_sec` | `60` | Negotiable | default inactivity threshold | Reliability Lead | TEST T089, T093, T405 |

Parameter review: first transcription from `docs/PRD.md`; independent second pass against rendered physical pages 152, 153, 154, and 155 on 2026-07-25. Result: all 32 source rows mapped; one PRD-only pseudo-parameter (`scoring.technical_loss`) reclassified as a mandatory outcome rule.

## 3. Requirement -> component -> TODO -> evidence

Each expanded requirement ID maps to exactly one primary planned owner component in this table and at least one concrete TODO task. Secondary components may participate, but the primary component is accountable.

| Requirement range | Count | Primary planned component | TODO task anchors | Primary evidence |
|---|---:|---|---|---|
| `FR-SDK-001..008` | 8 | `SimulationSdk` | T056-T058, T069, T158, T170, T473 | TEST |
| `FR-CFG-001..013` | 13 | `ConfigurationService` | T081-T119 | TEST |
| `FR-NEG-001..012` | 12 | `NegotiationService` | T177-T206 | TEST |
| `FR-GAME-001..020` | 20 | `GameRulesService` | T121-T165 | TEST |
| `FR-BEL-001..007` | 7 | `ScentService` | T267-T282 | TEST |
| `FR-BEL-008..015` | 8 | `BeliefService` | T283-T310 | TEST |
| `FR-STR-001..017` | 17 | `StrategyService` | T311-T380 | TEST |
| `FR-MCP-001..015` | 15 | `McpTransport` | T167-T175, T194-T214 | TEST |
| `FR-ORC-001..006` | 6 | `PeerOrchestrator` | T381-T403 | TEST |
| `FR-ORC-007..013` | 7 | `Watchdog` | T404-T425 | TEST |
| `FR-CRY-001..010` | 10 | `CommitmentService` | T217-T247 | TEST |
| `FR-CRY-011..015` | 5 | `AuditService` | T248-T265 | TEST |
| `FR-ART-001..013` | 13 | `ArtifactService` | T426-T447 | ARTIFACT |
| `FR-UI-001..008` | 8 | `LiveUiAdapter` | T471-T490 | TEST |
| `FR-UI-009..015` | 7 | `ReplayUiAdapter` | T491-T510 | TEST |
| `FR-RPT-001..005` | 5 | `ReportingService` | T448-T455 | TEST |
| `FR-RPT-006..009` | 4 | `Gatekeeper` | T456-T465 | TEST |
| `FR-RPT-010..013` | 4 | `ReportingService` | T450, T461, T466-T470 | TEST |
| `FR-LGE-001..006` | 6 | `LeagueService` | T181, T190-T193, T586, T610-T613 | ARTIFACT |
| `FR-LGE-007..014` | 8 | `ReleasePipeline` | T616-T645 | MANUAL |
| `NFR-REL-001` | 1 | `PeerOrchestrator` | T205, T403, T529 | TEST |
| `NFR-REL-002` | 1 | `McpTransport` | T196-T201, T206, T524 | TEST |
| `NFR-REL-003` | 1 | `ArtifactService` | T389, T399-T402, T527 | TEST |
| `NFR-REL-004` | 1 | `AuditService` | T444, T493, T534 | TEST |
| `NFR-REL-005` | 1 | `StrategyService` | T359, T364, T371 | TEST |
| `NFR-REL-006` | 1 | `SimulationSdk` | T158, T473, T552 | TEST |
| `NFR-REL-007` | 1 | `Gatekeeper` | T521-T531 | TEST |
| `NFR-SEC-001..003` | 3 | `ConfigurationService` | T100, T169, T533, T535 | TEST |
| `NFR-SEC-004` | 1 | `ObservabilityService` | T062, T204, T555 | TEST |
| `NFR-SEC-005..007` | 3 | `ReleasePipeline` | T064, T452, T538-T540 | TEST |
| `NFR-SEC-008..009` | 2 | `Gatekeeper` | T202, T417-T425, T545 | TEST |
| `NFR-SEC-010` | 1 | `CommitmentService` | T060, T218-T220 | TEST |
| `NFR-MNT-001..005` | 5 | `CiQualityGates` | T051-T055, T061, T068, T550-T554 | TEST |
| `NFR-MNT-006` | 1 | `ArchitectureDependencyPolicy` | T073, T170, T552 | TEST |
| `NFR-MNT-007` | 1 | `StrategyService` | T313, T318, T549 | TEST |
| `NFR-PERF-001..002` | 2 | `StrategyService` | T318, T328, T348, T565 | BENCHMARK |
| `NFR-PERF-003` | 1 | `BeliefService` | T288, T305, T564 | BENCHMARK |
| `NFR-PERF-004` | 1 | `ObservabilityService` | T399, T565 | BENCHMARK |
| `NFR-PERF-005` | 1 | `LiveUiAdapter` | T475, T489, T565 | BENCHMARK |
| `NFR-OBS-001..003` | 3 | `ObservabilityService` | T061, T395, T422, T439 | ARTIFACT |
| `NFR-OBS-004` | 1 | `SimulationSdk` | T056, T119, T470 | ARTIFACT |
| `NFR-OBS-005` | 1 | `ExperimentRunner` | T572, T597 | ARTIFACT |
| `NFR-REP-001..003` | 3 | `ReleasePipeline` | T044, T066, T074, T561 | TEST |
| `NFR-REP-004` | 1 | `ExperimentRunner` | T571, T572, T594, T597 | ARTIFACT |
| `NFR-REP-005` | 1 | `ReleasePipeline` | T637 | TEST |
| `NFR-UX-001..005` | 5 | `LiveUiAdapter` | T476-T489, T507, T638 | SCREENSHOT |

Expanded-count assertion: functional `183`, non-functional `44`, total `227`. The expected set is exactly the unique requirement IDs declared in PRD sections 11 and 14.

## 4. Acceptance and validation rules

The M0 validator shall fail when:

- any PRD requirement ID is duplicated or absent from the expanded mapping;
- any mapped component is absent from PLAN;
- any mapped task ID is absent from TODO;
- Appendix E IDs/rule numbers are not the exact sets `E-001..E-055` and `1..55`;
- Appendix F keys are duplicated or the exact 32-row baseline changes without a source/ADR update;
- an evidence type is outside `TEST`, `ARTIFACT`, `SCREENSHOT`, `BENCHMARK`, `MANUAL`, or `EXTERNAL`.

Detailed requirement-to-test-case links are added as tests are written. M0 establishes complete ownership and planned evidence, not false implementation evidence.

M11 replaces that planned-only test linkage with the generated executable
matrix at `results/benchmarks/m11_requirement_tests.json`. The generator asserts
the exact 227 FR/NFR identifiers, `E-001..E-055`, and `F-001..F-032`; every one
of the 314 entries maps to existing focused tests and is contract-tested in CI.
