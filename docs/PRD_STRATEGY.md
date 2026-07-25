# Mechanism PRD - Competitive Police and Thief Strategy

**Status:** M0 approved outline; finalize before M7 implementation
**Owner:** Strategy Lead
**Requirements:** FR-STR-001..009, FR-BEL-015, NFR-MNT-007, NFR-PERF-001..002
**Competitive KPIs:** KPI-S01..S06, KPI-P01..P03

## Purpose and scope

Define deterministic, deadline-bounded role policies that consume only local observations/beliefs and select legal actions. The Police policy combines belief-aware pursuit, information gain, graph cuts, and barrier-budget control. The Thief policy combines survival risk, reachable space, route diversity, entropy, scent exposure, anti-corner, and anti-cycle behavior.

Out of scope: physics legality, posterior construction, network phases, and natural-language realization.

## Inputs

- immutable local-view state;
- ordered engine-generated legal actions;
- normalized opponent belief or particles;
- public barriers/history, received hints, and calibrated trust;
- role-specific private strategy profile;
- injected deterministic RNG, monotonic deadline, and opponent summary derived only from legal observations.

## Outputs

- one action present in the provided legal-action set;
- concise redacted explanation and feature-score breakdown;
- latency/fallback/seed/version metrics;
- updated legally derived opponent-policy summary.

## Invariants

1. Final action always belongs to the current engine-provided legal set.
2. Thief never returns a barrier.
3. Same inputs/profile/seed produce the same decision.
4. Deadline miss/exception returns deterministic legal fallback within 50 ms.
5. Search cannot access opponent truth, replay truth, secrets, transport, filesystem, or GUI.
6. Online adaptation uses only observations legally available before the decision.
7. Barrier planning respects exact quota and public mechanics.
8. Score improvement cannot trade away compliance, integrity, or reliability.

## Police outline

- candidate ordering: capture, high-probability intercept, high-value legal barrier, safe pursuit, information action, hold;
- features: expected capture, posterior mass intercepted, shortest-path reduction, reachable-region cut, articulation/corridor effect, information gain, self-block risk, barrier scarcity, opponent adaptation, latency;
- search: iterative deepening over belief samples with transposition/cache keys that exclude hidden truth;
- budget: reserve barriers for high-confidence, high-cut-value states and terminal opportunities.

## Thief outline

- candidate ordering: terminal-safe escapes, high-distance/high-space, route-diverse, low-scent, low-corner, low-cycle, deceptive positioning, hold only when strategically justified;
- features: capture risk over belief samples, distance distribution, reachable region, disjoint routes, boundary/corner penalty, scent exposure, Police barrier potential, repeat/cycle risk, future entropy;
- mode switching: escape, conceal, reposition, exploit overcommitment, endgame survival.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| STR-AC-001 | Every random/corrupt strategy output passes final legal guard or falls back. | property/fuzz tests |
| STR-AC-002 | Decision is deterministic under same seed/config/observations. | replayed-decision tests |
| STR-AC-003 | Fallback p99 <=50 ms and normal p95 <=250 ms on declared baseline CPU. | benchmark |
| STR-AC-004 | No objective/replay/private-opponent field is reachable. | type/privacy tests |
| STR-AC-005 | Police capture and Thief survival each meet >=70% baseline target. | holdout tournament |
| STR-AC-006 | Official-score uplift is >=20 points with no fixture-family collapse >15 points. | paired holdout report |
| STR-AC-007 | Ablations quantify belief/search/opponent/barrier/risk contribution. | experiment artifacts |
| STR-AC-008 | Technical/tamper/illegal-action rate remains zero in evaluation. | reliability gate |

## Finalization checklist

- exact interfaces and feature definitions/scales;
- deterministic tie-breaking and fallback;
- search horizon/sample/time budgets;
- cache invalidation and complexity;
- opponent-model update policy;
- hyperparameter schema and safe ranges;
- baseline and holdout protocol from `docs/EXPERIMENTS.md`.

