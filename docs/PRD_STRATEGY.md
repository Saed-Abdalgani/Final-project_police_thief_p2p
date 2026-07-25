# Mechanism PRD - Competitive Police and Thief Strategy

**Status:** M7 implemented and approved
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

- [x] exact interfaces and feature definitions/scales;
- [x] deterministic tie-breaking and fallback;
- [x] search horizon/sample/time budgets;
- [x] cache invalidation and complexity;
- [x] opponent-model update policy;
- [x] hyperparameter schema and safe ranges;
- [x] baseline and holdout protocol from `docs/EXPERIMENTS.md`.

## Final contract

`StrategyBrain.decide(StrategyRequest) -> Decision` is the only plugin interface.
The request contains own `LocalGameState`, normalized `BeliefGrid`, engine-created
legal actions, bounded public history, the private strategy section, a normalized
legally learned opponent summary, injected clock/RNG, absolute deadline, and
shared map/hint limits. It cannot represent opponent truth, secrets, replay truth,
transport, or filesystem state.

The final guard accepts only an exact member of `LocalGameState.legal_actions()`;
Thief barriers are independently rejected. Exceptions, expired deadlines,
malformed decisions, non-finite scores, and empty search results select the
posterior-aware deterministic role baseline. The guard cutoff reserves 40 ms for
commitment/persistence under the default 250 ms decision budget.

Search uses 16 deterministic equal-mass posterior samples, iterative depths 1-3,
a 512-entry deterministic LRU transposition cache, a 25% downside tail, and the
private risk weight. Only a fully completed depth can replace the incumbent.
Thief stochastic tie-breaking is limited to safe actions within 2% of the best
score and is reproducible from the signed experiment seed.

All weights live under private `[strategy.police]` and `[strategy.thief]`, are
finite/non-negative and bounded, and carry semantic `profile_version`. Selectors
are restricted to `police_thief_p2p.services.strategy.<module>.<StrategyBrain>`.
Cross-sub-game opponent profiles are keyed by exact opponent/version; live
updates cannot contain hidden path features, while richer path features require a
completed audit.

Hint intent is selected separately from movement. Deterministic templates are the
zero-token default, use Unicode-aware word counting, contain no numeric coordinate
protocol, and bind realized text, semantic region, and truth/lie verdict into
commitment version `1.1.0`. Optional paraphrasing receives only quoted inert hint
data through Gatekeeper and must return exact bounded JSON text or fall back.
