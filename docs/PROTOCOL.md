# Peer Protocol and Interoperability Contract

**Contract version:** `0.7.0`
**Schema family:** `0.2.0`
**Package:** `0.11.0`
**Status:** Tool names stable since M4; audit, scent, and reliability semantics frozen through M11; M12/M13 consume the same peer contract
**Authority:** `docs/PRD.md`, mechanism PRDs, ADR-004/005/006/014, `docs/SCHEMAS.md`

## 1. Boundary and ownership

Each peer is an independent process with its own configuration, artifact, cache,
and temporary roots. The only live peer-to-peer channel is FastMCP over HTTP. An
inbound FastMCP tool converts framing to bytes and calls `SimulationSdk`; it owns
no session or game rule. An outbound adapter submits immutable canonical bytes to
the central Gatekeeper; only the Gatekeeper's backend may invoke FastMCP.

No health, capability, status, or error response exposes a private path, private
configuration, local ledger contents, stack trace, credential, nonce, strategy
state, or opponent truth.

## 2. Frozen tool inventory

All tool semantic versions remain `1.0.0` within protocol `0.6.0`; M5/M6 advance
payload contracts while preserving the M4 tool names and ownership.

| Tool | Request owner | Response owner | Mutating | Required phase -> next phase |
|---|---|---|---|---|
| `health_v1` | any preflight caller | receiving peer | no | none |
| `capabilities_v1` | any preflight caller | receiving peer | no | none |
| `propose_match_v1` | remote proposing group | receiving peer | yes | `NEGOTIATING -> NEGOTIATING` |
| `accept_match_v1` | remote accepting group | receiving peer | yes | `NEGOTIATING -> READY` |
| `commit_step_v1` | scheduled acting group | receiving peer | yes | `READY/WAITING -> AWAITING_ACK` |
| `acknowledge_step_v1` | scheduled remote group | receiving peer | yes | `AWAITING_ACK -> REVEALING` |
| `reveal_step_v1` | scheduled acting group | receiving peer | yes | `REVEALING -> WAITING/AUDITING` |
| `capture_claim_v1` | scheduled Police group | receiving peer | yes | `WAITING -> VERIFYING` |
| `capture_response_v1` | scheduled Thief group | receiving peer | yes | `VERIFYING -> WAITING/AUDITING` |
| `final_reveal_v1` | either negotiated group | receiving peer | yes | `AUDITING -> AGREEING_RESULT` |
| `audit_result_v1` | either negotiated group | receiving peer | yes | `AGREEING_RESULT -> REPORTING` |
| `agree_result_v1` | either negotiated group | receiving peer | yes | `REPORTING -> COMPLETED` |
| `peer_status_v1` | negotiated remote group | receiving peer | no | unchanged |

M4 freezes framing, negotiation, reliability, and phase ownership. M5 fills the
commit, capture, reveal, audit, and result payload schemas with cryptographic
semantics without changing tool names or envelope identity.

The M5 normative payload and sanction rules are in `docs/CRYPTO_AUDIT.md`.
Commit sends only identity/digest, acknowledgement locks exact bytes, live reveal
conforms to `live_reveal.schema.json` and forbids nonce, final reveal conforms to
`final_reveal.schema.json`, audit results conform to `audit_report.schema.json`,
and reporting requires matching audit-manifest and independent-result digests.
M6 adds `scent_frame.schema.json`: the frame is sparse, bounded, linked to exact
game/sub-game/step/actor/model identity, and its digest is sealed in the M5
commitment. It contains evidence cells, never an opponent true position.

## 3. Common envelope

Every session-bound request validates against
`schemas/protocol_envelope.schema.json` and carries:

