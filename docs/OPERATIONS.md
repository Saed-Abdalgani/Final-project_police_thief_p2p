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

## Official artifacts

Set `paths.artifact_root` to a local data directory. Official evidence is written
under `official/`, pre-audit sealed evidence under `private/`, and rotating
diagnostics under `diagnostics/`. Do not manually edit an official artifact.
Existing filenames are immutable; a conflicting rewrite indicates an integrity
failure.

Before replay, export, or reporting, load `manifest_<game_id>.json` through
`SimulationSdk.load_artifact_manifest` and verify it against the same artifact
root. Verification recomputes every byte digest and every identity/config/commit/
journal/audit/result edge. Preserve corrupt files for diagnosis; never repair
them in place.

Run a side-effect-free reporting check with:

```text
uv run police-thief-p2p report validate --manifest <manifest.json> --artifact-root <root> --sender <account@example.com>
```

`VALID` means the manifest, six config/log pairs, final result, mutual agreement,
score/token totals, JSON attachment, and MIME all passed. It does not create an
outbox item, open a browser, refresh OAuth, or contact Gmail.

## Gmail authorization and delivery

Keep `credentials.json` and `token.json` in configured private paths outside the
artifact root. Both filenames and common key/certificate formats are ignored by
Git. Gmail authorization requests exactly the `gmail.send` scope. First use opens
the installed-app PKCE authorization page and accepts one loopback callback;
subsequent use refreshes the owner-only token file. Never paste tokens into TOML,
commands, evidence, logs, issues, or chat.

Production flow is: verify manifest, build report, atomically enqueue, dispatch
through the Gmail Gatekeeper profile, and persist the provider result. A restart
while `SENDING` recovers to `RETRY_WAIT`. `SENT` is idempotent and never sends
again. Authentication errors become visible permanent failures; timeout, 429,
5xx, quota, queue, anomaly, and open-circuit states remain visible and
recoverable without rewriting the result.

For the mandatory real rehearsal, use a safe address controlled by the team and
never the lecturer address. Confirm the recipient out of band, run exactly one
send, preserve only the logical report ID, attachment digest, timestamp, terminal
outbox state, and a hash/redaction of the provider ID. Delete no token/outbox
state afterward. A lecturer send is permitted only for the actual agreed
competition report.

## Live GUI operations

Construct `LiveApp` with a configured `SimulationSdk` and an SDK-created
`SnapshotChannel`. Start the gameplay producer with
`SimulationSdk.run_live_async`; never run transitions or network waits in a Tk
callback. Only `LocalView` may enter the channel. Start, Pause, Resume, Stop,
Restart, and Quit call the SDK lifecycle port. Stop/restart/quit require operator
confirmation in the GUI.

If rendering falls behind, intermediate visuals coalesce. The newest final,
terminal, or error snapshot is retained, while official protocol events remain
in their authoritative journal and never enter the visual queue. Closing the
window requests cooperative SDK shutdown; headless gameplay remains fully
functional when Tk is absent.

## Replay operations

Run `police-thief-p2p replay verify` against the official series manifest and
artifact root. Admission verifies the full 14-document digest/link graph before
selecting a sub-game. Do not open individual files in the GUI or combine logs
outside the SDK.

`Verified OK` permits navigation and report export. `TAMPERED` stops normal
verification at the first invalid step, assigns no points in the replay report,
and preserves its typed finding. Keep the source artifacts unchanged. Objective
dual-track replay is post-audit only; single-log mode shows local track plus
belief and labels the missing sibling. Unequal linked tracks freeze the shorter
track explicitly rather than inventing positions.

## Gatekeeper recovery

Limits are loaded from `config/rate_limits.example.json` or its reviewed private
equivalent; never patch limits in code. A 429 wait is at least the configured
backoff and provider `Retry-After`. Circuits move from open to one half-open probe
after cooldown. Manual circuit/anomaly or session-quota reset requires explicit
operator confirmation. Inspect only redacted metrics: tokens, quotas, queue
depth, concurrency, retries, rejections, and circuit state.

## Role-repository export

Export both standalone peers from one frozen canonical commit:

```text
uv run python -m scripts.export_role_repo both
uv run python -m scripts.verify_release release/exports/GRP00001-police-p2p release/exports/GRP00001-thief-p2p
```

Manifests live under `release/export_manifests/`. Generated trees under
`release/exports/` are not committed. After verification, push each export to its
sibling GitHub repository and annotate `v1.0-submission` only on a clean verified
commit.
