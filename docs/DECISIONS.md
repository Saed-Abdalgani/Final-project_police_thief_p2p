# Architecture Decision Register

**Baseline:** `1.0.0`
**Status vocabulary:** Proposed, Accepted, Superseded, Rejected.

## 1. Index

| ADR | Decision | Status | Date | Owners |
|---|---|---|---|---|
| ADR-001 | SDK-only access to business logic | Accepted | 2026-07-25 | Architecture, QA |
| ADR-002 | Ports-and-adapters architecture | Accepted | 2026-07-25 | Architecture |
| ADR-003 | Canonical workspace exporting two standalone role repositories | Accepted | 2026-07-25 | Architecture, Release |
| ADR-004 | Canonical JSON and SHA-256 commitment bytes | Accepted | 2026-07-25 | Protocol, Security |
| ADR-005 | At-least-once delivery with exactly-once application effects | Accepted | 2026-07-25 | Protocol, Reliability |
| ADR-006 | Reject out-of-order requests without buffering | Accepted | 2026-07-25 | Protocol, Security |
| ADR-007 | HMAC-SHA-256 for course-key Step-0 declarations | Accepted | 2026-07-25 | Security, Protocol |
| ADR-014 | Exact scent decimals and boundary-only quantization | Accepted | 2026-07-25 | Belief, Protocol |

## 2. ADR template

```text
## ADR-NNN - Title
Status:
Date:
Owners:
Requirement links:
Source links:

### Context
### Decision drivers
### Options considered
### Decision
### Consequences
### Security and privacy impact
### Verification
### Rollback / supersession
```

## ADR-001 - SDK-only access to business logic

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-SDK-001..008, NFR-REL-006, NFR-MNT-002, NFR-MNT-006

### Context

Multiple entry points are required: headless runner, GUI, FastMCP handlers, replay verifier, tournament tooling, and reporting. Direct service access would duplicate policy and permit adapters to bypass validation or local-truth controls.

### Options considered

1. Let each adapter call domain services.
2. Put all logic in the Orchestrator.
3. Expose typed use cases through a versioned SDK facade while injecting ports.

### Decision

All business capabilities are invoked through `SimulationSdk`. Adapters translate input/output only. The SDK coordinates approved application use cases, returns typed results/errors, and accepts injected ports. Domain services remain independently testable and contain domain logic; the SDK does not become a monolith.

### Consequences

- One enforceable boundary for auth, validation, lifecycle, and local truth.
- Headless and GUI behavior stays identical.
- Public API compatibility must be versioned and tested.
- Adapters require integration tests proving they cannot bypass the SDK.

### Verification

Dependency tests, forbidden-import checks, SDK contract tests, public-method tests, and architecture review.

## ADR-002 - Ports-and-adapters architecture

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-SDK-006, FR-ORC-002, NFR-MNT-002, NFR-MNT-006, NFR-MNT-007

### Context

Core game, belief, strategy, and cryptographic behavior must remain deterministic and testable while transport, files, clocks, GUI, LLMs, tunnels, system inspection, and Gmail are failure-prone external concerns.

### Decision

Dependencies point inward:

```mermaid
flowchart LR
    A["CLI / GUI / MCP / Replay / Reporting adapters"] --> S["SimulationSdk application boundary"]
    S --> U["Application use cases / PeerOrchestrator"]
    U --> D["Domain and policy services"]
    U --> P["Port interfaces"]
    X["FastMCP / Files / Clock / RNG / LLM / Gmail adapters"] --> P
```

Domain modules import only domain/shared abstractions. Concrete adapters depend on ports; ports never depend on adapters. External calls pass through the Gatekeeper port where applicable.

### Consequences

- Deterministic in-memory tests and fault injection become straightforward.
- More interfaces and DTOs must be maintained.
- Architecture checks must prevent back imports and logic in controllers.

### Verification

Import-linter rules, dependency graph review, fake adapters, contract tests, and source-size/single-responsibility checks.

## ADR-003 - Two standalone exported role repositories

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-LGE-007..010, Appendix E rules 49-50

### Context

The submission requires separate Police and Thief repositories. Developing two copies from day one creates protocol and security drift; sharing a live package or filesystem at league time violates isolation.

### Options considered

1. Develop independently in two repositories.
2. Use one repository at runtime for both roles.
3. Develop one canonical workspace, then deterministically export two independently installable snapshots.

### Decision

Use option 3. The canonical workspace owns source, schemas, conformance vectors, and docs. A reviewed export manifest selects common and role-specific files. Each output gets its own lockfile, profile, README, tests, sibling link, history/tag, and no runtime dependency on the canonical workspace or other role.

