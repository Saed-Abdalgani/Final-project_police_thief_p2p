# Competitive Strategy Mechanism

## Runtime path

Adapters call `SimulationSdk.choose_strategy_action`. The SDK takes strategy
selectors only from validated private TOML and world/hint bounds only from the
shared constitution. `StrategyService` resolves an allowlisted role brain,
provides a monotonic cutoff and seeded RNG, validates the returned `Decision`, and
falls back to a deterministic legal baseline on every failure class.

Police minimizes posterior-expected graph distance and searches movement, hold,
and pruned barrier candidates. Its score covers proven capture, distance,
reachable-region reduction, disjoint-route cuts, information value, self-trap,
barrier opportunity cost, cycles, and CVaR downside. A belief-proven direct or
barrier capture receives an overriding priority; placing a barrier on the
Police's own cell receives the maximum self-isolation penalty.

Thief maximizes downside distance over the full Police posterior, bounded future
space, disjoint routes, and uncertainty while penalizing trap probability, scent
concentration, corners with too few exits, revisits, and cycles. Deterministic
rules switch between mobility, deception, escape, and anti-trap modes. Only
near-equivalent safe ties use the seeded RNG.

## Safety and adaptation

- Candidate actions always originate in the domain engine.
- The request and telemetry types cannot represent opponent true position.
- Online profiles accept public action/verdict features only.
- Boundary/revisit path features require completed audit evidence.
- Profiles persist under exact opponent group plus strategy version.
- Explanations are reason codes and finite feature summaries; hints and private
  state never enter telemetry.
- Default language play uses no remote calls or tokens.

## Reproducibility and evidence

The decision seed, profile version, candidates, deepest completed search, cache
hits, finite score breakdown, latency, reason, and fallback status are recorded.
Golden, property, privacy, injection, deadline, profile-isolation, and graph
scenarios live in `tests/`. The reproducible benchmark and initial paired
decision tournament are in `results/benchmarks/m7_strategy.json`.

M7 is an implementation gate, not permission to tune on the final M12 holdout.
The split/freeze rules in `docs/EXPERIMENTS.md` remain binding.
