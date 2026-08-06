# M9 Artifact and Reporting Exit Review

- **Milestone:** M9 artifacts, Gmail reporting, and full Gatekeeper
- **Package / protocol / schema:** `0.8.0` / `0.7.0` / `0.2.0`
- **Date:** 2026-07-26
- **Branch:** `main`
- **Review status:** `PENDING EXTERNAL EVIDENCE`
- **Remaining gate:** T469 controlled real OAuth/send to a team-controlled safe recipient

## Candidate quality results

| Control | Result |
|---|---|
| Ruff formatting and lint | Pass |
| Strict mypy | Pass |
| Repository validators | Pass |
| M9 focused campaign | Pass: 24 artifact/reporting/Gatekeeper tests |
| Full test campaign | Pass: 427 tests in 209.44 seconds |
| Branch-aware coverage | Pass: 89.40% (85% required) |
| Python source size | Pass: no file over 150 code lines |
| Real Gmail provider rehearsal | Not run: no team OAuth credentials or safe test recipient were provided |

No OAuth credential/token file exists in the repository. The implementation and
automated evidence are complete, but the review does not invent or substitute a
fake-provider receipt for T469.

## Artifact review

The candidate emits one series declaration, six exact played-config artifacts,
six finalized sealed logs, one final result, and one manifest using confined
Appendix F filenames. Model plus Draft 2020-12 schema validation precedes
flush/fsync/atomic replacement. Official files are immutable and separated from
private pre-audit evidence and rotating diagnostics.

The manifest binds exact byte size/digest, schema, game ID/UID, sub-game, config,
played commit, journal, audit, declaration, role assignment, and result links.
Verification requires the complete 14-document series graph before replay,
archive, or reporting. Archive export scans verified documents for credential,
OAuth, API-key, token, and private-TOML fields.

Final result validation independently recomputes all six score, win, tie,
winner, and per-group token totals. The report builder accepts only the opaque
verified-manifest proof and requires both participants to confirm the same
result-payload digest.

## Reporting and Gatekeeper review

The standard canonical JSON result is the sole authoritative attachment.
Deterministic MIME labels its body non-authoritative. Competition recipient
policy requires `rmisegal+uoh26finalgame@gmail.com`; OAuth scope must equal only
`https://www.googleapis.com/auth/gmail.send`. Installed-app PKCE first-run and
refresh persist an owner-only token outside artifact storage without logging
paths, codes, or values.

The atomic outbox persists `PENDING`, `VALIDATED`, `SENDING`, `RETRY_WAIT`,
`SENT`, and `FAILED_PERMANENT`. Restart converts an uncertain `SENDING` item to
`RETRY_WAIT`; logical report ID plus attachment digest prevents conflicting or
duplicate send. The Gmail adapter has no result-building imports or logic.

The central Gatekeeper loads MCP, Gmail, and remote-LLM profiles from JSON. It
applies continuous monotonic token buckets, durable UTC-day/named-session quotas,
priority/concurrency admission, bounded queues, timeouts, capped exponential
jitter, HTTP 429 guidance, burst/repetition/error anomaly detection, one
half-open probe, confirmed reset, and redacted resource/outcome metrics.

## Appendix E review

| Rule | Decision and evidence |
|---:|---|
| 28 | Pass: Gmail call is token-bucket protected through `FullGatekeeper`. |
| 29 | Pass: anomaly thresholds, bounded queue, circuit open/half-open/recovery tests. |
| 30 | Pass: exact send-only scope checks reject read/modify/full-mail scopes. |
| 31 | Deferred operational league evidence to M12; result/declaration models retain counted identity. |
| 32 | Pass in implementation: lifecycle has finalization/queue phases and dispatcher persists provider outcome. |
| 33 | Pass: canonical standard JSON final result is attached. |
| 34 | Pass: MIME body declares itself non-authoritative and cannot replace attachment. |
| 35 | Pass in implementation: mutual digest is mandatory and logical ID includes independent sender group. |
| 39 | Pass: repository scan and ignore controls contain no OAuth credentials/tokens. |
| 40 | Pass: nested credential/token, environment, key, certificate, and provider-cache patterns are ignored. |
| 51 | Pass: required competition recipient is a product constant and mandatory default allowlist member. |
| 54 | Pass: exact input/output tokens exist per step, sub-game, group, and series and are recomputed. |

## Sign-off

| Accountable role | Decision | Evidence reviewed |
|---|---|---|
| Artifact Lead | Approved | schemas, filenames, atomicity, linkage, tamper, archive |
| Reporting Lead | Approved implementation | result agreement, MIME, outbox, fake Gmail, dry run |
| Reliability Lead | Approved | quota, priority, backoff/429, anomaly, circuit, restart |
| Security Lead | Approved implementation | confinement, secret fields, OAuth scope/path/redaction |
| QA Lead | Approved automated candidate | focused/full tests, coverage, static/structural gates |
| Release Lead | Closed as operator-owned residual | `docs/evidence/FINAL_TODO_CLOSURE.md` |

T469 has no OAuth secrets in this workspace. The fake-provider/dry-run path remains
the evidenced path. A redacted real-provider receipt may still be appended later as
`docs/evidence/T469_REDACTED_RECEIPT.md` without reopening packaging. Never use the
lecturer address for that rehearsal.
