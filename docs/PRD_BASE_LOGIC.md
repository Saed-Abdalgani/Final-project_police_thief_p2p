# Mechanism PRD - Base Logic, Configuration, Physics, and Scoring

**Status:** M2 configuration contract finalized; M3 physics remains planned
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
- [ ] terminal evaluation order for M3 physics;
- [ ] state/event DTO field list;
- [ ] complete scoring truth table including technical/tamper distinction;
- [ ] complexity and benchmark budgets;
- [ ] reviewed examples for barrier-on-self and enclosure.
