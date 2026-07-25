# Mechanism PRD - Language, Scent, and Bayesian Belief

**Status:** M0 approved outline; finalize before M6/M7 implementation
**Owner:** Belief Lead with Strategy Lead
**Requirements:** FR-BEL-001..015, FR-STR-010..017
**Rules/parameters:** Appendix E 23, 25-27; F-007, F-008, F-013..F-015, F-024

## Purpose and scope

Create interoperable scent evidence, normalized local opponent beliefs, calibrated natural-language hint influence, and safe zero-token/optional-LLM language providers. Language may deceive through words and sealed truth/lie intent; it may not become a numeric location protocol.

## Inputs

- local movement/stay event;
- signed 5x5 kernel, center intensity, decay, rounding/clamp policy, and numeric example;
- public barriers and legal-cell mask;
- opponent scent observation available to this peer;
- received bounded natural-language hint;
- local history of hint consistency;
- private language provider profile and Gatekeeper budget/deadline.

## Outputs

- own emitted/decayed scent frame for protocol/audit;
- normalized opponent belief distribution or particles;
- entropy, credible region, peak, calibration, degeneracy/fallback diagnostics;
- bounded natural-language hint and sealed `truth|lie` intent;
- provider latency/token/fallback metadata without secret/private disclosure.

## Invariants

1. Center intensity is exactly 0.9, window exactly 5x5, decay exactly 0.10.
2. Emission is symmetric/non-negative and clipped at boundaries under one signed numeric policy.
3. Scent emits after move or stay and decays once per full Police-plus-Thief turn.
4. An agent observes only opponent scent and never opponent true position.
5. Belief is finite, non-negative, normalized, and zero on impossible/barrier cells.
6. Prediction precedes observation update.
7. All-zero updates use a documented valid fallback prior.
8. Hint evidence is bounded by calibrated reliability and never treated as truth.
9. Hints obey the word cap and cannot encode direct coordinates/protocol fields.
10. Template mode completes a series with zero LLM calls/tokens.
11. Optional LLM input/output is minimal, deadline/token bounded, strictly parsed, and safely falls back.

## Belief update outline

`prior -> motion prediction -> legal-cell mask -> scent likelihood -> bounded hint likelihood -> normalize -> diagnostics/fallback`

The exact kernel matrix/formula, clipping, accumulation, decay order, numeric precision, rounding, likelihood model, trust prior/update, and fallback distribution are signed and versioned before code interoperability is accepted.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| LSB-AC-001 | Independent peers reproduce signed scent numeric vectors exactly. | cross-repository golden vectors |
| LSB-AC-002 | Boundary/corner emission, accumulation, and turn decay are deterministic. | unit/property tests |
| LSB-AC-003 | Posterior remains valid under extreme, missing, delayed, contradictory, and all-zero evidence. | property/fault tests |
| LSB-AC-004 | Impossible/barrier cells remain zero after every update. | invariant tests |
| LSB-AC-005 | Hint trust responds to observed consistency without accessing hidden verdict before audit. | calibration tests |
| LSB-AC-006 | Numeric-coordinate/protocol-like hints, excess words, malformed LLM output are blocked/fallback. | adversarial language tests |
| LSB-AC-007 | Default six-game series records zero tokens and no external language call. | token ledger |
| LSB-AC-008 | Optional provider never exceeds signed budget/deadline and cannot choose moves without capability. | Gatekeeper/integration tests |

## Finalization checklist

- signed kernel/formula and worked numeric example;
- precision/rounding/serialization;
- motion-mixture and likelihood equations;
- hint parser, prohibited encoding policy, and trust calibration;
- provider interface, prompt fields, output schema, budgets, fallbacks;
- diagnostic fields and privacy review.

