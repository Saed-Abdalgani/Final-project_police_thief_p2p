# M3 Domain Review

- **Review date:** 2026-07-25
- **Milestone:** M3 - Domain physics and scoring
- **Current decision:** `PENDING FINAL VERIFICATION`

## Rule review

- [x] E-011/E-012 configuration identity and stricter minima remain enforced by M2.
- [x] E-013 permits exactly one N/S/E/W step or STAY.
- [x] E-014 rejects diagonal and multi-cell movement.
- [x] E-015 exposes every exact barrier target as an immutable public event.
- [x] E-016 has no hidden barrier state or alternate private placement path.
- [x] E-046 resolves a barrier on the verified Thief cell as capture.
- [x] E-047 excludes STAY from spatial enclosure escape.
- [x] E-048 maps every terminal reason through the fixed scoring table.

## Architecture and quality review

- [x] Live state contains no opponent truth field.
- [x] Position, actions, barriers, state, events, outcomes, schedules, and scores are
  immutable.
- [x] Police self-barrier behavior is explicit and tested.
- [x] Barriers are permanent and universally block movement targets.
- [x] Transition order and action/event order are deterministic.
- [x] Group totals survive three role swaps without accidental role-total swaps.
- [x] SDK exposes initialization, legality, transition, schedule, and aggregation.
- [x] Protected adapters remain unable to import domain internals.
- [x] Public API inventory is complete and documented.
- [x] Golden scenarios cover all required terminal/scoring families.
- [x] Hypothesis executes at least 10,000 legal transition examples.
- [x] Minimum and expanded-board performance budgets pass.

## Verification gate

The decision becomes `READY` only after frozen sync, static gates, all tests and
coverage, pre-commit/secret scan, package build/installed-wheel smoke, benchmark
evidence, and an exact-candidate clean-clone run pass.
