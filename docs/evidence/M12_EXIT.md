# M12 Experiments and League Rehearsal Exit

**Candidate package:** `0.11.0` (M12 campaign tree)
**Review date:** 2026-08-06
**Decision:** CONDITIONALLY READY
**Severity gate:** competitive holdout and external public-tunnel verification remain open

## Objective evidence

| Campaign | Path | Verdict |
|---|---|---|
| Hyperparameter search | `results/benchmarks/m12_tuning.json` | PASS (freeze recorded) |
| Ablation / robustness / adversarial | `results/benchmarks/m12_studies.json` | PASS (robustness gate; every adversary reliable=false noted) |
| Validation + one-shot holdout | `results/benchmarks/m12_selection.json` | FAIL on holdout |
| Paraphrasing comparison | `results/benchmarks/m12_language.json` | PASS |
| League dress rehearsal | `results/benchmarks/m12_league_rehearsal.json` | PASS with outstanding external tunnels |
| Research report | `docs/RESEARCH_REPORT.md` | Structure and method complete |

### Tuning

- Random then surrogate search on the frozen training split only.
- Best trial objective (paired uplift lower bound): `7.5`.
- Training confirmation score share: about `72%`.
- Resource ledger recorded wall time, peak RSS, calls, and zero LLM tokens.

### Selection and holdout

- Validation share about `67.5%`; Police capture `96.7%`; Thief survival `76.7%`; validation gates PASS; overfitting gate PASS.
- Sealed holdout opened exactly once against the freeze digest.
- Holdout share about `65.4%`; Police capture `100%`; Thief survival `66.7%`.
- Holdout failures:
  - `R02-DEADLINE`: one decision deadline miss.
  - `S03-THIEF`: Thief survival `66.7%` below the `70%` KPI.

### League rehearsal

- Two independently rooted peer processes, bidirectional loopback preflight, warmups, six counted sub-games, mutual audits, and distinct final digests: PASS.
- Outstanding: T608/T609 external public-tunnel and second-machine verification (`external_network_tunnels_verified: false`).

### Language

- Deterministic template remains the default: zero tokens, deterministic, within word cap, unsafe provider output rejected, hostile opponent hints do not change emitted text.

## Independent review notes

M12 delivers the offline arena, baselines, sealed splits, search, studies, SDK tournament entry point, and a two-root protocol rehearsal. Competitive promotion of the frozen candidate is blocked by the holdout reliability/role gate above. External tunnel dress rehearsal on two machines is still required before a counted league claim.

**Signed:** Coding agent QA pass — 2026-08-06
