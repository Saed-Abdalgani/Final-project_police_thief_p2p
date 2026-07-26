# M11 QA and Security Exit

**Candidate:** `0.10.0`  
**Review date:** 2026-07-26  
**Decision:** PASS  
**Severity gate:** no unresolved P0/P1 defect

## Objective evidence

- Complete module inventory and direct tests:
  `results/benchmarks/m11_module_inventory.json`.
- All 227 FR/NFR requirements, 55 Appendix E rules, and 32 Appendix F parameters:
  `results/benchmarks/m11_requirement_tests.json`.
- Adversarial, transition/tool phase, two-process, six-game, loss/retry,
  crash/recovery, watchdog, Gatekeeper, schema, artifact-corruption, and privacy
  suites execute under `tests/`.
- Continuous soak: 1,000 series / 6,000 sub-games, zero deadlocks, zero
  unbounded waits, and zero retained-object growth:
  `results/benchmarks/m11_soak.json`.
- Performance, MCP request/byte/retry, outbox outage, template-token, and
  profiler evidence: `results/benchmarks/m11_performance.json`.
- Six semantic mutation families: `results/benchmarks/m11_mutation.json`.
- Zero working-tree/history/archive secret findings:
  `results/benchmarks/m11_security_audit.json`.
- Zero known applicable locked-dependency vulnerabilities and compatible
  licenses for all 98 lock entries:
  `m11_vulnerabilities.json` and `m11_licenses.json`.
- Manual cryptographic decision: `docs/M11_CRYPTO_REVIEW.md`.
- Windows/macOS scope and limitation: `docs/M11_PLATFORM.md`.
- Full local regression: 521 passed, one capability-based symlink skip, 87.11%
  statement/branch coverage (85% gate).

## Independent role-based review

A separate QA/security review pass re-read the M11 acceptance criteria against
the generated evidence, inspected the security-sensitive diffs, reran the
focused and full gates, and checked that failures remain fail-closed. The review
found and required correction of two issues before approval: quadratic
articulation analysis/cold-start budget failures, and non-canonical fractional
outbox retry deadlines. Both have regression coverage and passing measurements.

The reviewer found no unresolved P0/P1 defect and approves M11 exit. External
Gmail/tunnel rehearsal, counted league play, role-repository export, tagging,
and submission remain M12/M13 gates and are not represented as completed here.

**Signed:** Codex QA/Security Review — 2026-07-26
