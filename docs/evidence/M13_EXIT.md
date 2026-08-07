# M13 Documentation, Two-Repository Release, and Submission Exit

**Candidate package:** `0.11.0`
**Review date:** 2026-08-07
**Decision:** CONDITIONALLY READY
**Severity gate:** operator submission residuals only (Gmail receipt / Moodle PDF); M12 competitive and two-machine tunnel gates PASS

## Delivered in this tree

| Item | Evidence |
|---|---|
| Academic README sections + sibling links | `README.md` |
| Schema catalog | `docs/SCHEMAS.md` |
| Protocol/ops/security/research finalize | `docs/PROTOCOL.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`, `docs/RESEARCH_REPORT.md` |
| Export manifests | `release/export_manifests/*.json` |
| Export / verify tooling | `scripts/export_role_repo.py`, `scripts/verify_release.py` |
| Submission checklist | `docs/evidence/M13_SUBMISSION_CHECKLIST.md` |
| Police sibling repository | https://github.com/JCS1029/GRP00001-police-p2p |
| Thief sibling repository | https://github.com/JCS1029/GRP00001-thief-p2p |
| Annotated tag target | `v1.0-submission` on both exports |
| Two-machine public-tunnel playtest | `results/benchmarks/two_machine_playtest.json` |

## Outstanding residuals

| Item | Owner | Notes |
|---|---|---|
| Real Gmail send receipt (T469) | Release Lead | No OAuth secrets in workspace; dry-run path already evidenced |
| Official Moodle PDF visual compare | Release Lead | Paste package in `MOODLE_FORM_PACKAGE.md`; template not in-repo |

M12 holdout + tunnel evidence: `docs/evidence/M12_EXIT.md`,
`results/benchmarks/m12_selection.json`, `results/benchmarks/two_machine_playtest.json`.

TODO closure evidence for T469/T509/T608/T609/T641/T642:
`docs/evidence/FINAL_TODO_CLOSURE.md`.

## Decision rule

`READY` is not recorded only because Gmail/Moodle operator items remain open. Packaging,
documentation, sibling repositories, repaired holdout, and two-machine public-tunnel
rehearsal are complete enough for `CONDITIONALLY READY`.

**Signed:** Coding agent release pass — 2026-08-07
