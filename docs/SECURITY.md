# Security and Privacy Plan

**Baseline:** `0.10.0`
**Scope:** initial threat model for live peers, public MCP, tunnels, configuration, artifacts, Commit-Reveal, GUI/replay, optional LLMs, Gmail, repository, and release pipeline.

## 1. Assets and security objectives

| Asset | Confidentiality | Integrity | Availability |
|---|---|---|---|
| Pre-audit nonce and own private state | Critical | Critical | High |
| Shared constitution and protocol schemas | Public after agreement | Critical | Critical |
| Commitments, actions, barriers, capture answers | Phase-limited | Critical | Critical |
| Operational journal and official artifacts | Local-private then post-audit | Critical | High |
| Counted-match ledger and final result | Shared-signed | Critical | High |
| OAuth credentials/tokens | Critical | Critical | Medium |
| Repository source, lockfile, release tag | Public/reviewer-accessible | Critical | High |
| Strategy model/config and experiment holdout | Local-private | High | Medium |

Primary objectives: prevent hidden-state disclosure, forged or replayed effects, commitment substitution, false outcomes, secret leakage, path escape, denial-of-service amplification, and unauditable recovery.

## 2. Actors

- honest local peer and operator;
- buggy or incompatible peer;
- malicious opponent peer;
- unauthenticated internet client/scanner;
- compromised dependency or developer workstation;
- accidental committer/reviewer;
- optional LLM/email/tunnel provider;
- authorized lecturer/auditor.

No remote peer or provider is trusted merely because negotiation began.

## 3. Trust boundaries

| Boundary | Untrusted input | Mandatory controls |
|---|---|---|
| Internet/tunnel -> MCP server | headers, body, tool name, identity, timing, connection pattern | endpoint allowlist, TLS/tunnel controls, size/depth limits, schema, identity/game/phase/sequence checks, rate/concurrency/queue limits, deadlines, redaction |
| MCP client -> opponent | retry timing and duplicate uncertainty | Gatekeeper, stable idempotency identity, bounded retry/jitter, response schema, circuit breaker |
| JSON/TOML/artifact -> SDK | paths, keys, values, versions, digests | confined path resolution, strict schema, unknown-key policy, finite numbers, canonicalization, digest/link validation |
| Adapter/UI -> SDK | lifecycle commands and file selections | typed APIs, authorization by phase, no direct service access, confirmation for terminal actions |
| Strategy/LLM -> engine | malformed or illegal action, prompt leakage, latency | minimal local-view prompt, strict parser, deadline, token cap, legal-action guard, deterministic fallback |
| SDK -> filesystem | crash, partial write, symlink/path traversal | configured root confinement, atomic write, append journal, permissions, fsync policy, immutable finalize |
| Reporter -> Gmail | token theft, recipient injection, quota failure | send-only scope, local protected token, destination allowlist, Gatekeeper, durable idempotent outbox |
| Developer -> Git/release | secret commit, drift, dependency compromise | ignore patterns, secret scan, dependency audit, reviewed deterministic export, signed/annotated release evidence |

## 4. STRIDE coverage

| ID | Boundary / threat | STRIDE | Control | Verification | Residual treatment |
|---|---|---|---|---|---|
| THR-001 | Attacker claims another group/role/game. | Spoofing | signed negotiation identities, envelope checks, pinned session identity | negative identity matrix | terminal reject; incident evidence |
| THR-002 | Message or config changes in transit/storage. | Tampering | SHA-256 digests, canonical bytes, artifact links, final mutual audit | golden/mutation tests | tamper forfeit |
| THR-003 | Sender denies move/result or supplies conflicting duplicate. | Repudiation | append-only envelopes, message IDs, persisted responses, mutual result digest | duplicate/conflict tests | preserve both claims |
| THR-004 | Opponent truth, nonce, token, or secret leaks in payload/log/UI/prompt/error. | Information disclosure | local DTO allowlist, phase gates, redaction, prompt minimization, secret scan | privacy corpus and log scan | revoke/rotate; stop affected match |
| THR-005 | Flood, oversized JSON, slow request, retry storm, queue exhaustion. | Denial of service | Gatekeeper token bucket, semaphore, bounded queue/body/depth, deadlines, backpressure, circuit | load/slowloris/fuzz tests | degrade/technical terminal |
| THR-006 | Adapter or extension bypasses SDK/state machine. | Elevation of privilege | SDK-only boundary, import rules, typed ports, capability negotiation | architecture tests | release block |
| THR-007 | Path traversal/symlink writes outside artifact root. | Tampering/Elevation | sanitized IDs, resolved-path containment, no arbitrary remote paths | traversal/symlink tests | reject and alert |
| THR-008 | Replayed commit/action duplicates an effect. | Spoofing/Tampering | sequence+phase+message+digest identity, atomic idempotency store | loss-after-apply tests | prior response or tamper |
| THR-009 | Weak/reused/premature nonce breaks concealment. | Information disclosure/Tampering | OS CSPRNG, >=128 bits, per-commit uniqueness, delayed reveal | randomness interface and log tests | tamper/security incident |
| THR-010 | False capture claim/answer manipulates score. | Tampering/Repudiation | sealed answers, deterministic audit replay | exhaustive capture vectors | tamper forfeit |
| THR-011 | Malicious artifact consumes resources or bypasses validation. | DoS/Tampering | size/depth/schema/version/digest checks before replay/send | fuzz and corrupt corpus | quarantine artifact |
| THR-012 | Gmail token or arbitrary recipient abused. | Spoofing/Disclosure | send-only OAuth, protected local file, allowlisted destination, no log token | scope/recipient/secret tests | revoke and rotate |
| THR-013 | Dependency/reference code introduces backdoor or incompatible behavior. | Elevation/Tampering | lockfile, audit, provenance, minimal reuse, code review | dependency/license/secret audit | pin/remove/update |
| THR-014 | Holdout leakage or fabricated results corrupts competitive evidence. | Tampering/Repudiation | sealed split manifests, immutable raw outputs, one-shot holdout, commit/config linkage | experiment audit | invalidate run |
| THR-015 | Recovery invents progress after crash. | Tampering/Repudiation | mutually acknowledged durable checkpoints only | crash-boundary matrix | typed technical outcome |