### Consequences

- Minimizes design drift and maximizes cross-role conformance.
- Export tooling and manifests become release-critical.
- Both exports require independent clean-clone, secret, link, and compatibility tests.
- Any post-export patch must return to canonical source and regenerate both outputs.

### Verification

Manifest digests, clean-clone runs, disconnected-filesystem test, reciprocal links, and cross-version protocol matrix.

## ADR-004 - Canonical JSON and SHA-256

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-CFG-010, FR-CRY-001..015, NFR-SEC-003, NFR-SEC-010

### Context

Commit-Reveal fails if peers serialize equivalent data into different bytes. String concatenation is ambiguous and vulnerable to field substitution.

### Decision

- Payloads conform to a versioned schema and include a `schema_version`.
- Strings are Unicode NFC and encoded as UTF-8.
- Object keys are sorted lexicographically by Unicode code point.
- JSON uses separators `,` and `:` with no insignificant whitespace.
- Arrays preserve schema-defined order.
- Booleans and null use JSON literals.
- Non-finite numbers are rejected. Integer fields serialize as decimal integers; non-integer fields must use schema-defined decimal-string encoding rather than runtime float formatting.
- The fresh nonce is a canonical payload field for hash calculation but remains locally secret until final audit.
- SHA-256 hashes the exact canonical byte sequence and digests are lowercase hex in envelopes.
- Digest comparisons use constant-time comparison.

Illustrative numeric values elsewhere in the PDF do not alter Appendix F. Appendix F values populate schema defaults; legal negotiated changes are signed in `game.json`.

### Consequences

Golden vectors are mandatory across both repositories. Schema changes require a protocol/config version bump and compatibility decision.

### Verification

Exact byte fixtures, cross-process/cross-platform vectors, Unicode cases, reordered-key cases, non-finite rejection, mutation tests, and independent replay verification.

The normative M5 vector is
`data/conformance/crypto/commitment.v1.json`. Its canonical payload SHA-256 is
`c66e743102b1644d8d4b1e6a029c7eab8de235965d34e3cc56131d35eec5b716`.
The Step-0 canonical SHA-256 is
`33581788aaaad599e4dd653de2a6c7236f14a13e920aaeb77a1b99f13457a1d7`.

## ADR-005 - At-least-once delivery, exactly-once effects

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-NEG-012, FR-MCP-005..012, FR-ORC-006..012, NFR-REL-001..004, NFR-REL-007

### Context

Public networks can lose responses after applying requests. Blind retry can duplicate a move or barrier; avoiding retries makes recoverable loss terminal.

### Decision

Transport may retry within bounded deadlines, so delivery is at least once. Every mutating request carries stable game, phase, sequence, sender, message, correlation, and payload-digest identity. Before mutation, the receiver checks an atomic idempotency record:

- unseen identity + valid phase: apply once, persist effect and response atomically;
- same identity + same digest: return the persisted response;
- same identity + different digest: tamper/protocol violation;
- future/out-of-window sequence: reject or bounded-buffer according to the protocol mechanism PRD;
- stale sequence: return prior result only when identity/digest match.

Recovery resumes only at a mutually acknowledged durable checkpoint. It never fabricates acknowledgement or replays a possibly applied non-idempotent action.

### Consequences

Storage and state transition ordering are part of protocol correctness. Idempotency records must outlive retry windows and official audit evidence must preserve conflicts.

### Verification

Loss-after-apply, duplicate, reordering, reconnect, crash-at-boundary, digest-conflict, deadline, and bounded-queue fault tests.

## ADR-006 - Reject out-of-order requests without buffering

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-MCP-008, FR-MCP-010, NFR-SEC-008..009

### Context

At-least-once delivery requires clear gap handling. A receiver-side reorder buffer
adds memory pressure, expiry state, and another recovery surface before the
orchestrator has durable checkpoint agreement.

### Decision

M4 buffers zero protocol messages. After exact-idempotency replay is checked, the
receiver accepts only the next per-sender sequence. Old messages, bounded gaps,
and far-future messages receive typed sequence errors with no mutation. The
configured `reorder_window` classifies a normal gap versus an abusive future
sequence; it never allocates a buffer. The sender retries the missing exact bytes
within one monotonic Gatekeeper deadline.

### Consequences

- Memory use is constant under reordering and denial attempts.
- Senders must retain stable request bytes until acknowledgment.
- M8 may add a durable bounded buffer only through a new accepted ADR and protocol
  compatibility review.

