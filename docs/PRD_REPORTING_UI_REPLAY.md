# Mechanism PRD - Artifacts, Reporting, Live UI, and Replay

**Status:** M9 artifact/reporting and M10 UI/replay contracts finalized 2026-07-26
**Owners:** Artifact Lead, Reporting Lead, UX Lead
**Requirements:** FR-ART-001..013, FR-RPT-001..013, FR-UI-001..015
**Rules:** Appendix E 8-9, 20, 28-35, 39-44, 49-51, 54-55

## Purpose and scope

Define four linked artifact families, atomic event evidence, mutually agreed Gmail JSON reporting, live local-truth monitoring, and post-audit replay verification. All entry points call the SDK; Gmail calls pass through Gatekeeper.

## Inputs

- typed SDK local-view, status, replay, artifact, and reporting use cases;
- verified shared config, declaration, sub-game events/audits, final result agreement;
- artifact root, naming policy, schemas, and retention classification;
- local GUI accessibility preferences;
- send-only OAuth handle and allowlisted recipient;
- durable outbox and Gatekeeper policies.

## Outputs

- one declaration and result per series;
- one exact config and finalized log per sub-game;
- atomic, schema-valid, digest-linked artifact manifest;
- live GUI containing own truth, public state, belief heatmap, status and metrics only;
- replay with navigation and prominent `Verified OK`/`TAMPERED`;
- idempotent durable JSON report dispatch record.

## Artifact families

| Family | Cardinality | Core linkage |
|---|---:|---|
| Declaration | one per series/group | game UID, identities, repos/commits, Step-0, config/scent/schedule digests |
| Played config | one per sub-game | exact bytes/digest, role assignment, schema/version |
| Sub-game log | one per sub-game/group | ordered commitments/reveals/events/nonces-after-audit/findings |
| Final result | one per series/group | six outcomes/scores/tokens, totals, winner/tie, audit and agreement digests, report metadata |

## M9 frozen artifact contract

Official filenames are exactly:

- `declaration_<game_id>.json`;
- `config_<game_id>_g<NN>.json`;
- `log_<game_id>_g<NN>.json`;
- `result_<game_id>.json`;
- `manifest_<game_id>.json`.

`game_id` is a lowercase ASCII slug of at most 64 characters and `NN` is the
one-based two-digit sub-game number. A resolved path must be a direct child of
`<artifact_root>/official`; traversal, nested paths, Windows reserved names, and
names longer than 180 UTF-8 bytes fail closed. `<artifact_root>/private` contains
owner-only pre-audit evidence. `<artifact_root>/diagnostics` contains rotating,
non-authoritative operational data. Neither may substitute for an official file.

All official documents use schema family `0.2.0`, canonical NFC UTF-8 JSON, and
SHA-256. An exact supported schema version is required; a later version needs an
explicit reader/migration rule before acceptance. Writes validate the model and
JSON Schema before a sibling exclusive temporary file is flushed, fsynced,
atomically replaced, and made best-effort read-only. Rewriting an existing
official filename with different bytes is prohibited.

The manifest contains every official artifact filename, schema, exact byte size
and digest plus series config, played commits, journal head, and audit-manifest
links. Acceptance recomputes every digest and validates game ID/UID, sub-game,
role assignment, config, commit, declaration, log, journal, audit, and result
edges. A series requires one declaration, six config/log pairs, and one result.
Archive export includes only the verified graph and rejects credential, OAuth,
API-key, private-TOML, and token fields.

Live evidence remains append-only. Final log derivation copies contiguous event
records and enriches them only after terminal audit with commitment/reveal,
public effects, exact per-group input/output tokens, metrics, and audit status.
Source journal records are never mutated. Result acceptance independently
recomputes all six score/win/tie totals, series winner/tie, and per-sub-game plus
series token totals.

## M9 frozen reporting contract

Only a verified manifest may enter report construction. The authoritative
attachment is the canonical final-result JSON; the MIME body explicitly states
that it is informational. The attachment digest and logical report ID
(`game_uid` plus sender group) are fixed before outbox admission.

The result contains a mutual agreement over the result payload excluding only
the self-referential `agreed_digest` field. Both participant IDs must sign it.
Any disagreement blocks the production outbox.

The atomic outbox persists the entire collection as one bounded record. Its only
states and legal forward transitions are:

`PENDING -> VALIDATED -> SENDING -> SENT`

`SENDING -> RETRY_WAIT -> VALIDATED`

`SENDING -> FAILED_PERMANENT`

On restart, `SENDING` becomes `RETRY_WAIT` with a redacted interruption code.
`SENT` and `FAILED_PERMANENT` are terminal. Re-enqueueing identical bytes returns
the existing item; conflicting bytes under a logical ID fail closed.

Competition reporting permits only the configured allowlist, which must contain
`rmisegal+uoh26finalgame@gmail.com`. OAuth authority must equal only
`https://www.googleapis.com/auth/gmail.send`. Credential and token JSON are
separate private paths outside artifact storage. First run uses installed-app
PKCE with a loopback callback; refresh and token persistence never log secret
paths, codes, or values.

Every Gmail API call passes through the same provider-neutral Gatekeeper used for
MCP and optional remote LLM calls. Per-service JSON profiles own continuous
monotonic token buckets, durable UTC-day and named-session quotas, concurrency,
bounded priority queues, timeout, exponential jittered retry, HTTP 429 guidance,
burst/repetition/error anomaly limits, and closed/open/half-open circuit state.
Metrics expose only service, quota/tokens, queue/concurrency, retry/rejection
counts, and numeric circuit state.

