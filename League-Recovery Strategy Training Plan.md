# League-Recovery Strategy Training Plan

## Summary

- Treat the failures as strategic, not protocol-related: all 18 sub-games passed audit with no tampering or technical loss.
- Baseline from the supplied results:
  - SMNGRP05: `0/6` wins, estimated score `30–90`.
  - ahk-yosi: `1/6` wins, estimated score `45–85`.
  - G005: `3/6`, an on-board `45–45` tie before the two-point series tie bonus.
  - Police captured in only `1/9` games; Thief survived `3/9`.
- Train a deterministic hybrid policy rather than an LLM: particle belief tracking, opponent classification, risk-sensitive lookahead, graph-cut barriers, minimax evasion, controlled randomization, and lawful deceptive hints.
- “Tricking” is limited to permitted natural-language lies and unpredictable mixed strategies. Never falsify movement, scent, capture, configuration, commitments, or audit evidence.

## Implementation Changes

### 1. Build a faithful compatibility training environment

- Add a thief-first offline arena matching the real compatibility wire:
  - pre-emission scent timing;
  - multiplicative and subtractive-Chebyshev scent models;
  - movement/barrier capture and enclosure;
  - 35-step survival;
  - role alternation and official scoring.
- Create clean-room behavioral sparring profiles for:
  - SMNGRP05’s containment Police and open-space Thief;
  - ahk-yosi’s velocity-intercept/squeeze Police and risk/juke Thief;
  - generic corner, boundary, cycle, random, aggressive-barrier, anti-intercept, and mid-game-switch opponents.
