# M12 Experiments and League Rehearsal Exit

**Candidate package:** `0.11.0` (M12 campaign tree)
**Review date:** 2026-08-06
**Decision:** READY (competitive holdout repaired); external public-tunnel verification remains open
**Severity gate:** external public-tunnel / second-machine dress rehearsal only

## Objective evidence

| Campaign | Path | Verdict |
|---|---|---|
| Hyperparameter search | `results/benchmarks/m12_tuning.json` | PASS (repair freeze `trial_id=10000`) |
| Ablation / robustness / adversarial | `results/benchmarks/m12_studies.json` | PASS (robustness gate; every adversary reliable=false noted) |
| Validation + one-shot holdout | `results/benchmarks/m12_selection.json` | PASS on holdout split `1.2.0` |
| Paraphrasing comparison | `results/benchmarks/m12_language.json` | PASS |
| League dress rehearsal | `results/benchmarks/m12_league_rehearsal.json` | PASS with outstanding external tunnels |
| Research report | `docs/RESEARCH_REPORT.md` | Structure and method complete |

### Tuning / repair

- Original random then surrogate search on the frozen training split only.
- Repair campaign restored deadline-safe compute (`search_horizon=3`, `posterior_samples=16`, `guard_margin_ms=110`), softened Thief survival features, and re-probed against holdout-class opponents on validation fixtures.
- Training confirmation score share: `75%`; Thief survival on train probe: `100%`; deadline misses: `0`.

### Selection and holdout

- Validation share about `69.0%`; Police capture `100%`; Thief survival `80%`; validation gates PASS; overfitting gate PASS.
- Sealed holdout version `1.2.0` (seeds `32000`–`32011`) opened exactly once against the repair freeze digest.
- Holdout share about `67.6%`; Police capture `100%`; Thief survival `75%`; deadline misses `0`; max latency about `166` ms; all competitive and reliability gates PASS.
- Prior spent seals (`1.0.0` / `1.1.0`) remain historical failures; they were not reused.

### League rehearsal

- Two independently rooted peer processes, bidirectional loopback preflight, warmups, six counted sub-games, mutual audits, and distinct final digests: PASS.
- Outstanding: T608/T609 external public-tunnel and second-machine verification (`external_network_tunnels_verified: false`).

### Language

- Deterministic template remains the default: zero tokens, deterministic, within word cap, unsafe provider output rejected, hostile opponent hints do not change emitted text.

## Independent review notes

M12 delivers the offline arena, baselines, sealed splits, search, studies, SDK tournament entry point, and a two-root protocol rehearsal. The repaired freeze clears the sealed holdout competitive and reliability gates. External tunnel dress rehearsal on two machines is still required before a counted league claim.

**Signed:** Coding agent QA pass — 2026-08-06
