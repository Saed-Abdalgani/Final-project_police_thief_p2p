# M13 Documentation, Two-Repository Release, and Submission Exit

**Candidate package:** `0.11.0`
**Review date:** 2026-08-06
**Decision:** CONDITIONALLY READY
**Severity gate:** external/submission residuals only; M12 holdout competitive gates now PASS

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

## Outstanding residuals

| Item | Owner | Notes |
|---|---|---|
| External public-tunnel / second-machine rehearsal | Ops | T608/T609; loopback rehearsal already PASS |
| Real Gmail send receipt (T469) | Release Lead | No OAuth secrets in workspace; dry-run path already evidenced |
| Official Moodle PDF visual compare | Release Lead | Paste package in `MOODLE_FORM_PACKAGE.md`; template not in-repo |

M12 holdout repair evidence: `docs/evidence/M12_EXIT.md` and
`results/benchmarks/m12_selection.json` (`result: PASS`, split `1.2.0`).

TODO closure evidence for T469/T509/T608/T609/T641/T642:
`docs/evidence/FINAL_TODO_CLOSURE.md`.

## Decision rule

`READY` is not recorded because EXTERNAL submission items remain open. The
packaging, documentation, sibling repositories, and repaired M12 competitive
holdout are complete enough for `CONDITIONALLY READY`.

**Signed:** Coding agent release pass — 2026-08-06
