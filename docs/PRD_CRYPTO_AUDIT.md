# Mechanism PRD - Commit-Reveal, Declarations, and Mutual Audit

**Status:** M0 approved outline; finalize before M5 implementation
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

## Finalization checklist

- exact schemas and canonical number encoding;
- nonce type/storage/permissions/lifecycle;
- commitment payload field ownership and phase;
- Step-0 keyed-signature semantics;
- journal hash-chain format;
- audit failure taxonomy and sanctions;
- artifact/report digest graph and conformance vectors.

