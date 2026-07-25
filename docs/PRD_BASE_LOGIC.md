# Mechanism PRD - Base Logic, Configuration, Physics, and Scoring

**Status:** M3 deterministic physics and scoring contract finalized
**Owner:** Domain Lead
**Requirements:** FR-CFG-001..013, FR-GAME-001..020, FR-SDK-001..008
**Rules:** Appendix E 11-16 and 46-48; Appendix F F-001..F-032

## Purpose and scope

Define the deterministic, network-free core that parses the shared constitution, normalizes coordinates, enumerates legal actions, applies own-state transitions, maintains public barriers, detects terminal conditions, and scores a six-sub-game series. It also defines the typed SDK-facing contracts that prevent adapters from accessing services directly.

Out of scope: MCP transport, commitment construction, opponent belief, competitive action ranking, GUI rendering, Gmail, and objective live state.

## Configuration assumptions and ownership

This section is the reviewed implementation contract for M2. It closes the
configuration placeholders from the M0 outline without weakening Appendix F.

| Concern | Authority | Implemented decision |
|---|---|---|
| Fixed/minimum/negotiable status | Appendix F through `docs/TRACEABILITY.md` | Fixed values are exact; ordinary minimums may increase; request-rate and concurrency safety maxima may only decrease; negotiable omissions use Appendix F defaults in typed model construction. |
| Shared terms | Mutually agreed `game.json` | Every Appendix F key is required on the signed wire document. Unknown fields fail except keys inside `extensions`, whose keys must be explicit lowercase namespaces. |
| Private terms | Per-peer `game.toml` | Only identity, network, paths, strategy, language, email, GUI, tunnel, and observability sections exist. Shared rule section names fail closed. |
| Merge authority | Shared constitution | Shared and private fields retain immutable provenance. Private configuration cannot override a shared rule because it cannot represent one. |
| Secret resolution | Private environment references | TOML stores allowlisted environment-variable names only. Environment lookup resolves only those secret references; game rules never read environment overrides. |
| Identifier mode | Runtime mode | Development IDs use bounded ASCII syntax. Submission mode requires exactly eight ASCII alphanumeric characters for both agreed peers and the local identity. |
| Coordinate representation | Signed board convention | External starts use the signed origin corner and 0/1 start index; the engine normalizes to zero-based top-left positions and validates both starts as on-board and distinct. |
| Decimal representation | ADR-004 | Non-integer values are plain decimal strings. Canonical JSON never serializes binary floats or non-finite numbers. |
| Scent interoperability | Signed constitution | The exact center-normalized symmetric 5x5 kernel, six-place `ROUND_HALF_EVEN` policy, and `0.900000 -> 0.810000` example are mandatory. |
| Resource limits | Local parser boundary | Shared JSON is capped at 262,144 bytes and depth 32; private TOML is capped at 131,072 bytes. UTF-8, duplicate keys, NaN/infinity, malformed input, and schema/model violations fail with stable safe codes. |
| Raw versus semantic equality | Negotiation/audit | SHA-256 of exact raw bytes and SHA-256 of canonical semantics are separate evidence. Semantic equality never substitutes for the byte-identical match requirement. |

### Validation sequence

1. Enforce byte limit and strict UTF-8.
2. Parse while rejecting duplicate JSON keys and non-finite numbers.
3. Enforce maximum JSON nesting depth.
4. Validate Draft 2020-12 schema with unknown-key rejection.
5. Construct immutable typed models.
6. Enforce fixed values, minimum direction, start legality, deadlines, namespaces,
   schema/protocol compatibility, and optional submission IDs.
7. Serialize NFC canonical JSON and calculate lowercase SHA-256.

### Reviewed scent formula

The signed kernel contains a unit center and symmetric attenuation weights. Emitted
cell intensity is `quantize(center_intensity * kernel_weight)`. One full turn of
decay is `quantize(value * (1 - decay))`. Quantization uses six decimal places and
round-half-even. The complete matrix and expected outputs are immutable vectors in
`data/conformance/scent/emission_decay.json`.

## Inputs

- versioned shared `game.json` bytes and private `game.toml`;
- typed role, group/game/sub-game/step identities;
- local state containing own truth only;
- public barrier/event history;
- one proposed action from the strategy boundary;
- verified public capture/barrier information;
- Appendix F status-aware defaults and constraints.

## Outputs

- `ConfigValidationResult` with exact safe paths/codes;
- immutable `EffectiveConfig` with field provenance;
- normalized `Position`, `Action`, and legal-action set;
- immutable next local state plus public events;
- typed terminal reason and fixed score;
- six-game schedule and group-level aggregate;
- deterministic SDK DTOs and errors.

## Accepted M3 domain contracts

| Use case | Input | Deterministic output | Rejection |
|---|---|---|---|
| Initialize local state | validated `SharedConfig`, own `Role` | immutable own start/rules/empty barriers/visited set | invalid role/config is unrepresentable or rejected upstream |
| Enumerate actions | `LocalGameState` | ordered MOVE actions, STAY, then Police barrier actions | terminal state returns no actions |
| Transition | local state and one validated `Action` | immutable next state plus exact public barrier events | terminal, illegal, blocked, out-of-bounds, wrong-role, duplicate, or over-quota action |
| Graph query | board, public barriers, public/local cell(s) | BFS distance, components, cuts, escape routes | out-of-board endpoint |
| Verified terminal | offline/audit positions and public facts | one typed terminal reason or `None` | invalid counters/cells |
| Score sub-game | typed terminal reason, fixed `ScoringConfig` | Police/Thief role points | fixed config already enforced by M2 |
| Aggregate series | six uniquely numbered balanced outcomes, two group IDs | group totals, tie awards, winner | missing/duplicate/unbalanced/foreign-group outcome |

