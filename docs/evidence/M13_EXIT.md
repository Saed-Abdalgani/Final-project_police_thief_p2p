# M13 Documentation, Two-Repository Release, and Submission Exit

**Candidate package:** `0.11.0`
**Review date:** 2026-08-06
**Decision:** CONDITIONALLY READY
**Severity gate:** competitive holdout, external tunnels, Moodle PDF, and lecturer access remain open

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

## Outstanding / EXTERNAL

| Item | Owner | Notes |
|---|---|---|
| M12 holdout competitive gates | Strategy | `R02-DEADLINE`, `S03-THIEF` in `m12_selection.json` |
| T608/T609 public tunnels on two machines | Operations | Loopback rehearsal passed; external not verified |
| Moodle form PDF layout check | Release Lead | No template in-repo; EXTERNAL |
| Lecturer access confirmation | Release Lead | EXTERNAL |
| Full clean-clone pytest in both exports | Release Lead | Structure/readiness verify is automated; full suite is time-gated |

## Decision rule

`READY` is not recorded because mandatory competitive and EXTERNAL submission
items remain open. The packaging, documentation, and sibling repositories are
complete enough for `CONDITIONALLY READY`.

**Signed:** Coding agent release pass — 2026-08-06