```json
{
  "protocol_version": "0.6.0",
  "message_type": "commit_step_v1",
  "message_id": "7aa6fd2e-80b7-4adf-a0c7-533c41b7429c",
  "correlation_id": "2445bb6f-050d-4595-8c3e-cf6028554a69",
  "game_uid": "11111111-1111-4111-8111-111111111111",
  "sub_game_number": 1,
  "step_number": 1,
  "sender": {"group_id": "GRP00001", "role": "police"},
  "sequence": 3,
  "payload": {"commitment": "0000000000000000000000000000000000000000000000000000000000000000"}
}
```

UUIDs are canonical lowercase strings. Counters are positive signed 32-bit
integers. The sender role must equal the frozen role schedule for that sub-game.
The exact canonical envelope bytes are reused on every retry.

## 4. Resource limits

The private network configuration owns the following public-input ceilings:

| Key | Example | Enforcement |
|---|---:|---|
| `network.max_request_bytes` | `65536` | envelope UTF-8 byte ceiling |
| `network.max_json_depth` | `16` | recursive object/array depth |
| `network.max_string_length` | `4096` | every key and string value |
| `network.max_collection_items` | `256` | each object or array |
| `network.reorder_window` | `8` | distinguishes bounded gap from far future |
| `rate_limiter_gatekeeper.concurrent_requests` | `2` | inbound semaphore and outbound Gatekeeper |
| `network_and_league.response_timeout_sec` | `30` | monotonic outbound deadline |

Duplicate JSON keys, invalid UTF-8, non-object roots, booleans in integer fields,
non-finite numbers, unknown fields, and malformed UUIDs fail before session access.
An already-full inbound semaphore rejects overload; it does not wait unboundedly.

## 5. Negotiation contract

`propose_match_v1` uses `match_proposal.schema.json`. It binds:

- both group names, eight-character counted identities, members, role
  capabilities, credential-free MCP URLs, and all four distinct HTTPS role
  repository URLs;
- exact 40-lowercase-hex played commits for both role artifacts of both groups;
- truthful prior counted totals and unique opponent ledgers;
- explicit `counted` or named warmup status, never both;
- deterministic `game_id`, proposer-selected UUID `game_uid`, schema/protocol
  versions, and the balanced six-sub-game schedule;
- base64 exact shared-config bytes, their raw SHA-256, canonical config SHA-256,
  scent-model SHA-256, and `scent-5x5-v1` numeric-vector version;
- both complete Step-0 declarations and namespaced optional capabilities.

The deterministic game slug is:

```text
match-<first 24 hex of SHA-256(sorted_group_a-group_b:config_sha256)>
```

Each receiver compares the exchanged raw bytes directly to its local bytes, then
checks both raw and canonical digests. A one-byte difference refuses play.
`accept_match_v1` requires the exact proposal, game, UUID, and schedule digests.

For counted mode, both IDs are exactly eight ASCII alphanumerics, the local
participant declaration must equal the immutable local ledger, totals `0..9` may
start a match, totals `10+` may not, and an already-counted opponent is refused.
Named warmups never update the counted ledger.

Optional capabilities use a dotted/dashed namespaced key. Only the intersection
of locally and remotely named capabilities is retained. Unknown optional
capabilities cannot alter any mandatory field, fixed value, minimum protection,
phase, identity, or security control.

## 6. Inbound pipeline and exactly-once effects

Every mutating request executes this ordered pipeline:

```text
parse -> session -> identity -> idempotency -> phase/sequence
      -> persist intent -> SDK mutation -> persist session/effect
      -> persist completed response -> acknowledge
```

The idempotency key is `(game_uid, sender_group, message_id)`. Its record stores
the request digest, `pending|completed` state, and completed response.

1. An unseen valid request writes `pending` before mutation.
2. The effect, next sequence, phase, and exact response are atomically persisted
   in the session snapshot.
3. The receipt becomes `completed` before success returns.
4. A same-key/same-digest retry returns the exact prior response.
5. A same-key/different-digest retry returns `IDEMPOTENCY_CONFLICT` with no
   mutation.
