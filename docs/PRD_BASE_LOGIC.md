# Mechanism PRD - Base Logic, Configuration, Physics, and Scoring

**Status:** M0 approved outline; must be finalized before M2/M3 implementation
**Owner:** Domain Lead
**Requirements:** FR-CFG-001..013, FR-GAME-001..020, FR-SDK-001..008
**Rules:** Appendix E 11-16 and 46-48; Appendix F F-001..F-025

## Purpose and scope

Define the deterministic, network-free core that parses the shared constitution, normalizes coordinates, enumerates legal actions, applies own-state transitions, maintains public barriers, detects terminal conditions, and scores a six-sub-game series. It also defines the typed SDK-facing contracts that prevent adapters from accessing services directly.

Out of scope: MCP transport, commitment construction, opponent belief, competitive action ranking, GUI rendering, Gmail, and objective live state.

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

- exact JSON/TOML schemas and duplicate-key/depth/size rules;
- coordinate and terminal evaluation order;
- state/event DTO field list;
- complete scoring truth table including technical/tamper distinction;
- source-to-test links for F-001..F-025;
- complexity and benchmark budgets;
- reviewed examples for barrier-on-self and enclosure.

