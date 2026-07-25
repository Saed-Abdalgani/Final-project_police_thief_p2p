# Mechanism PRD - MCP Infrastructure, Negotiation, and Reliability

**Status:** M0 approved outline; finalize before M4/M8 implementation
**Owner:** Protocol Lead
**Requirements:** FR-NEG-001..012, FR-MCP-001..015, FR-ORC-001..013, NFR-REL-001..007
**Rules:** Appendix E 1-12, 31, 37-38, 52

## Purpose and scope

Specify two symmetric FastMCP peers, their versioned tools/envelopes, match negotiation, state-machine phases, idempotency, deadlines, startup independence, durable event ordering, recovery checkpoints, and Watchdog behavior.

Out of scope: strategy scoring, cryptographic payload internals, GUI layout, and Gmail-specific delivery.

## Inputs

- validated local identity/profile and shared constitution;
- remote public endpoint and capabilities;
- proposal/declaration/config/scent digests and played commits;
- typed SDK commands and local durable session state;
- rate/deadline/retry/queue configuration;
- injected monotonic clock and transport/storage ports.

## Outputs

- mutually agreed `game_id`, `game_uid`, versions, counted flag, and six-game role schedule;
- versioned protocol responses/errors;
- exactly-once application result for each idempotency identity;
- durable phase transitions and checkpoints;
- readiness/health state: alive, ready, degraded, or failed;
- typed technical/tamper evidence when progression cannot safely continue.

## Minimum MCP tool families

Health/capabilities, propose/accept negotiation, commit/acknowledge/reveal, capture claim/response, final nonce reveal, audit-manifest agreement, status, and final result agreement. Final tool names, versions, request/response schemas, auth/session preconditions, mutability, idempotency, and phase transitions are frozen in `docs/PROTOCOL.md`.

## Invariants

1. Each peer runs one server and one client in an independent process/root.
2. Inbound and outbound adapters call the SDK; no handler owns business logic.
3. Every request is bounded and validated for schema, session, identity, version, role, game, phase, sequence, message ID, correlation ID, and replay status.
4. Delivery may be at least once; application effects are exactly once per stable request identity/digest.
5. A repeated identity with different bytes is a violation, not a retry.
6. External waits use monotonic deadlines; queues/retries/buffers are bounded.
7. Terminal phases are immutable.
8. Recovery resumes only from mutually acknowledged durable checkpoints.
9. Startup order never changes semantics.
10. No remote error includes stack traces, secrets, opponent private state, or credential-bearing URLs.

## State outline

`INITIALIZING -> NEGOTIATING -> READY -> WAITING/COMPUTING -> COMMITTING -> AWAITING_ACK -> REVEALING -> VERIFYING -> ... -> AUDITING -> AGREEING_RESULT -> REPORTING -> COMPLETED`

Any state may enter an allowed typed technical/tamper/stopped terminal through explicit transitions. A full event/command transition table, timeout owner, persistence point, and retry rule is required before implementation.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| MCP-AC-001 | A-first and B-first separate processes negotiate and complete localhost play. | integration tests |
| MCP-AC-002 | Config, scent, version, identity, count, schedule, or commit mismatch fails before counted Step-0. | mismatch matrix |
| MCP-AC-003 | Loss after receiver mutation plus sender retry creates one effect and same response. | fault injection |
| MCP-AC-004 | Duplicate, stale, gap, future, reordered, malformed, oversized, and conflicting requests are bounded. | protocol property/fuzz tests |
| MCP-AC-005 | Crash at each persistence boundary resumes only when checkpoint agreement exists. | crash matrix |
| MCP-AC-006 | Watchdog detects frozen progress, persists redacted evidence, and never invents a winner. | fake-clock tests |
| MCP-AC-007 | Two peers have no shared writable state or direct IPC. | isolation audit |
| MCP-AC-008 | Public endpoint preflight proves bidirectional health/capability reachability. | external confirmation |

## Finalization checklist

- exact tool inventory and schemas;
- transition table and timeout/deadline ownership;
- atomic idempotency persistence algorithm;
- request/body/depth/string/queue/concurrency limits;
- reconnect and out-of-order policy;
- error-code catalog;
- public tunnel authentication/exposure assumptions;
- recovery snapshot fields and retention.