- Pin the public opponent revisions used for behavioral analysis: [SMNGRP05 Police](https://github.com/afaf-gharra/SMNGRP05-police/tree/2b41147664c9d7a76a7bcf70a47bfce36ec03885), [SMNGRP05 Thief](https://github.com/afaf-gharra/SMNGRP05-thief/tree/82206d6f384e2c031b01f927bc8d26e9e455bf5d), [ahk-yosi Police](https://github.com/yosefshanaa/p2p-police-agent/tree/3893ff0ed6ed8703331d9d39a270500c8c6d7a28), and [ahk-yosi Thief](https://github.com/yosefshanaa/p2p-thief-agent/tree/5f2942c79f411b2166ec54f039278ef744c19b03). Do not vendor or copy unlicensed ahk-yosi source.
- Treat G005 as an unknown-policy family because only its outcome summary is available.
- Preserve future post-audit peer records in ignored training sidecars so later tuning can use exact legal trajectories without changing official result artifacts.

### 2. Replace the single-cell greedy policy

- Introduce a stateful compatibility strategy session shared across all six sub-games.
- Replace scent argmax with a bounded sequential Monte Carlo tracker:
  - particles carry opponent position, simulated scent field, heading, and behavior family;
  - observations score complete received scent grids with the correct one-turn lag;
  - exact Police capture claims collapse the posterior when present;
  - barriers mask impossible paths;
  - hint likelihood remains bounded and cannot override strong scent evidence.
- Maintain an online Bayesian mixture over opponent archetypes using only public observations. After a successful audit, update the next sub-game’s model from revealed actions and hints; reject unaudited data.
- Police policy:
  - depth-3/4 belief-state expectimax over moves and legal barriers;
  - maximize capture probability and CVaR worst-case value;
  - predict turns, jukes, cycles, and boundary escape rather than extrapolating one heading;
  - switch to graph-cut containment when pursuit stops closing;
  - reserve barriers for posterior capture, corridor cuts, or provable enclosure;
  - prohibit self-isolation and tempo-wasting barriers.
- Thief policy:
  - apply a hard one-turn minimax veto to cells Police can immediately move onto, wall, or enclose;
  - maximize owned territory, graph distance, disjoint escape routes, future mobility, and worst-case survival;
  - penalize corners, boundary pockets, straight-run predictability, scent reinforcement, reversals, and cycles;
  - use secret-seeded mixed actions only among near-equivalent safe choices.
- Add legal hint deception:
  - emit one valid coarse region or landmark, never coordinates or malformed parser exploits;
  - select the decoy that maximizes expected opponent movement error;
  - use neutral hints when deception has insufficient value;
  - mark every deceptive audit payload as `lie`, enforce the 15-word cap, and limit consecutive lies.

### 3. Train, validate, and freeze

- Extend the existing random-plus-surrogate tuner with the compatibility profile:
  - particle count and observation sharpness;
  - opponent-mixture decay;
  - Police pursuit, intercept, cut, enclosure, risk, budget, and cycle weights;
  - Thief immediate-risk, territory, route, trap, scent, boundary, and unpredictability weights;
  - lookahead depth, CVaR tail, hint urgency, and lie cadence.
- Rank candidates lexicographically:
  1. zero illegal actions, technical failures, audit failures, and deadline misses;
  2. highest worst-family Police capture/Thief survival rate;
  3. highest worst-family official score share;
  4. average score share, latency, and barrier efficiency.
- Campaign:
  - screen 64 broad candidates;
  - fully evaluate the best candidates over eight opponent families and 12 training seeds;
  - run 24 surrogate-refined candidates;
  - validate the top five on 20 disjoint seeds with parameter perturbations and policy switching;
  - freeze one profile and evaluate it on 50 unseen seeds per role and family.
- If the frozen profile fails, promote those cases into validation, generate a fresh sealed holdout, and repeat. Never tune directly on a failed holdout.
- Store the winning weights and profile version in the tracked private strategy configuration, then bind deployment to its Git commit and profile digest.

## Interfaces

- Add SDK-facing types containing only lawful observations:
  - `CompatibilityTurnObservation`
  - `CompatibilityDecision`
  - `OpponentFingerprint`
  - `CompatibilityStrategyMetrics`
- Add:
  - `SimulationSdk.create_compatibility_strategy(terms, strategy, opponent_id, seed)`
  - session methods `start_subgame(...)`, `observe(...)`, `decide(...)`, and `complete_audited_subgame(...)`.
- Keep the existing wire schema unchanged. `PeerHalf` becomes a translation layer between wire messages and the SDK session.
- Change CLI seed behavior:
  - explicit `--seed N` remains deterministic for tests and rehearsals;
  - omitted seed generates a private per-series seed;
  - reveal it only in the post-series local training sidecar for replayability.
- Preserve the current `choose_move` entry point as a compatibility wrapper while migrating tests and runtime to the session API.

## Test and Deployment Gates

- Unit/property tests for particle normalization, exact scent timing, barrier masking, legal actions, capture/enclosure, opponent switching, seed reproducibility, and truthful `lie` audit labeling.
- Regression simulations must defeat the current lagged-scent, velocity-intercept, containment, corner-squeeze, cycle, and policy-switch fixtures.
- Integration tests must complete six-game loopbacks under both scent models with matching results, audits, and consensus hashes.
- Final deployment gate, separately for every held-out opponent family:
  - Police capture rate at least `80%`;
  - Thief survival rate at least `80%`;
  - official score share above `50%`;
  - zero illegal, technical, tamper, audit, or timeout outcomes;
  - strategy p95 at or below `250 ms`.
- Run targeted tests with coverage disabled, followed by the full `pytest`, Ruff, formatting check, mypy, build, and release verification.
- Deploy only the frozen profile that passes all gates; otherwise retain commit `622dc23` as the rollback baseline and report the remaining counterexample families.

## Assumptions

- Hybrid ensemble, robust `80%` acceptance, and summary-only evidence are the selected defaults.
- The supplied files are outcome summaries, not training trajectories.
- Winning every unknown future game cannot be guaranteed; deployment is gated by the agreed robust per-family threshold.
- No opponent service, repository, or live system will be attacked or disrupted; all counterplay remains inside the game’s permitted strategy and hint channels.
