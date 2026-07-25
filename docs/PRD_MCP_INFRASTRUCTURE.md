# Mechanism PRD - MCP Infrastructure, Negotiation, and Reliability

**Status:** M4 protocol/negotiation contract approved; M8 reliability expansion pending
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

The frozen `1.0.0` tools are `health_v1`, `capabilities_v1`,
`propose_match_v1`, `accept_match_v1`, `commit_step_v1`,
`acknowledge_step_v1`, `reveal_step_v1`, `capture_claim_v1`,
`capture_response_v1`, `final_reveal_v1`, `audit_result_v1`,
`agree_result_v1`, and `peer_status_v1`. Request/response ownership,
mutability, phase transitions, and M5 payload-extension boundaries are normative
in `docs/PROTOCOL.md`.

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

M4 implements `NEGOTIATING -> READY -> AWAITING_ACK -> REVEALING ->
WAITING/VERIFYING -> AUDITING -> AGREEING_RESULT -> REPORTING -> COMPLETED`.
`TECHNICAL`, `TAMPER`, and `STOPPED` are immutable terminal phases. M8 adds
orchestration-only `INITIALIZING`, `COMPUTING`, and recovery/watchdog states
without weakening the M4 tool preconditions.

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

## Approved M4 failure and persistence semantics

- JSON and envelope size/depth/string/collection limits are private typed
  configuration; inbound concurrency is the signed Gatekeeper ceiling.
- Inbound order is parse, session, identity, idempotency, phase/sequence,
  persist intent, SDK mutation, persist effect/response, acknowledge.
- Idempotency identity is game + sender + message UUID. Same digest replays;
  another digest conflicts. A durable session receipt repairs a pending record
  after restart.
- Out-of-order requests are rejected, never buffered. The configured reorder
  window distinguishes a normal gap from an abusive far-future sequence.
- Outbound FastMCP calls use a single monotonic deadline and bounded Gatekeeper
  retries with identical request bytes.
- Stable safe errors cover validation, unknown session, identity, phase,
  sequence, conflict, timeout, overload, and internal failure.
- Loopback HTTP is development-only. Public deployment requires
  credential-free HTTPS tunnel URLs and bidirectional preflight.
- Session and idempotency snapshots live only in the peer's private artifact
  root and are retained with official match evidence.

The exact field tables, examples, transition matrix, limits, recovery algorithm,
and interoperability commands are approved in `docs/PROTOCOL.md`.

## M4 approval

Approved by the Protocol Lead role on 2026-07-25 after contract, hostile-input,
restart, Gatekeeper, in-memory FastMCP, and dual-OS-process integration tests.
No M4 mechanism remains an outline. Watchdog, circuit breaker, authentication
hardening, and public-tunnel rehearsal remain explicitly owned by M8/M11/M12.
