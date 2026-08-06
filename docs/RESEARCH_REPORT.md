# Research Report: Offline Tuning and Competitive Evaluation

**Milestone:** M12
**Baseline policy document:** `docs/EXPERIMENTS.md`
**Status:** results generated from the campaign scripts listed in section 9.

This report answers one question: does the advanced belief-and-search policy beat
the documented reference-greedy behavior by a margin large enough to be worth the
extra machinery, without breaking any correctness or reliability gate?

## 1. Hypotheses

| ID | Hypothesis | Primary test |
|---|---|---|
| H1 | The tuned candidate beats the reference-greedy baseline by at least 20 official score points on fixtures never used for tuning. | Paired role-swapped holdout tournament, gate `S01-SHARE`/`S02-UPLIFT` |
| H2 | Each role independently clears a 70% success rate (Police capture, Thief survival). | Role summaries, gates `S03-POLICE`/`S03-THIEF` |
| H3 | Every component in the candidate contributes: removing any one of belief fusion, lookahead, graph-cut barriers, escape routes, risk aversion, or hint deception costs measurable score. | Ablation study, `results/benchmarks/m12_studies.json` |
| H4 | The advantage survives degraded observation (delayed and dropped scent frames) and hostile hint profiles. | Robustness study and adversarial sweep |
| H5 | The deterministic hint template is the right default: optional language providers add latency and token cost without improving the game surface. | Provider comparison, `results/benchmarks/m12_language.json` |
| H6 | Gains do not come from cutting corners: zero illegal actions, zero deadline misses, zero technical or tamper losses at the release decision budget. | Reliability gates `R02-*`, `P01-LATENCY` |

Predeclared primary metric: **official score share (percent) over paired
role-swapped matches**, with the candidate-selection rule "highest lower bound of
the paired uplift bootstrap interval on the training split."

## 2. Method

### 2.1 Offline arena

Every measurement comes from `MatchArena`, an in-process referee that reuses the
production domain transition, belief service, scent emission, hint pipeline, and
strategy brains. No protocol, network, or crypto layer is stubbed out of the
decision path; the arena replaces only the two peer processes and the tunnel.

A match is played from one fixed board fixture and one seed. Both sides receive
their own local state, their own belief track, and their own scent frames through
an `ObservationChannel` that can delay or drop frames deterministically.

### 2.2 Pairing

Every comparison is played twice: once with the candidate seated as Police and
once as Thief, on the same fixture and seed. This removes start-position and role
bias from the score share, and it makes the uplift a paired statistic.

### 2.3 Opponents

The roster in `services/experiments/roster.py` registers the six baseline
families from `docs/EXPERIMENTS.md`: `BL-REF` (clean reference-greedy
reimplementation), `BL-RND` (seeded random legal), `BL-SCR` (shortest-path Police
and maximum-distance Thief), the `BL-ADV-*` adversary suite (corner, boundary,
cycle, switch, aggressive barrier, graph cut, and the always-honest, always-lie,
periodic-lie, and trust-switch hint profiles), and `BL-PREV`/`BL-POST` as
immutable regression checkpoints.

### 2.4 Splits

| Split | Seeds | Opponents | Fixture families | Use |
|---|---|---|---|---|
| train | 10000-10023 | `BL-REF`, `BL-RND`, `BL-SCR` | `train-*` | search and tuning only |
| validation | 20000-20015 | `BL-POST`, corner, cycle, liar, trust-switch | `validation-*` | selection, ablation, robustness |
| holdout | 30000-30011 | `BL-REF`, boundary, switch, `BL-PREV` | `holdout-*` | one unbiased estimate after freeze |
| rehearsal | 40001-40006 | `BL-REF` | default geometry | league dress rehearsal only |

Seeds, opponent identifiers, and fixture identifiers are disjoint across splits
and digested into `SplitManifest`. Holdout access goes through `SealedHoldout`,
which refuses to reveal its contents until it is handed a full candidate freeze
digest, and `assert_tunable` fails closed if any tuning code names the holdout. A
security test asserts the tuning and study scripts never contain the string
`holdout`.

