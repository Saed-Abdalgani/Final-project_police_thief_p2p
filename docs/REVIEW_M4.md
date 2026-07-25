# M4 Peer Protocol Review

- **Review date:** 2026-07-25
- **Milestone:** M4 - Peer protocol and negotiation
- **Current decision:** `READY`

## Rule review

- [x] E-001..E-006 bind group identities, exact repositories/commits, public
  endpoints, shared constitution, and counted-match declarations before play.
- [x] E-010..E-012 preserve the signed role schedule and reject any shared
  configuration or stricter-minimum mismatch.
- [x] E-031 requires every peer mutation to cross an immutable versioned envelope.
- [x] E-037/E-038 enforce exact idempotency replay and monotonic sender order.
- [x] E-052 proves the two peers run as distinct processes with isolated roots.

## Architecture and quality review

- [x] The FastMCP server is a framing adapter over `SimulationSdk`; it contains no
  game or persistence logic.
- [x] Every outbound call crosses Gatekeeper and one monotonic deadline.
- [x] The frozen tool inventory, ownership, phase matrix, and error catalog are
  published in `docs/PROTOCOL.md`.
- [x] Hostile JSON is bounded by bytes, depth, strings, collections, and finite
  numeric representation before model parsing.
- [x] Sessions, mutation intents, effects, responses, and idempotency receipts are
  durably persisted before acknowledgement.
- [x] Duplicate delivery replays the exact response; digest conflicts and
  reordered/gapped sequences cannot mutate state.
- [x] Counted negotiation validates group ledgers, exact commits, four repository
  URLs, two credential-free MCP URLs, exact config bytes/digest, scent digest,
  versions, game UUID, and balanced six-game roles.
- [x] Startup succeeds in either peer order with different process IDs and
  separate config, artifact, cache, and temporary roots.

## Verification evidence

- **Tests:** 265 passed with 94.82% branch-aware global coverage on the M4
  candidate; focused protocol edge and negotiation additions also passed.
- **Interoperability:** real FastMCP streamable-HTTP peers passed both A-first and
  B-first startup campaigns and converged on one public sub-game outcome.
- **Failure campaign:** restart, crash boundary, duplicate, digest conflict,
  delayed/reordered/future sequence, deadline, overload, hostile payload,
  mismatch, redaction, and exception mapping cases passed.
- **Static/quality:** Ruff lint/format, strict mypy, structure/source-size checks,
  schema examples, adapter import boundaries, and secret-safe response snapshots
  passed.

## Sign-off

Engineering review sign-off: Codex, 2026-07-25. The M4 exit gate and T166-T215
are satisfied with no unresolved P0/P1 finding.