`LocalGameState` contains own role and position, rules, public barriers, own barrier
count, public step number, own visited cells, and optional terminal reason. It has
no opponent position, objective world, or field whose name can carry opponent
truth. Offline terminal functions accept verified positions as transient arguments;
they never construct or retain a live two-position state.

`BarrierPlaced` contains `event_type`, Police actor, positive step number, and exact
row/column target. MOVE and STAY produce no public M3 event; later protocol phases
seal them before disclosure.

## Terminal evaluation order

1. Tamper sanction.
2. Technical failure.
3. Newly placed barrier on verified Thief cell.
4. Direct Police landing on verified Thief cell.
5. No passable N/S/E/W Thief escape (`STAY` deliberately excluded).
6. Survival threshold reached.
7. Maximum step ceiling reached.
8. Explicit operator stop.

Capture always precedes survival/ceiling at the same completed step. A Police
barrier on its own current cell is legal, public, and leaves Police able to move
out; no role may move into any barrier. A Thief can never occupy a public barrier.

## Fixed scoring truth table

| Terminal reason | Police | Thief |
|---|---:|---:|
| Capture, barrier capture, enclosure | 20 | 5 |
| Survival, step ceiling without capture | 5 | 10 |
| Technical, tamper, stopped | 0 | 0 |

Raw points follow group identity through role alternation. Equal six-game raw totals
receive the fixed 2/2 series tie award. The default signed schedule is P,T,P,T,P,T
for the initiating group and the complement for its opponent.

## Complexity and deterministic ordering

- cell iteration: `O(V)` row-major;
- neighbors/legal movement: `O(1)` in N,S,E,W order, with STAY last;
- shortest path and connected component: `O(V+E)` BFS;
- all components: `O(V+E)`;
- articulation points: deterministic removal analysis `O(V(V+E))`, intentionally
  simple and measured below 0.5 seconds on an open 15x15 board;
- escape routes: deterministic greedy internally vertex-disjoint approximation
  using cardinal-start BFS passes;
- local transition: `O(1)` aside from immutable visited/barrier set copy.

Recorded measurements and methodology are in `results/benchmarks/m3_domain.json`.

## Invariants

1. Shared terms always override duplicate private settings.
2. Fixed values never change; minimums never weaken; negotiable fields require mutual signed agreement or use defaults.
3. The engine has no type containing both peers' true positions during live play.
4. Legal movement is exactly one `N/S/E/W` step or `STAY`; barriers are one alternative Police action.
5. Public barriers are immutable, exact, and impassable to both roles.
6. `STAY` does not defeat enclosure capture.
7. Terminal state is immutable and score is a pure function of the verified terminal reason and Appendix F table.
8. For equal config/state/action, bytes/events/results are deterministic across processes and supported platforms.
9. All application access is through `SimulationSdk`.

## Contract outline

| Use case | Input | Result | Failure classes |
|---|---|---|---|
| Validate configuration | shared bytes, private path/env | effective config + digests | parse, schema, fixed/minimum, conflict, secret |
| Normalize coordinates | external position + axis convention | canonical row/column | range, index, origin |
| Enumerate legal actions | local state/config/role | ordered immutable actions | corrupt state |
| Apply local action | state/action | next state + public events | illegal action, quota, terminal |
| Resolve terminal | verified local/public facts | terminal reason or none | inconsistent evidence |
| Score series | six verified outcomes | totals/winner/tie | missing/duplicate/wrong schedule |

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| BL-AC-001 | Every F-001..F-025 default/status validates exactly. | table-driven tests |
| BL-AC-002 | One-field fixed mutations and weakening minimums fail closed. | mutation matrix |
| BL-AC-003 | All origin/index conversions round-trip. | metamorphic/property tests |
| BL-AC-004 | Diagonal, jump, out-of-bounds, barrier crossing, combined move/barrier fail. | negative action matrix |
| BL-AC-005 | Direct, barrier, enclosure, survival, ceiling, technical, tamper, and tie outcomes score correctly. | golden scenarios |
| BL-AC-006 | Generated transitions preserve bounds, barrier, quota, and local-truth invariants. | >=10,000 property cases |
| BL-AC-007 | GUI/MCP/CLI imports cannot directly invoke domain services. | architecture test |
| BL-AC-008 | Same seed/config/action sequence produces byte-identical public events. | cross-process golden run |

## Finalization checklist

- [x] exact JSON/TOML contracts and duplicate-key/depth/size rules;
- [x] coordinate convention and start validation order;
- [x] Appendix F fixed/minimum/default source-to-test mapping;
- [x] canonical serialization and digest vectors;
- [x] scent kernel, rounding policy, and signed numeric example;
- [x] declaration, sub-game config, log, result, and envelope schemas;
- [x] terminal evaluation order for M3 physics;
- [x] state/event DTO field list;
- [x] complete scoring truth table including technical/tamper distinction;
- [x] complexity and benchmark budgets;
- [x] reviewed examples for barrier-on-self and enclosure.
