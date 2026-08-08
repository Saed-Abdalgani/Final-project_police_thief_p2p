# M13 Moodle and Per-Member Submission Checklist

**Group IDs:** `GRP00001` (Police export default), `GRP00002` (Thief export default)
**Canonical repository:** https://github.com/Saed-Abdalgani/Final-project_police_thief_p2p
**Police export:** https://github.com/JCS1029/GRP00001-police-p2p
**Thief export:** https://github.com/JCS1029/GRP00001-thief-p2p
**Annotated tag (both exports):** `v1.0-submission`

## Per-member checklist

| Step | Owner | Status |
|---|---|---|
| Confirm GitHub access to both role repositories | every member | operator |
| Confirm lecturer can open both repositories and the annotated tag | Release Lead | EXTERNAL |
| Clone Police export, `uv sync --frozen --all-groups`, readiness OK | every member | operator |
| Clone Thief export, `uv sync --frozen --all-groups`, readiness OK | every member | operator |
| Attach both repository URLs and group ID on the Moodle form | every member | EXTERNAL |
| Export Moodle form to PDF without moving template fields | Release Lead | EXTERNAL |
| Visually compare Moodle PDF layout to the provided template | Release Lead | EXTERNAL |
| Include screenshots: belief heatmap + replay Verified OK | every member | in-repo SVGs |
| Include result JSON links (tuning, selection, language, rehearsal) | every member | in-repo |
| Confirm no secrets in either repository history | Release Lead | tooling |

## In-repo evidence already present

- Live belief heatmap: `docs/screenshots/m10_live_local_view.svg`
- Replay Verified OK: `docs/screenshots/m10_replay_verified.svg`
- Replay TAMPERED contrast: `docs/screenshots/m10_replay_tampered.svg`
- M12 campaigns: `results/benchmarks/m12_*.json`
- Two-machine public tunnels: `results/benchmarks/two_machine_playtest.json`
- Full audit map: `docs/evidence/SUBMISSION_AUDIT.md`
- Exit notes: `docs/evidence/M12_EXIT.md`, `docs/evidence/M13_EXIT.md`

## Moodle form

No Moodle form template is checked into this repository. Filling the official
course form, exporting PDF, and layout comparison are **EXTERNAL** operator
actions. Do not invent a substitute form.
