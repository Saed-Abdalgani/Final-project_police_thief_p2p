# M10 Live GUI and Replay Exit Review

- **Milestone:** M10 live local-truth GUI and offline replay verifier
- **Package / protocol / schema:** `0.9.0` / `0.7.0` / `0.2.0`
- **Date:** 2026-07-26
- **Branch:** `main`
- **Review status:** `PENDING HUMAN VISUAL CONFIRMATION`
- **Remaining gate:** T509 human-rendered screenshot confirmation

## Candidate quality results

| Control | Result |
|---|---|
| M10 focused campaign | Pass: 43 live/replay/privacy/linkage tests |
| Strict M10 mypy and Ruff | Pass |
| Python source size | Pass: no file over 150 code lines |
| Full test campaign | Pass: 470 tests |
| Branch-aware coverage | Pass: 87.27% total; >=85% required |
| Deterministic screenshot generation | Pass: three byte-stable SVG fixtures |
| Forbidden-field screenshot scan | Pass |
| Human browser rendering review | Pending: local `file://` navigation blocked by in-app browser policy |

The implementation, automated privacy review, SVG source/geometry review, and
contrast checks are complete. The browser restriction was not bypassed. T509
remains open until a human opens the three checked-in SVGs and confirms no
clipping, overlap, or unexpected rendering on a supported desktop.

## Live-view and GUI review

`LocalView` is an immutable SDK DTO with an explicit field allowlist. It carries
own role/position/trail, public board/barriers, normalized opponent belief,
uncertainty summaries, hints, own verdict, progress, barrier usage, safe
latency/token/fallback metrics, typed lifecycle state, audit text, and optional
correlation ID. It cannot represent opponent true position/track, objective
board, nonce, future reveal, sibling private log, credentials, keys, or provider
tokens. Reflection and recursive serialized-key tests enforce that boundary.

The Tk adapter imports the SDK and no domain/service module. Its live board is
resizable, coordinate-origin/index aware, and renders own role marker, own
visited trail, public barriers, fixed-scale heatmap, numeric legend, posterior
peak, entropy, and credible-region summary. Ready, thinking, waiting, locked,
paused, degraded, terminal, and error use text, icon, and contrast-checked color.
Keyboard commands, deterministic focus, scalable text, minimum window size,
safe terminal confirmations, and redacted errors are present.

Gameplay workers run outside Tk. The bounded snapshot channel accepts only
`LocalView`, coalesces disposable intermediate visuals, and retains the newest
final/terminal/error snapshot. Protocol evidence never enters the UI queue.
Differential evidence proves snapshot observation does not mutate headless
domain state.

## Replay verifier review

`SimulationSdk.verify_log` is the only adapter replay boundary. It enforces byte
size, strict UTF-8 JSON, no duplicate keys/non-finite numbers/deep trees, JSON
Schema, exact identifiers, typed models, and log/config linkage before frame
construction. Full-manifest replay verifies the complete 14-document digest
graph before selecting a config/log pair.

Every revealed step checks global and actor order, game/sub-game/role identity,
nonce format/uniqueness, SHA-256 commitment, config/protocol/scent bindings,
pre-state digest, legal transition, barrier effect, scent frame, terminal truth,
and fixed score. Verification stops at the first invalid step and returns a
typed finding with zero replay points.

Single-log mode exposes local track plus belief and labels the absent sibling.
Objective truth cannot be requested from `verify_log`; it requires two final,
audited, linked logs through `verify_dual_log`. Unequal linked tracks get an
explicit frozen-track banner. Immutable cursors implement play, pause, previous,
next, restart, go-to-step, and six-sub-game selection. Exported JSON validates
against `replay_audit.schema.json`; standalone HTML escapes untrusted findings.

## Screenshot evidence

| Fixture | SHA-256 | Automated review |
|---|---|---|
| `m10_live_local_view.svg` | `fd8fb0c0bba0c958f9745c12ef0efbcbfe8fdbe78e0524ea4d87a5b28516b1fd` | local truth, belief legend, status, no forbidden key |
| `m10_replay_verified.svg` | `8a30448b586fcd16924d7d67b76607d947de33efd193000806d294099b6ee7a4` | icon/text/color `Verified OK` |
| `m10_replay_tampered.svg` | `03f60f18153561a516020522ea8b4d087784ea267725c479826cf521e811af61` | icon/text/color `TAMPERED`, first failure |

Regenerate with `uv run python scripts/generate_m10_screenshots.py`. Generated
bytes are deterministic and scanned for opponent-truth, nonce, credential, key,
and provider-token field names.

## Appendix E review

| Rule | Decision and evidence |
|---:|---|
| 8 | Pass: live GUI consumes only the immutable SDK local-view allowlist. |
| 9 | Pass: objective position fields do not exist in live types or screenshots. |
| 20 | Pass: schema/linkage/commitment/domain/score replay verifier and application shell exist. |
| Submission screenshots | Automated/source pass; human-rendered confirmation remains T509. |

## Sign-off

| Accountable role | Decision | Evidence reviewed |
|---|---|---|
| UX Lead | Approved implementation | layout, controls, status vocabulary, scaling, keyboard map |
| Replay Lead | Approved | schema/linkage, transitions, navigation, exports, mutation campaign |
| Security Lead | Approved automated evidence | local-truth DTO, adapter imports, scans, injection/resource tests |
| QA Lead | Approved automated candidate | 470 tests, 87.27% coverage, static/source-size gates |
| Release Lead | Hold M10 exit | T509 human-rendered screenshot confirmation is absent |

T510 records a completed signed review with a `HOLD`; it does not fabricate
T509. After a human opens all three SVGs at common desktop scaling, append the
reviewer/date/findings, check T509, and change this status to `APPROVED`.