`police-thief-p2p report validate` verifies the complete graph, result agreement,
token/score totals, attachment, and deterministic MIME without creating an
outbox item or contacting Gmail.

## M10 frozen live-view contract

The live adapter receives only an immutable SDK `LocalView`. Its explicit
allowlist is: own role/position/visited cells, public board geometry and
barriers, normalized opponent belief, credible region and uncertainty
diagnostics, natural-language hints, own verdict, sub-game/series progress,
barrier usage, latency/token/fallback metrics, audit text, and one typed status.
It cannot represent opponent true position, opponent track, nonce, objective
board, sibling private log, future reveal, credential, or replay-derived truth.
Construction rejects mismatched board/belief sizes, non-normalized belief,
out-of-bounds cells, unsafe status text, and forbidden serialized keys.

The Tk adapter owns layout only. Every lifecycle action calls the injected
`SimulationSdk`; the adapter imports no domain or service module. Gameplay and
snapshot production run outside the Tk event loop. A bounded, thread-safe
channel stores only immutable `LocalView` snapshots. Under backpressure it
coalesces intermediate visuals while retaining the newest final, terminal, or
error snapshot; protocol evidence never enters this channel.

The resizable board uses the signed origin corner and start index for row/column
labels. It renders own role/position, public barriers, own trail, a fixed
zero-to-one belief scale, numeric legend, peak/entropy/credible-region summary,
and no opponent marker. Ready, thinking, waiting, locked, paused, degraded,
terminal, and error states each have text, an icon token, and a contrast-checked
color. Controls have keyboard equivalents, deterministic focus order, scalable
text, a minimum usable size, safe confirmation for stop/restart/quit, and
redacted correlation-ID errors with no traceback.

## M10 frozen replay contract

Replay input is bounded NFC UTF-8 JSON. Model and JSON Schema validation,
identifier checks, exact byte digest, and manifest/config/log/commit/journal/
audit linkage happen before a frame is exposed. `SimulationSdk.verify_log` is
the only adapter entry point. The verifier recomputes every revealed
commitment, nonce uniqueness, actor sequence, pre-state digest, action,
barrier/public effect, scent frame, capture/terminal result, and fixed score.
Normal verification stops at the first invalid step and returns a deterministic
ordered finding without rendering later evidence.

Single-log mode exposes the selected local track plus belief and explicitly
marks a missing/frozen sibling track. Objective dual-log mode is unavailable
until both logs are final-reveal complete, audited `Verified OK`, and linked to
the same game, configuration, commits, journal, and audit graph. Unequal valid
tracks retain their last known frame with a text banner rather than inventing
movement.

Replay navigation is immutable and supports play, pause, previous, next,
restart, go-to-step, and selection across sub-games 1-6. Integrity is always
shown as `✓ Verified OK` or `⚠ TAMPERED` using text, icon, color, and an
accessible description. Export produces canonical machine-readable JSON and a
standalone escaped UTF-8 HTML report. Deterministic SVG screenshots are derived
from reviewed fixtures and scanned for forbidden live fields and secrets.

## Invariants

1. Artifact IDs/filenames are sanitized, unique, and confined under the configured root.
2. Writes are atomic; live journal is append-only; finalization is immutable.
3. Schema/version/digest/link validation precedes replay or send.
4. Operational logs never substitute for protocol evidence.
5. Live UI/retrieval receives local-view DTOs with no opponent truth.
6. UI is observational/lifecycle-only and cannot bypass SDK/state machine.
7. Headless mode retains full game capability.
8. Objective replay is unlocked only after final reveal and link/audit validation.
9. Report is an attached standard JSON to the allowlisted address; body cannot replace it.
10. Each group independently sends the same agreed logical result exactly once, with recoverable durable retry.
11. Color is never the sole critical-state channel; keyboard/text alternatives exist.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| RUR-AC-001 | Crash during each write leaves prior valid artifact or recoverable temp, never partial accepted JSON. | M9 atomic/outbox recovery tests |
| RUR-AC-002 | Traversal, collision, wrong UID/digest/version, corrupt/truncated/oversized artifacts fail closed. | M9 artifact security tests |
| RUR-AC-003 | Live GUI/log/prompt/screenshot contains no opponent truth or pre-audit nonce. | privacy tests |
| RUR-AC-004 | Headless and GUI runs produce the same domain/protocol evidence for same inputs. | differential test |
| RUR-AC-005 | Replay navigation never bypasses verification and clearly reports tamper. | UI/integration test |
| RUR-AC-006 | Gmail scope/destination/attachment are exact; free-text substitute and arbitrary recipient fail. | M9 Gmail/report contract tests |
| RUR-AC-007 | Restart/429/timeout/retry preserves one logical report with visible pending/failed state. | M9 fake-Gmail/outbox fault tests |
| RUR-AC-008 | Keyboard, contrast, scaling, text alternatives, status, errors, confirmation and recovery pass review. | SCREENSHOT/MANUAL |

## Finalization checklist

- [x] four JSON schemas, filenames, atomicity and digest graph;
- [x] journal/finalization permissions and retention;
- [x] OAuth/outbox/idempotency/allowlist contract;
- [x] Gatekeeper profiles, retry classification, quotas, anomaly and telemetry;
- [x] standard report JSON, exact token accounting, MIME, and dry run;
- [x] live-view DTO and complete forbidden-field list;
- [x] GUI screens, states, threading, error/recovery and accessibility specification;
- [x] replay verification/navigation state machine;
- [x] screenshot and deterministic sample-run procedure.