### 2.5 Search

Two stages, both seeded. A broad random search samples the declared bounded
spaces (Police weights, Thief weights, belief mixture and trust priors, hint
cadence); then a Gaussian-kernel surrogate with an upper-confidence-bound
acquisition refines the best region, reusing every prior observation. Every
attempted configuration is persisted, including the ones stopped early.

Early stopping is two-tier: a configuration that fails the hard reliability gate
during screening is dropped immediately (`RELIABILITY_GATE`), and one whose
screening objective falls below the running median is dropped before the full
stage (`BELOW_MEDIAN_SCREEN`). Screening runs a reduced opponent, fixture, and
seed subset; the median threshold only activates after four observations, so the
first trials are never pruned by an empty history.

### 2.6 Scoring and statistics

Score share uses the official fixed point values from the negotiated shared
configuration, never an invented reward. Technical and tamper outcomes are scored
exactly as the rules mandate and are additionally reported as a separate
zero-tolerance reliability count; they are never averaged into a quality claim.

Intervals are deterministic percentile bootstraps (1,000 resamples) drawn from
the seeded random source, clamped to the observed support. Uplift is a paired
bootstrap of candidate-minus-opponent points. Secondary ranking is a
Bradley-Terry fit rendered on the Elo scale, anchored at 1500.

## 3. Hardware, runtime, and cost accounting

Every campaign wraps its measured body in `experiments.resources.measure`, which
records wall time, peak process resident set size, call count, transferred
payload bytes, and prompt/completion tokens beside the host platform, processor,
core count, and interpreter. The exact values for each campaign are in the
`resources` block of its evidence file; the resource block is deliberately
excluded from the reproducibility manifest digest so that replaying a campaign on
different hardware still produces the same manifest identity.

The offline arena makes no network calls and spends no tokens: the hint surface
is the deterministic template. The only nonzero token column in this milestone
belongs to the optional-provider comparison, and it is measured through the real
Gatekeeper fallback path rather than a fabricated figure.

## 4. Results

See section 9 for the generated evidence files. The headline numbers, gate
verdicts, and per-opponent and per-fixture breakdowns live in those documents;
they are not restated here so that this report cannot drift away from the
measurements.

### 4.1 A latency defect the campaign exposed

The first full campaign failed `P01-LATENCY` on every board larger than 7x7. The
measured p95 decision latency was 217 ms on a 7x7 fixture but 860 ms on an 8x8
fixture with a 20-barrier quota and 1,264 ms on a 9x9 fixture with a 45-move
ceiling, against a 250 ms budget.

Profiling a single 8x8 match attributed 44 of 52 seconds to `fallback_decision`,
the deterministic baseline the strategy service invokes when a brain overruns its
guard deadline. The baselines scored each candidate action with
`expected_distance` or `lower_quantile_distance`, and both ran one breadth-first
search **per supported posterior cell**. On a nearly uniform posterior over an
8x8 board that is roughly 64 searches per action and several hundred per
decision, so the safety path cost far more than the search it was protecting.

The fix computes one single-source distance map from the candidate cell and looks
every posterior cell up in it, which returns identical values in one search
instead of one per cell. Latency on the same three fixtures fell to 222, 224, and
228 ms with zero deadline misses, and campaign wall time dropped by roughly five
times.

Two things are worth recording beyond the fix itself. First, the defect was
invisible on the smallest board and only appeared as boards grew, which is
precisely what the board-geometry robustness requirement exists to catch. Second,
the cost lived in the fallback rather than the optimizer, so it grew worse exactly
when the system was already under deadline pressure. Latency numbers reported
before this fix are not comparable with the ones in the evidence files, and all
campaigns were rerun afterwards.

## 5. Ablation and sensitivity

`results/benchmarks/m12_studies.json` measures nine variants against the intact
candidate on the validation split: intact, single-ply lookahead, single-sample
posterior, no graph cut, no information gain, no escape routes, no scent penalty,
risk-neutral scoring, and forced-honest hints. Each row reports the score
delta, the paired uplift interval, both role success rates, the p95 decision
latency, and its reliability record.