6. After a crash between steps 2 and 3, the durable session receipt repairs the
   pending idempotency record and returns the prior response.
7. After a crash between steps 1 and 2, retry safely applies the still-absent
   effect once.

Files are written to a sibling temporary file, flushed, and atomically replaced.
Keys are fixed safe digests; traversal and oversized records are rejected.
Official records are retained with the match evidence through the release
retention period.

## 7. Sequence and phase policy

Sequences are monotonic per sender and session, starting at one. Exact retries
are resolved by idempotency before sequence validation. A different message with
an old sequence is rejected. A gap inside `reorder_window` is rejected as
out-of-order; a larger gap is rejected as far-future. M4 intentionally buffers
zero messages, so memory use is constant and senders retry only the missing
stable request.

`COMPLETED`, `TECHNICAL`, `TAMPER`, and `STOPPED` are immutable terminal phases.
Any tool/phase pair not listed in section 2 fails with `PHASE_VIOLATION` before
intent persistence.

## 8. Response and error catalog

All responses have `ok`, `code`, `message`, `correlation_id`, and `payload`.

| Code | Meaning |
|---|---|
| `OK` | request applied or safe query completed |
| `PROTOCOL_VALIDATION` | framing, schema, bounds, version, or terms invalid |
| `UNKNOWN_SESSION` | game is unknown; no registry information is exposed |
| `IDENTITY_MISMATCH` | sender group or scheduled role differs |
| `PHASE_VIOLATION` | tool is illegal in the current phase |
| `SEQUENCE_VIOLATION` | stale, duplicate-with-new-ID, gap, or future sequence |
| `IDEMPOTENCY_CONFLICT` | one message ID was reused with different bytes |
| `REQUEST_TIMEOUT` | monotonic outbound deadline expired |
| `SERVER_OVERLOADED` | configured inbound concurrency is full |
| `INTERNAL_FAILURE` | unexpected local failure mapped to a safe correlation ID |

Unexpected exceptions never cross FastMCP. Logs may retain redacted diagnostics,
but the remote message is fixed and contains no exception type, stack, path, URL
credential, or private payload.

## 9. Startup and retry

Either peer may start first. Health and capabilities are state-free and use
bounded retries. Every outbound call enters the Gatekeeper, which enforces a
single monotonic deadline, concurrency, and bounded attempts. Mutation retries
reuse the same immutable `ExternalCall`, envelope string, message ID, and bytes.
The raw FastMCP backend is not accessible from `McpClientAdapter`.

League deployment terminates TLS at an approved public tunnel or reverse proxy.
URLs must contain no user-info credentials. M4 localhost permits `http` loopback;
public rehearsal requires `https`, independent bidirectional preflight, and the
security controls finalized in M8/M11.

## 10. Reproducible interoperability check

Run:

```text
uv run pytest tests/integration/test_dual_process_mcp.py -q
uv run pytest tests/integration/test_protocol_runtime.py -q
uv run pytest tests/contract/test_protocol_contracts.py -q
```

The dual-process runner executes both A-first and B-first. It proves distinct
PIDs; separate config, artifact, cache, and temporary roots; exact shared config
bytes; bounded readiness; mirrored proposal/acceptance; and the same terminal
public phase sequence over streamable HTTP FastMCP.

Interoperability checklist:

- [x] package installs from the frozen lockfile;
- [x] `health_v1` and `capabilities_v1` return no session/private state;
- [x] protocol major/minor policy agrees;
- [x] all proposal, acceptance, envelope, and declaration schemas validate;
- [x] raw config, config digest, scent digest/vector, groups, commits, URLs,
  counted terms, UUID, and six-role schedule agree;
- [x] duplicate and lost-response retries have exactly one effect;
- [x] conflicting IDs, malformed input, gaps, future messages, illegal phases,
  timeouts, and overload fail closed;
- [x] both process start orders reach `COMPLETED`;
- [x] peers have no shared writable runtime root or direct IPC.
