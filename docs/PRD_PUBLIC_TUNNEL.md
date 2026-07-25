# Mechanism PRD - Public Tunnel, Gatekeeper, and Remote Operations

**Status:** M0 approved outline; finalize before M5/M9/M12 remote implementation
**Owner:** Operations Lead with Security Lead
**Requirements:** FR-MCP-002, FR-MCP-010..015, FR-RPT-006..009, NFR-SEC-001..009
**Parameters:** F-026..F-032

## Purpose and scope

Define safe exposure and use of public MCP/health endpoints through a tunnel, central outbound Gatekeeper controls, preflight, degradation, circuit behavior, and the two-machine league runbook.

## Inputs

- local bind address/port and public tunnel URL;
- expected peer identity/capabilities;
- per-service rate, concurrency, queue, retry, timeout, size, and circuit profiles;
- typed outbound operation carrying stable idempotency identity;
- health/readiness and observability signals.

## Outputs

- redacted readiness report;
- bounded queued request or typed overload/deadline/circuit result;
- metrics for attempts, latency, retries, queue, concurrency, bytes, circuit, and outcome;
- remote preflight evidence;
- safe degraded/terminal recommendation to the Orchestrator.

## Invariants

1. Only MCP and minimal health/readiness surfaces are public.
2. No URL contains credentials; tunnel secrets never enter logs/artifacts.
3. Every external API request goes through Gatekeeper.
4. Limits are loaded from config and interpreted as minimum protection.
5. Queue, concurrency, body, response, retry, deadline, and error amplification are bounded.
6. Retries use stable request bytes/idempotency and exponential backoff with jitter.
7. Provider 429/retry guidance is honored without immediate loops.
8. Circuit opening does not mutate game outcome by itself; Orchestrator owns typed progression.
9. Readiness distinguishes liveness from ability to accept a counted match.
10. A counted match cannot start until bidirectional external preflight passes.

## Gatekeeper pipeline

`validate operation -> destination/service policy -> quota/rate -> bounded queue -> concurrency permit -> deadline -> call -> classify -> retry/backoff -> metrics/redaction -> release permit`

Fairness, cancellation, overflow strategy, half-open circuit probes, and service-specific policies are finalized before implementation.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| TUN-AC-001 | Requests outside Gatekeeper are rejected by architecture tests. | TEST |
| TUN-AC-002 | Token bucket, queue, semaphore, retries, timeout, circuit and cancellation obey fake-clock vectors. | TEST |
| TUN-AC-003 | Flood, slow body, oversized data, 429/5xx, disconnect and recovery remain bounded. | chaos/security tests |
| TUN-AC-004 | Logs redact tunnel/auth data and remote errors reveal no stack/private state. | leakage tests |
| TUN-AC-005 | Two external networks prove bidirectional health/capability calls before rehearsal. | EXTERNAL |
| TUN-AC-006 | Full six-game two-machine tunnel run meets >=98% controlled-fault completion target. | BENCHMARK/ARTIFACT |
| TUN-AC-007 | Startup order and reconnect do not duplicate effects. | integration tests |
| TUN-AC-008 | Config changes cannot make minimum protection weaker. | validator tests |

## Finalization checklist

- chosen tunnel provider-neutral contract and local bind rules;
- endpoint/auth/TLS exposure model;
- service policy schema and minimum-protection comparisons;
- queue fairness/overflow and circuit thresholds;
- health/readiness payload privacy;
- preflight, incident, endpoint-change, and rollback runbooks.