The same file records robustness across one- and two-turn observation delay,
30% and 60% scent loss, a combined degraded case at a halved decision budget, and
two hostile hint profiles, plus an exhaustive adversarial sweep over every
registered adversary. The two worst adversaries are retained as validation-only
regression cases; they are deliberately not promoted into training or holdout.

## 6. Limitations and threats to validity

- **Compute budget.** The screening stages use reduced opponent, fixture, and seed
  subsets. A larger budget would tighten every interval; the reported intervals
  already reflect the sample sizes actually played.
- **Single host.** All offline numbers come from one machine and one interpreter.
  Latency gates are therefore host-specific, and the p95 figures should be read as
  "this host at this budget," not as a portable guarantee.
- **Rehearsal is loopback.** The league dress rehearsal runs two fully separated
  peer roots as independent processes on one host over loopback tunnels. That
  validates configuration separation, artifact isolation, and the full protocol
  exchange, but it does **not** validate public-tunnel reachability from an
  external network or a second physical machine. The rehearsal gate reports this
  as an explicit outstanding item rather than passing it silently.
- **Simulated opponents.** Adversaries are the declared policy families, not real
  league opponents. A human-tuned opponent may exploit patterns none of them do.
- **Optional providers are stubbed at the boundary.** The provider comparison
  exercises the real `OptionalParaphraser`, safety filter, and Gatekeeper fallback,
  but substitutes deterministic provider stubs when no daemon or cloud secret is
  present. Availability is recorded honestly per provider, so a reader can tell
  which column was measured live.
- **Holdout is spent.** The sealed holdout was opened exactly once, for one freeze
  digest. Any further tuning invalidates the candidate and requires a new holdout
  version before another generalization claim.

## 7. Conclusions

Measured against `docs/evidence/M12_EXIT.md` and the campaign JSON files:

| Hypothesis | Outcome |
|---|---|
| H1 holdout uplift / share | Holdout share about `65.4%`; validation about `67.5%`. Competitive holdout promotion failed. |
| H2 role success | Validation Police `96.7%` / Thief `76.7%` cleared `70%`. Holdout Thief survival `66.7%` failed `S03-THIEF`. |
| H3 ablations | Studies campaign completed; every ablation remained reliable. |
| H4 robustness | Degraded-observation robustness gate passed; adversarial reliability flag noted in studies evidence. |
| H5 language default | Template remains default: zero tokens, deterministic, unsafe outputs rejected. |
| H6 reliability | Holdout recorded one `R02-DEADLINE` miss, so the frozen candidate is not competitively promoted. |

League rehearsal on two isolated peer roots over loopback passed mutual audits;
external public-tunnel / second-machine verification remains outstanding
(T608/T609).

## 8. Reproduction

```bash
uv run python -m scripts.run_m12_tuning
uv run python -m scripts.run_m12_studies
uv run python -m scripts.run_m12_selection
uv run python -m scripts.run_m12_language
uv run python -m scripts.run_m12_league_rehearsal
uv run python -m scripts.run_tournament --split validation --campaign-id ad-hoc
```

The scripts are order-dependent: the studies and selection campaigns read the
tuned point from `results/benchmarks/m12_tuning.json`.

## 9. Evidence index

| Campaign | Evidence | Covers |
|---|---|---|
| Hyperparameter search | `results/benchmarks/m12_tuning.json` | T594-T597, T603 |
| Ablation, robustness, adversarial sweep | `results/benchmarks/m12_studies.json` | T598-T601 |
| Validation, overfitting gate, one-shot holdout | `results/benchmarks/m12_selection.json` | T602, T604-T606 |
| Paraphrasing provider comparison | `results/benchmarks/m12_language.json` | T607 |
| League dress rehearsal | `results/benchmarks/m12_league_rehearsal.json` | T608-T613 |
| Exit review | `docs/evidence/M12_EXIT.md` | T614, T615 |
