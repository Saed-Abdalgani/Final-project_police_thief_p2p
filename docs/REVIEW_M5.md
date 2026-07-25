# M5 Cryptography and Mutual Audit Review

- **Review date:** 2026-07-25
- **Milestone:** M5 - Cryptography and mutual audit
- **Current decision:** `READY`

## Rule review

- [x] E-017..E-020 enforce fresh secret nonces, canonical commitments,
  acknowledgement locks, nonce-free live reveals, and terminal nonce release.
- [x] E-021/E-022 bind exact local pre-state, action, language verdict/evidence,
  public effects, model/tokens, constitution, protocol, and scent.
- [x] E-023/E-024 independently reconstruct every commitment and legal transition
  before accepting terminal/scoring truth.
- [x] E-036 binds exact clean played revisions and normalized Step-0 declarations.
- [x] E-046..E-048 recompute direct/barrier/enclosure capture and fixed scores.
- [x] E-053 maps any integrity mismatch to immutable `TAMPERED` with zero points.

## Security and architecture review

- [x] Production nonces come only from `secrets.token_bytes`, contain at least
  128 bits, reject reuse, and redact string/repr/log fields.
- [x] Commitment and Step-0 golden bytes/digests are frozen under
  `data/conformance/crypto/`.
- [x] Step-0 HMAC keys enter only through secret environment/file handles and
  never serialize.
- [x] CPU/RAM/runtime/Git and optional GPU probes degrade safely without a vendor
  SDK or hidden fallback value.
- [x] Capture claim/response messages bind the committed action/context and expose
  no position.
- [x] The local journal detects removal, reorder, modification, and coverage gaps.
- [x] `AuditService` is pure and imports no adapter, GUI, network, clock,
  persistence, or randomness dependency.
- [x] Preflight, commitment, state, scent, legality, effect, terminal, score,
  capture, manifest, and result checks have deterministic typed findings.
- [x] Every commitment field mutation, missing/duplicate/reordered/truncated/
  foreign record, forged scent, valid-hash illegal action, false capture,
  corrupt journal, nonce reuse, and peer disagreement fails closed.

## Verification evidence

- **Full suite:** 319 passed with 94.80% branch-aware global coverage.
- **Interop:** two independently rooted FastMCP processes passed A-first and
  B-first startup, transported the full commitment/reveal/final-manifest/report
  graph, and independently returned `Verified OK`.
- **Contracts:** commitment, nonce-free live reveal, final manifest, capture, and
  audit-report schemas passed Draft 2020-12 validation.
- **Golden values:** commitment SHA-256
  `c66e743102b1644d8d4b1e6a029c7eab8de235965d34e3cc56131d35eec5b716`;
  Step-0 canonical SHA-256
  `33581788aaaad599e4dd653de2a6c7236f14a13e920aaeb77a1b99f13457a1d7`.
- **Static/quality:** Ruff, strict mypy, structure, 150-code-line source policy,
  schema registry, import-boundary, and secret-redaction gates passed.

## Sign-off

Engineering review sign-off: Codex, 2026-07-25. The M5 exit gate and T216-T265
are satisfied with no unresolved P0/P1 finding.
