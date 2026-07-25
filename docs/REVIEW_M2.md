# M2 Contract Review

- **Review date:** 2026-07-25
- **Milestone:** M2 - Configuration and contracts
- **Current decision:** `READY`

## Appendix F completeness

- [x] F-001..F-032 are represented in the shared schema and example.
- [x] All 14 fixed parameters have one-field mutation rejection tests.
- [x] All 9 minimum parameters have weakening rejection and stricter acceptance tests.
- [x] All 9 negotiable parameters have exact typed defaults.
- [x] Gatekeeper request rate/concurrency use the security interpretation from AMB-008.
- [x] The six-sub-game fixed schedule and 200,000-token default are preserved.

## Contract and security checklist

- [x] JSON Schema Draft 2020-12 validates all packaged schemas.
- [x] Unknown shared/private fields fail closed.
- [x] Namespaced extensions remain canonicalizable.
- [x] Shared JSON rejects oversize, depth, invalid UTF-8, duplicate keys, NaN,
  infinity, malformed syntax, traversal-like IDs, and invalid cross-fields.
- [x] Private TOML reports source-aware safe errors and cannot hold shared rules.
- [x] Environment resolution is secret-only and redacted.
- [x] Submission identifiers are exactly eight ASCII alphanumeric characters.
- [x] Four origins and both start indexes round-trip through canonical coordinates.
- [x] Scent kernel, rounding, emission, and decay match golden vectors.
- [x] Canonical JSON is NFC, deterministic, float-free, and idempotent.
- [x] Raw-byte equality is distinct from canonical semantic equality.
- [x] Declaration, per-game config, log, result, and envelope schemas have positive
  and negative conformance fixtures.
- [x] SDK readiness reports schema/protocol compatibility.

## Verification evidence

- **Implementation candidate:** `916d3d4f2162343f3e22e656ad173b70325e67e5`
- **Clean-clone evidence:** `docs/evidence/M2_CLEAN_CLONE.txt`
- **Tests:** 147 passed with 95.65% branch-aware global coverage.
- **Critical contract coverage:** canonical JSON, identifiers, loader, config models,
  rule table, coordinate conversion, effective config, private config, and scent
  modules each report 100%.
- **Static/quality:** frozen sync, Ruff lint/format, strict mypy, import boundaries,
  structure, traceability, source-size, file hygiene, and secret scan passed.
- **Packaging:** source distribution and wheel built from the clean clone; the
  installed wheel located every packaged schema and returned SDK `READY`.
- **Independent contract method:** Draft 2020-12 independently validates each schema;
  table-driven tests enumerate every fixed/minimum/default rule; manifest-driven
  positive and negative fixtures verify every artifact schema.

## Sign-off

- **Reviewed by:** Codex contract review pass
- **Signed on:** 2026-07-25
- **Finding:** No omitted Appendix F row, unresolved P0 contract defect, secret, or
  milestone blocker remains.
