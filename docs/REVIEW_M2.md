# M2 Contract Review

- **Review date:** 2026-07-25
- **Milestone:** M2 - Configuration and contracts
- **Current decision:** `PENDING FINAL VERIFICATION`

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

## Verification gate

The decision becomes `READY` only after the frozen dependency sync, Ruff, format,
strict mypy, complete pytest/coverage, source-size, conformance, build, installed
wheel, secret scan, and Git hygiene checks all pass on the implementation candidate.
