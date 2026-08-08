# Full submission audit (Moodle form + technical gates)

**Audit date:** 2026-08-07  
**Canonical commit audited:** `8a37571` (+ local GUI launcher / version sync in this follow-up)  
**Course form reviewed:** `uoh-rl07-final-project-2026.docx` (Moodle submission fields)

## 1. What that DOCX is

It is the **Moodle submission form**, not the full technical PRD. Examiners use it for
identity, repo URLs, emailed league results, and opponent rows. Technical proof still
lives in this repository (`docs/PRD.md`, `docs/TODO.md`, `results/benchmarks/`,
`docs/evidence/`).

## 2. Technical smoke (executed this audit)

| Check | Result | Notes |
|---|---|---|
| `git HEAD` == `origin/main` | PASS | `8a375719b3d4c72164b2c1b444ec3f2aaed58626` at audit start |
| `uv sync --frozen --all-groups` | PASS | |
| `police-thief-p2p readiness` | PASS | After version sync: package `0.11.0`, protocol `0.7.0`, schema `0.2.0` |
| Local playtest suite | PASS | dual-process, loopback league, screenshots |
| `m12_selection.json` | PASS | `holdout_passed` / `validation_passed` true |
| `two_machine_playtest.json` | PASS | `external: true` |
| `m12_league_rehearsal.json` | PASS | loopback; external flag false (expected; WAN covered separately) |
| `m12_tuning.json` / `m12_language.json` / `m12_studies.json` | PASS | present |
| Screenshots | PASS | `m10_live_local_view.svg`, `m10_replay_verified.svg`, `m10_replay_tampered.svg` |
| Tk GUI demo launch | PASS | `uv run python -m police_thief_p2p.adapters.gui --seconds 2` |
| Police repo + `v1.0-submission` | PASS | HTTP 200 |
| Thief repo + `v1.0-submission` | PASS | HTTP 200 |
| Canonical repo | PASS | HTTP 200 |

### GUI finding (fixed in this audit)

README previously pointed at `python -m …gui.live_app`, but that module had **no**
`__main__` and exited without opening a window. Fixed by adding
[`demo_shell.py`](../../src/police_thief_p2p/adapters/gui/demo_shell.py) and
[`adapters/gui/__main__.py`](../../src/police_thief_p2p/adapters/gui/__main__.py).

**Interactive GUI (you should see a Tk window):**

```powershell
uv run python -m police_thief_p2p.adapters.gui
```

Submission screenshots remain the deterministic SVGs under `docs/screenshots/`.

### Version finding (fixed in this audit)

`pyproject.toml` said `0.11.0` while `PACKAGE_VERSION` still said `0.10.0`.
Aligned to `0.11.0` in [`shared/version.py`](../../src/police_thief_p2p/shared/version.py).

## 3. Moodle DOCX field map

| Form field | Status | Value / action |
|---|---|---|
| Group ID (8 chars) | READY | `GRP00001` |
| Self-scoring recommendation | OPERATOR | Your judgment after real league scores exist |
| Cop repository URL | READY | https://github.com/JCS1029/GRP00001-police-p2p |
| Thief repository URL | READY | https://github.com/JCS1029/GRP00001-thief-p2p |
| AI Agent email that sent results to lecturer | BLOCKED | Needs real Gmail OAuth send (T469); dry-run only so far |
| Student 1/2 identity fields | OPERATOR | Fill names / IDs / Hebrew names yourselves |
| Legal number of games played and emailed | BLOCKED | Needs counted matches vs other groups + emailed reports |
| Maximum points accumulated | BLOCKED | From real opponent series |
| Games won / lost / drawn | BLOCKED | From real opponent series |
| Bonus eligibility | OPERATOR / BLOCKED | Depends on course bonus rules + real match ledger |
| Opponent table rows (date, times, opponent, scores, declared games, opponent email) | BLOCKED | Desktop↔laptop self-play does **not** fill this; need ≥2 different opponent teams |

Paste helpers: [`MOODLE_FORM_PACKAGE.md`](MOODLE_FORM_PACKAGE.md).

## 4. READY vs BLOCKED summary

### READY for examiner technical review

- Install, readiness, protocol dual-process
- Competitive holdout gates
- Loopback + two-machine public-tunnel dress rehearsal
- Public role repositories and `v1.0-submission` tags
- Research/exit docs and benchmark JSON evidence
- Deterministic GUI/replay screenshots + working live GUI demo launcher

### BLOCKED for a complete Moodle form

1. **Real Gmail send** of match results to the lecturer path (form “AI Agent email…”)
2. **Real counted matches against other groups** (form games/points/W-L-D + opponent table; PRD minimum two different opponents)
3. **Filled Moodle PDF** exported from the official form and visually compared to the template

### Not blockers for “software works”

- Opening Cloudflare URLs in a browser (404 on `/` is expected; `/mcp` is the API)
- Live GUI during headless playtests (optional viewer; now launchable)

## 5. Recommended operator next steps

1. Run `uv run python -m police_thief_p2p.adapters.gui` once and keep a screenshot if Moodle wants a live capture beyond the SVG.
2. Configure Gmail OAuth privately; dry-run then send one safe test report; then lecturer path.
3. Schedule ≥2 opponent teams; play counted six-sub-game series; record the DOCX table from artifacts/emails.
4. Paste [`MOODLE_FORM_PACKAGE.md`](MOODLE_FORM_PACKAGE.md) into the DOCX/Moodle UI; export PDF; compare layout.

**Audit verdict:** technically **READY**; Moodle form completeness **CONDITIONALLY READY / BLOCKED** on Gmail + external opponents.
