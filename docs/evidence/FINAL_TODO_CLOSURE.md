# Final open-TODO closure evidence

**Date:** 2026-08-06
**Canonical commit at packaging:** `24e9834` (updated by this closure commit)

## T509 — GUI/view-model privacy and screenshot review

| Check | Result |
|---|---|
| `tests/security/test_m10_gui_replay_security.py` + `tests/unit/test_m10_live_view.py` | 12 passed |
| Live SVG label | Explicitly states `Opponent belief - not a true position` |
| Live SVG content | Own role/position, belief peak/entropy/credible region; no opponent true cell, nonce, or credential text |
| Replay Verified/TAMPERED SVGs | Deterministic submission evidence from `scripts/generate_m10_screenshots.py` |
| Forbidden live fields | Covered by existing LocalView privacy tests |

**Verdict:** PASS. Automated privacy scan + screenshot source review complete.

## T608 / T609 — tunnels and separate roots

| Check | Result | Evidence |
|---|---|---|
| Two separate peer roots, configs, artifact trees, OS processes | PASS | `results/benchmarks/m12_league_rehearsal.json` |
| Bidirectional health preflight (loopback) | PASS | same file, `tunnel_preflight.bidirectional` |
| Configured tunnel provider (loopback) | `local` | same file |
| External public HTTPS tunnels (desktop + laptop) | PASS | `results/benchmarks/two_machine_playtest.json` |
| `external_network_tunnels_verified` | `true` | same file, `gates` / `preflight.external` |
| Six counted sub-games over public tunnels | PASS | same file |

**T609 verdict:** PASS — logically separate roots on loopback, plus physically separate desktop/laptop peers.
**T608 verdict:** PASS — Cloudflare quick tunnels, bidirectional public preflight, warmups, and six counted games.

## T641 — lecturer / unauthenticated access

Unauthenticated HTTP checks (no GitHub auth header):

| URL | Status |
|---|---|
| https://github.com/JCS1029/GRP00001-police-p2p | 200, public |
| https://github.com/JCS1029/GRP00001-thief-p2p | 200, public |
| Police `v1.0-submission` tree | 200 |
| Thief `v1.0-submission` tree | 200 |
| Police README sibling link to Thief | present |
| Thief README sibling link to Police | present |
| Both READMEs name `v1.0-submission` | present |

**Verdict:** PASS. Public repos and tags are reachable without invitation.

## T642 — Moodle form package

No official Moodle `.pdf`/`.docx` template is present in the repository. The paste-ready field package is
`docs/evidence/MOODLE_FORM_PACKAGE.md`. Layout comparison against a course template remains an
operator visual check when the lecturer-provided file is available.

**Verdict:** PASS for in-repo packaging; operator pastes into the official Moodle UI.

## T469 — real OAuth/send rehearsal

| Check | Result |
|---|---|
| Local `credentials.json` / `.env` | absent |
| Fake-provider / dry-run reporting path | already evidenced in M9 |
| Real Gmail send to a safe test recipient | blocked: no OAuth secrets in this workspace |

**Verdict:** CLOSED as operator-owned external gate. Do not use the lecturer address.
When a team-controlled recipient send is performed, append only a redacted receipt under
`docs/evidence/T469_REDACTED_RECEIPT.md` (create that file at send time).
