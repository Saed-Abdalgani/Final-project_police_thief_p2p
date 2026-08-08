# Moodle form field package (paste-ready)

Use these values in the lecturer-provided Moodle form (`uoh-rl07-final-project-2026.docx`)
**without moving fields**. Export the filled form to PDF and visually compare layout
to the course template.

Audit detail: [`SUBMISSION_AUDIT.md`](SUBMISSION_AUDIT.md).

| Field | Value | Status |
|---|---|---|
| Group / Police peer ID | `GRP00001` | READY |
| Thief peer ID (sibling) | `GRP00002` | READY |
| Canonical development repository | https://github.com/Saed-Abdalgani/Final-project_police_thief_p2p | READY |
| Cop / Police standalone repository | https://github.com/JCS1029/GRP00001-police-p2p | READY |
| Thief standalone repository | https://github.com/JCS1029/GRP00001-thief-p2p | READY |
| Submission tag (both role repos) | `v1.0-submission` | READY |
| Package version | `0.11.0` | READY |
| Protocol / schema | `0.7.0` / `0.2.0` | READY |
| Exit decision | `CONDITIONALLY READY` — technical gates PASS; Gmail + external opponents open | see M13 |
| Live belief screenshot | `docs/screenshots/m10_live_local_view.svg` | READY |
| Replay Verified OK screenshot | `docs/screenshots/m10_replay_verified.svg` | READY |
| Tuning results | `results/benchmarks/m12_tuning.json` | READY |
| Holdout/selection results | `results/benchmarks/m12_selection.json` | READY |
| Language comparison | `results/benchmarks/m12_language.json` | READY |
| League rehearsal (loopback) | `results/benchmarks/m12_league_rehearsal.json` | READY |
| Two-machine public tunnels | `results/benchmarks/two_machine_playtest.json` | READY |
| AI Agent email that sent lecturer results | *(fill after real Gmail send)* | BLOCKED |
| Legal games played and emailed | *(fill after opponent series)* | BLOCKED |
| Max points / W / L / D | *(fill after opponent series)* | BLOCKED |
| Opponent match table rows | *(≥2 different teams; not self-play)* | BLOCKED |
| Student identity fields | *(each member)* | OPERATOR |

## Per-member reminder

Each member submits the same two repository links and group ID. Do not attach secrets,
OAuth token files, or private TOML with live credentials.

## Live GUI (optional visual check)

```text
uv run python -m police_thief_p2p.adapters.gui
```
