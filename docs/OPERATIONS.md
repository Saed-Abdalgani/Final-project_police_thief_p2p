# Peer Operations and Recovery

## Startup

Load shared JSON and private TOML through `SimulationSdk`, create the protocol
runtime with its private durable root, then run the peer lifecycle through
`SimulationSdk.run_peer_lifecycle`. Startup moves through `created`,
`initializing`, `ready`, and `negotiating`. Either peer may start first; readiness
calls use the shared response timeout, retry only transport failures, and end in a
typed technical loss when the bounded attempt budget is exhausted.

Before public play, normalize and validate the tunnel URL. Competition endpoints
must use public HTTPS, contain no credentials or fragments, and pass health,
capability, round-trip, payload-limit, and bidirectional probes within one
deadline.

## Timeouts and health

Every negotiation, MCP, acknowledgement, reveal, strategy, LLM, audit, and report
operation receives a `DeadlineTracker`. Shared response/watchdog values remain
authoritative; private reliability config supplies the other local bounds.
Semantic, phase, validation, and integrity failures never retry. Transport
timeouts, reset/refusal, selected 5xx, and dependency unavailability use identical
idempotent bytes, exponential backoff, bounded seeded jitter, and a circuit
breaker.

Heartbeat fields are phase, step, monotonic timestamp, and an increasing progress
token only. Public health is exactly `alive`, `ready`, `degraded`, or `failed`.
The independent Watchdog intervenes on absent heartbeat or unchanged progress and
persists only a redacted snapshot.

## Recovery

Inbound mutations are journaled and flushed before acknowledgement. Journal
records have monotonic sequence and a local SHA-256 chain. A checkpoint binds the
session, config digest, phase, sub-game, step, journal sequence/head, and last
mutually acknowledged commitment.

On restart:

1. validate the journal sequence/hash chain;
2. validate checkpoint session and config identity;
3. exchange the exact checkpoint digest;
4. resume only when both digests match;
5. otherwise terminate with tamper/integrity or technical outcome.

Never invent an acknowledgement, silently roll back, or select the nearest common
state. Crash-injection tests cover before/after journal and acknowledgement.

## Backpressure and shutdown

Gameplay and audit work outrank reporting and banter. Queues are capacity-bounded;
critical work may evict optional tail work, otherwise admission returns explicit
backpressure. No producer can create an unbounded wait or allocation.

Controlled shutdown first signals cooperative cancellation, then closes in this
order: transport, journal, artifact writer, GUI, workers. Terminal phases
(`completed`, `refused`, `technical-loss`, `tamper`) are immutable.

The 1,000-sub-game deterministic persistence/Watchdog soak and fault matrix are
recorded in `results/benchmarks/m8_reliability.json`.