### Verification

Duplicate, old, gap, far-future, delayed, retry-after-response-loss, and restart
tests plus configured-limit inspection.

## ADR-007 - HMAC-SHA-256 for course-key Step-0 declarations

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-NEG-007..010, FR-CRY-011..015

### Context

The course supplies shared signing semantics rather than a public-key identity
infrastructure. Step-0 must be authenticated before play without placing the key
in configuration, artifacts, exceptions, or logs.

### Decision

Each peer computes HMAC-SHA-256 over exact ADR-004 canonical Step-0 bytes. A key
contains at least 256 bits and is loaded from a named secret environment entry or
an already-open binary file handle. Public APIs never accept the key value or a
filesystem path. Verification uses constant-time comparison. Counted Step-0
requires a known clean exact Git commit.

### Consequences

Possession of the shared course key authenticates a declaration but does not
provide non-repudiation between key holders. Key rotation is external and a new
match requires new signed declarations.

### Verification

Golden HMAC, body/key/signature tamper, missing/short key, environment/file-handle
loading, serialization absence, repr/log redaction, clean/dirty/unknown Git, and
two-peer preflight tests.

## ADR-014 - Exact scent decimals and boundary-only quantization

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-BEL-001..015, Appendix E rules 8-9 and 23

### Context

Binary floats and per-operation rounding can make two peers produce different
scent frames and commitments despite starting with identical moves. Belief
updates need efficient log-space arithmetic, but their tolerances must not weaken
the exact evidence contract.

### Decision

- Scent parameters, kernel, accumulation, clamp, and decay use finite base-10
  `Decimal` arithmetic with context precision 28 or greater.
- Internal scent values are never rounded. At wire/audit boundaries only, values
  quantize to six places using `ROUND_HALF_EVEN` and serialize as fixed-point
  decimal strings.
- Scent frames use row-major sparse ordering and canonical JSON before SHA-256.
- Beliefs use finite binary floats, log-sum-exp normalization, and absolute
  normalization tolerance `1e-12`.
- Belief diagnostic/audit output quantizes row-major probabilities to 12 fixed
  decimal places. Quantized values never feed a later live update.
- NaN, infinity, negatives, exponent-form scent strings, and dimension/range
  mismatches fail closed.

### Consequences

Scent commitments are byte-stable across platforms. Belief implementations may
use optimized local floating-point math while sharing an explicit acceptance
tolerance and deterministic diagnostic digest. Internal exact scent state must be
persisted as decimal strings, not binary floats.

### Verification

The vector `data/conformance/scent/emission_decay.json` covers center, edge,
corner, overlap, repeated stay, and full-turn decay. Schema/digest substitution,
restart restoration, long-run underflow, normalization, and two-independent-peer
tests verify both numeric profiles.

## ADR-015 - Orchestrator as an injected policy-free gateway

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-ORC-001..006, NFR-MNT-001..007

The `PeerOrchestrator` owns phase ordering, deadlines, cancellation, progress, and
terminal mapping only. Physics, belief, strategy, crypto, parsing, transport,
persistence codecs, artifacts, and reporting remain behind injected ports and
the public SDK. This makes the complete lifecycle model-testable without a remote
peer and prevents a second implementation of business rules.

## ADR-016 - Append-only local orchestration event journal

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-ORC-007..010, NFR-REL-001..004

Mutating inbound events append canonical JSON with monotonic sequence, previous
hash, and record hash through an atomic byte repository before acknowledgement.
Restoration validates every link, session, and config binding. Corruption fails
closed; a derived artifact is never treated as mutable live state.

## ADR-017 - One monotonic deadline policy for every wait

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-ORC-006, FR-ORC-011..013, NFR-PERF-002, NFR-REL-001..002

All waits and expensive operations receive absolute monotonic deadlines from an
effective config policy. Shared response/watchdog values win; private config owns
other local limits. Only transport-class failures retry, with identical
idempotency context, finite attempts, exponential backoff, bounded seeded jitter,
and circuit breaking. Semantic and integrity failures never retry.

## ADR-018 - Exact mutual checkpoint recovery

**Status:** Accepted
**Date:** 2026-07-25
**Requirements:** FR-ORC-009, FR-ORC-011..012, NFR-REL-002..004, NFR-REL-007

Recovery resumes only when both peers present the same canonical digest of a
session/config-bound, journal-linked, mutually acknowledged checkpoint. There is
no nearest-state merge, invented acknowledgement, or silent rollback. Disagreement
terminates safely and preserves the evidence needed to distinguish technical
failure from tamper.