All remote boundaries have Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation considerations represented either directly or through the shared controls above.

## 5. Security requirements for implementation

- Parse remote input into strict DTOs before accessing domain code.
- Reject unknown protocol fields unless a negotiated extension namespace/version allows them.
- Bound request bytes, JSON depth/container counts, strings, arrays, batch sizes, queue length, retries, response size, and diagnostic amplification.
- Use `secrets` or injected OS CSPRNG only; never seeded experiment RNG for nonces.
- Never log raw authorization headers, OAuth files, environment values, tunnel tokens, private keys, pre-audit nonces, opponent truth, or unrestricted prompts.
- Use allowlisted, structured logs and error codes.
- Resolve user/game-derived paths under configured roots and verify containment after normalization; handle symlinks defensively.
- Keep live and replay packages/data flows separate.
- Live GUI serialization uses an explicit immutable allowlist and recursively
  rejects opponent truth, objective-board, nonce, future-reveal, credential,
  key, and provider-token fields.
- Objective replay types unlock only after final nonces, both audits, and
  manifest/config/commit/journal/audit linkage verify. Single-log mode cannot
  represent the sibling true track.
- Replay JSON is bounded, strict UTF-8, duplicate-free, depth-limited, schema
  validated, and commitment/domain replayed before any frame is rendered.
- Escape every replay finding in HTML and scan deterministic SVG fixtures for
  truth/secret field leakage.
- Scan repository history and release archives for secrets, not only the working tree.
- Run dependency and license review before each release.

## 6. Incident handling

1. Stop the affected external operation without deleting evidence.
2. Enter a safe immutable or degraded state according to protocol.
3. Preserve redacted logs, request identity, artifact digests, version, and timeline.
4. Classify as invalid input, technical loss, tamper forfeit, security incident, or project blocker.
5. Revoke/rotate exposed tokens or keys immediately.
6. Patch canonical source, add a regression test, update threat/risk/ADR/changelog, regenerate both releases.
7. Resume counted play only after Security and QA close the gate.

## 6.1 Secret rotation

Treat any credential-pattern finding, unredacted provider response, accidental
OAuth-file inclusion, or suspicious account activity as exposure. Stop outbound
calls, preserve only redacted evidence, revoke the Gmail token in the provider
console, rotate the OAuth client secret/tunnel token as applicable, delete local
cached credentials after evidence capture, re-authorize with exactly
`gmail.send`, and rerun working-tree, all-ref history, artifact, and built-archive
scans. Never rewrite shared Git history without coordinated repository-owner
approval; revoke first because history rewriting cannot un-expose a secret.

## 6.2 Residual risks

- Windows without Developer Mode may not permit unprivileged symlink creation;
  containment logic remains active and the CI macOS job exercises the supported
  filesystem path.
- Public tunnels, Gmail, and optional model providers remain external
  availability dependencies. Failures are bounded, typed, durable, and do not
  authorize fabricated progress.
- SHA-256 commitments provide integrity/concealment through random nonces, not
  encryption or peer identity certificates. The signed Step-0 identity and final
  mutual audit remain mandatory.
- The current unified repository is the canonical source for both M13 role
  exports. Export drift remains a final-release gate until those repositories
  are generated and cross-compared.

## 7. Review status

M9 verifies the artifact path/digest boundary and Gmail controls with automated
traversal, corruption, scope, recipient, OAuth, fake-provider, quota, queue,
retry, anomaly, circuit, restart, and duplicate-dispatch tests. OAuth files
remain local-only and are never test fixtures. The controlled real-provider
rehearsal is external evidence and must be completed with a team-controlled safe
recipient before final M9 approval. No documentation statement substitutes for
that receipt.

M10 adds automated forbidden-field reflection and recursive runtime scans,
schema/resource/linkage mutation tests, full commitment-body mutation, safe GUI
error tests, fixed WCAG contrast assertions, deterministic screenshot byte
checks, and replay HTML injection tests. The in-app browser policy blocks local
`file://` rendering, so exit evidence distinguishes automated/source inspection
from the remaining human visual confirmation instead of bypassing that control.

M11 adds the complete transition/tool phase matrices, every outbound-tool
response-loss retry, every persistence/ack crash boundary, worker-family
watchdog freezes, bounded session/signature stores, hostile Unicode/bidi/null/
separator inputs, log/prompt injection, path/symlink/archive escape, tunnel and
dynamic-import restrictions, and a full working-tree/all-ref/archive secret
audit. The frozen dependency audit reports zero known vulnerabilities; all 98
locked package licenses are compatible after explicit primary-source review of
platform-only metadata. The cryptographic design review records no open P0/P1
finding.

## M13 residual risks

- Role exports must regenerate from the canonical commit after any patch; drift
  between sibling repositories is a release defect, not a local hotfix.
- The M12 repair holdout (`1.2.0`) cleared reliability and role gates (`R02-DEADLINE`
  zero misses; Thief survival `75%`). Earlier spent seals remain historical only.
- Lecturer access and Moodle form PDF layout remain EXTERNAL checks and are not
  implied by a green CI run. Public-tunnel two-machine rehearsal is evidenced in
  `results/benchmarks/two_machine_playtest.json`.
