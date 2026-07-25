# Mechanism PRD - Commit-Reveal, Declarations, and Mutual Audit

**Status:** M5 approved and frozen
**Owner:** Security Lead
**Requirements:** FR-CRY-001..015, FR-GAME-013, FR-NEG-007..010
**Rules:** Appendix E 15-24, 36, 46-48, 53; ADR-004

## Purpose and scope

Bind every outcome-relevant decision and declaration before the opponent reveals dependent information, keep nonces secret during play, and independently reconstruct legality/scoring at final audit without a central judge.

## Inputs

- versioned canonical payload schema;
- game/sub-game/step/role identity and pre-action local-state digest;
- action, hint, sealed truth/lie verdict, public barrier effects;
- token/model metadata;
- fresh >=128-bit nonce from OS CSPRNG;
- config, scent, Step-0, schedule, journal, and result artifacts.

## Outputs

- lowercase SHA-256 commitment digest and public envelope;
- post-ack reveal that excludes nonce;
- final nonce/reveal manifest;
- structured deterministic audit report/findings;
- mutual audit/result agreement digest;
- immutable verified or tampered terminal status.

## Canonical byte contract

UTF-8, Unicode NFC, lexicographically sorted object keys, no insignificant whitespace, separators `,`/`:`, schema-defined array order and number representation, finite values only, explicit schema version, and nonce as a payload field. Exact golden bytes/digests are shared by both exports.

The normative commitment body is `commitment_version`, game UUID, sub-game,
actor-local step, actor, pre-action local-state digest, action, hint, verdict,
public effects, token count, model/provider, config digest, protocol version,
scent-model digest, and scent-frame digest. The canonical commitment payload adds
one lowercase nonce field. `data/conformance/crypto/commitment.v1.json` fixes the
exact bytes and SHA-256 result.

## Nonce and lifecycle contract

- A nonce is at least 16 bytes and production generation calls
  `secrets.token_bytes`; reuse is prohibited across the sealed store.
- `SecretNonce` is opaque and its string/repr are permanently redacted.
- Commit stores the secret payload locally and sends identity plus digest only.
- A matching acknowledgement locks the payload. A live reveal then exposes the
  complete body but no nonce.
- Only `AUDITING`, `AGREEING_RESULT`, `REPORTING`, or `COMPLETED` can create the
  final manifest of commitment-linked nonces.
- All digest and keyed-signature checks use constant-time comparison.

## Step-0 keyed signature

Each peer signs exact canonical Step-0 bytes using HMAC-SHA-256 and the
course-provided shared secret. The key is loaded from a named secret environment
entry or an already-open binary file handle, is never accepted as a path/value in
public configuration, and never serializes. Counted play requires a known clean
40-character Git commit. Template mode declares zero operational tokens.

Step-0 binds group, counted/template terms, model/provider/tokens, normalized
OS/platform/runtime, CPU/core/frequency, RAM, optional GPU/VRAM, Git status, exact
config/scent/schedule digests, and protocol/schema versions. The golden body/HMAC
is `data/conformance/crypto/step_zero.v1.json`.

## Invariants

1. Every commitment uses a unique fresh secret nonce.
2. Pre-ack payload cannot mutate; reveal occurs only after the required lock.
3. Live reveal omits nonce; final audit reveal is phase-gated.
4. Hash comparison is constant-time.
5. Same semantic payload produces identical bytes/digest across supported systems.
6. Audit first verifies constitution/declaration/schedule, then identities/order/completeness, commitments, physics/scent, terminal/scoring, artifact linkage, and result agreement.
7. A valid hash never excuses an illegal action.
8. One mismatch produces a deterministic tamper finding and stops normal scoring.
9. Audit is pure over evidence and can run through SDK/replay without network/GUI.
10. Raw secrets/nonces never enter operational logs.

## Audit order

1. Validate artifact schemas, versions, sizes, paths, and digests.
2. Verify shared config, scent model/example, role schedule, repositories/commits, and Step-0.
3. Verify journal chain, unique monotonic identities, actor/phase completeness.
4. Recompute every commitment with final nonce.
5. Replay actions through deterministic physics and recompute scent.
6. Verify capture claims/answers and terminal order.
7. Recompute sub-game and series scoring/tokens.
8. Compare peer audit manifests and final result agreement.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| CRY-AC-001 | Golden payloads yield identical bytes/hashes in both role exports/platforms. | cross-platform vectors |
| CRY-AC-002 | Each payload field mutation, nonce change, reorder, deletion, truncation, substitution is detected. | mutation suite |
| CRY-AC-003 | Nonce never appears in repr, exception, log, MCP live reveal, screenshot, or LLM prompt. | secret-leak tests |
| CRY-AC-004 | Commit/reveal/ack/final-reveal illegal orders fail without mutation. | phase matrix |
| CRY-AC-005 | False capture claim/denial and forged scent/score fail audit. | adversarial corpus |
| CRY-AC-006 | Valid complete logs independently return identical `Verified OK` report. | dual-peer integration |
| CRY-AC-007 | Corrupt/foreign/oversized/path-escaping artifacts fail closed and remain preserved. | security/fault tests |
| CRY-AC-008 | Audit report localizes first failure and deterministically orders all findings. | snapshot tests |

## Failure taxonomy and sanction

Findings are ordered as constitution/config, scent model, schedule, Step-0,
journal, final manifest, global/actor sequence, foreign identity, nonce,
commitment, step binding, pre-state, scent frame, domain legality, public effect,
post-terminal record, terminal, score, and capture truth. Each finding has an
order, stable code, evidence link, and safe detail. Unsafe replay stops at the
first physical mismatch; independent preflight failures are aggregated in stable
order.

Any integrity mismatch returns immutable `TAMPERED`, terminal reason `tamper`,
and zero Police/Thief points. A valid digest never legalizes an invalid action.
Only two byte-identical independent audit reports over one manifest can produce a
final result-agreement digest and unlock reporting.

## Approval

Approved by the Security Lead role on 2026-07-25. Exact schemas, canonical
encoding, nonce lifecycle, Step-0 signature, journal chain, failure taxonomy,
sanction, artifact graph, conformance vectors, and localhost mutual-audit exit
evidence are frozen for protocol `0.5.0`.
