# M7 and M8 Exit Evidence

- **Milestones:** M7 competitive strategy; M8 orchestration and reliability
- **Package/protocol:** `0.7.0`
- **Date:** 2026-07-25
- **Branch:** `main`
- **Status:** `APPROVED` for M9 entry

## Candidate quality results

| Control | Result |
|---|---|
| Ruff formatting and lint | Pass: 247 Python files |
| Strict mypy | Pass: 247 Python files |
| Repository validators | Pass: structure, hygiene, size, imports, traceability, CI |
| Full test campaign | Pass: 403 tests |
| Branch-aware coverage | Pass: 90.88% |
| Python source size | Pass: no file over 150 code lines |
| M7 deterministic evidence | Pass |
| M8 1,000-sub-game soak | Pass |

## M7 competitive strategy review

The SDK strategy boundary accepts only local state, belief, public history,
validated private policy config, seeded randomness, and a monotonic deadline.
Police and Thief use separate role brains, full-posterior sampling, risk-sensitive
bounded search, engine-originated legal candidates, deterministic fallback, and
safe telemetry. Hint semantic intent is movement-independent and is sealed into
commitment version `1.1.0`; templates remain zero-token and optional language
providers have strict parsing and fallback.

The reproducible campaign in `results/benchmarks/m7_strategy.json` records:

| Gate | Result |
|---|---|
| Strategy p50 / p95 / max | 105.469 / 205.110 / 210.516 ms |
| Fallbacks | 0 of 20 |
| Police paired reference losses | 0 of 20 |
| Thief paired reference losses | 0 of 20 |
| Legal outputs / zero-token default | Pass / Pass |

The initial ablation review preserves explicit evidence for each contribution:

| Removed contribution | Observed mechanism evidence |
|---|---|
| Full belief | Argmax reference loses or ties the full-posterior policy |
| Iterative search | Deadline tests preserve the deepest complete search |
| Opponent model | Uniform/learned-mixture fixtures change legal response weights |
| Barrier graph | Corridor, cut, route, and self-isolation golden cases |
| Deception | Truth-only and trust-aware semantic schedules diverge deterministically |
| CVaR risk | Downside-tail fixtures reject higher-variance unsafe choices |

Appendix E rule 25 is satisfied by algorithmic movement with optional language-only
LLM authority. Rule 26 is satisfied by bounded free natural-language hints. Rule
27 is satisfied by coarse semantic regions and rejection of numeric location
protocols. FR-STR-001..017 are covered by unit, property, security, integration,
and performance tests. The M12 frozen final holdout remains untouched.

## M8 reliability review

`PeerOrchestrator` is the sole SDK lifecycle coordinator and depends only on typed
ports. It drives reason-specific compare-and-set transitions, immutable terminal
states, monotonic operation deadlines, retry classification, circuit breaking,
bounded priority queues, persist-before-acknowledge, exact mutual checkpoint
recovery, independent Watchdog monitoring, and ordered cooperative shutdown.

The reproducible campaign in `results/benchmarks/m8_reliability.json` records:

| Gate | Result |
|---|---|
| Seeded persistent sub-games | 1,000 completed |
| Progress checks / journal records | 18,000 / 17,000 |
| Deadlocks | 0 |
| Unbounded waits | 0 |
| Terminal distribution | 1,000 completed; no unexpected terminal |

Appendix E rules 3-7 are satisfied respectively by the SDK Orchestrator gateway,
formal phase machine, mutation-free illegal transition rejection, monotonic
deadlines, and an independent Watchdog with redacted recovery intervention.
FR-ORC-001..013 and NFR-REL controls are exercised by lifecycle, race, crash,
network-fault, recovery-disagreement, queue, tunnel, and soak tests.

## Sign-off

| Accountable role | Decision | Evidence reviewed |
|---|---|---|
| Strategy Lead | Approved | M7 role policies, language safety, paired matrix, ablations |
| Reliability Lead | Approved | M8 state machine, deadlines, persistence, recovery, soak |
| Security Lead | Approved | private selectors, taint boundaries, commitments, redaction |
| Architecture Lead | Approved | SDK gateway and port-only Orchestrator boundary |
| QA Lead | Approved | 403 tests, 90.88% branch-aware coverage, all validators |

This report signs the implementation candidate represented by the commit that
contains this file; the immutable Git commit is the evidence identity.
