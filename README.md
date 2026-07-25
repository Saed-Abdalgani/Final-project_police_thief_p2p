# Distributed Police-Thief P2P

Two autonomous, independently running Police and Thief peers compete over FastMCP
without a central game server or shared live state. Each peer owns only local truth,
uses SHA-256 Commit-Reveal for later audit, and exposes all business capabilities
through a typed `SimulationSdk`.

Status: scent and Bayesian-belief milestone. Strict configuration, deterministic
local-only physics, FastMCP negotiation, sealed mutual audit, exact scent
evidence, privacy-safe probabilistic tracking, and independent fail-closed replay
are complete.

## Requirements

- Windows, Linux, or macOS.
- [`uv`](https://docs.astral.sh/uv/) `0.11.14`.
- CPython 3.13 or newer. The repository pins 3.13 for local development and tests
  Python 3.13/3.14 in CI.

Do not install dependencies with `pip`, `venv`, `virtualenv`, or `python -m`.

## Installation

```text
git clone <repository-url>
cd Final-project_police_thief_p2p
uv python install 3.13
uv sync --frozen --all-groups
```

Verify the foundation:

```text
uv run police-thief-p2p readiness
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests scripts
uv run pytest
uv build
```

## Usage

The CLI adapter exposes readiness:

```text
uv run police-thief-p2p readiness
uv run police-thief-p2p readiness --json
```

Application adapters must call `SimulationSdk`; importing domain or service
implementations from CLI, GUI, MCP, or Gmail adapters is prohibited.

Run one peer with its private bind/root settings:

```text
uv run python -m police_thief_p2p.adapters.mcp.peer_process \
  --shared-config config/shared/game.example.json \
  --private-config config/private/game.example.toml
```

Run the two-process A-first/B-first interoperability campaign:

```text
uv run pytest tests/integration/test_dual_process_mcp.py -q
```

## Configuration

- `.env-example` documents local environment names without real secrets.
- Shared match rules use `config/shared/game.example.json` as the signed contract.
- Private peer settings use `config/private/game.example.toml`.
- Per-service external-call limits use `config/rate_limits.example.json`.
- Only declared secret references are resolved from environment variables; shared
  rules cannot be overridden by environment or private TOML.
- `.env`, OAuth files, tokens, keys, runtime logs, generated results, and temporary
  files are ignored by Git.

Appendix F status semantics, parser limits, canonicalization, provenance, schemas,
and examples are documented in [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) and
remain traceable through [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md).

## Examples

Python callers use the SDK:

```python
from police_thief_p2p import SimulationSdk

report = SimulationSdk().check_readiness()
print(report.status.value)
```

No adapter may call an internal service directly.

Validate and merge configuration through the SDK:

```python
from pathlib import Path

from police_thief_p2p import SimulationSdk

effective = SimulationSdk().load_configuration(
    Path("config/shared/game.example.json").read_bytes(),
    Path("config/private/game.example.toml").read_bytes(),
    submission_mode=True,
)
print(effective.shared.digest())
```

Create and transition local game state through the SDK:

```python
from police_thief_p2p.sdk import Action, Role

state = SimulationSdk().create_local_game(effective.shared, Role.POLICE)
next_state = SimulationSdk().apply_action(state, Action.stay()).state
print(next_state.step_number)
```

Domain mechanics, scoring, privacy boundaries, and evidence are documented in
[`docs/DOMAIN.md`](docs/DOMAIN.md).

The exact FastMCP inventory, envelopes, proposal fields, phases, idempotency
algorithm, error codes, retry policy, examples, and interoperability checklist are
documented in [`docs/PROTOCOL.md`](docs/PROTOCOL.md).

Commitment bytes, nonce lifecycle, signed declarations, evidence chaining,
failure sanctions, replay order, and mutual result agreement are documented in
[`docs/CRYPTO_AUDIT.md`](docs/CRYPTO_AUDIT.md).

## Development

Use test-driven changes and keep public behavior linked to requirement IDs:

```text
uv sync --frozen --all-groups
uv run pre-commit run --all-files
uv run pytest
```

The complete test strategy, markers, and clean-clone sequence are in
[`docs/TESTING.md`](docs/TESTING.md). Architecture and security decisions are in
[`docs/PLAN.md`](docs/PLAN.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), and
[`docs/SECURITY.md`](docs/SECURITY.md).

## Troubleshooting

- **Wrong Python selected:** run `uv python install 3.13` and `uv sync --reinstall`.
- **Lockfile mismatch:** do not edit `uv.lock`; use `uv add`, `uv remove`, or
  `uv lock`, then review the diff.
- **Readiness command fails:** run `uv run python scripts/validate_structure.py`
  and inspect the returned missing path.
- **Peer does not become ready:** verify the configured port is free and call
  `health_v1` at the streamable-HTTP `/mcp` endpoint; startup retries are bounded.
- **Negotiation is refused:** compare exact shared-file bytes first, then
  `config_sha256`, scent digest/vector, protocol/schema, group IDs, commits, URLs,
  counted ledger, game UUID, and role schedule in that order.
- **Sequence/conflict error:** retry the exact original envelope and message ID;
  never construct new bytes for an uncertain mutation.
- **Secret scanner flags a value:** remove/rotate the value. Do not suppress a real
  credential in a baseline.
- **Tk unavailable:** headless operation remains the required functional path; GUI
  support is implemented and tested in M10.

## Contribution Rules

1. Start from the current canonical branch and use a focused review branch.
2. Update the owning PRD/ADR before changing public protocol, schema, config, or SDK
   behavior.
3. Add tests for happy, edge, invalid, and dependency-failure paths.
4. Preserve SDK-only access, Gatekeeper routing, local truth, and no shared state.
5. Run the complete foundation command suite before review.
6. Never commit generated results or secrets.

## Security

Treat all remote input as hostile. Report vulnerabilities privately to the project
team; do not open an issue containing tokens, opponent private state, nonces, or
exploitable league details. See [`docs/SECURITY.md`](docs/SECURITY.md).

## Credits and Reference Use

Attribution and the reference-code policy are recorded in
[`CREDITS.md`](CREDITS.md). The public example repository is informative only and
does not override the supplied rules book.

## License

Project-owned code is released under the MIT License. Third-party material retains
its original license and attribution.
