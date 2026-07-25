# Distributed Police-Thief P2P

Two autonomous, independently running Police and Thief peers compete over FastMCP
without a central game server or shared live state. Each peer owns only local truth,
uses SHA-256 Commit-Reveal for later audit, and exposes all business capabilities
through a typed `SimulationSdk`.

Status: foundation milestone. The SDK shell and engineering controls exist; gameplay
and network behavior are implemented in later milestones.

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

The M1 CLI is an adapter over the SDK and currently exposes a readiness command:

```text
uv run police-thief-p2p readiness
uv run police-thief-p2p readiness --json
```

Application adapters must call `SimulationSdk`; importing domain or service
implementations from CLI, GUI, MCP, or Gmail adapters is prohibited.

## Configuration

- `.env-example` documents local environment names without real secrets.
- Future shared match rules live in signed `config/shared/game.json`.
- Future private peer settings live in local TOML and environment variables.
- `.env`, OAuth files, tokens, keys, runtime logs, generated results, and temporary
  files are ignored by Git.

Appendix F values and status semantics remain governed by
[`docs/TRACEABILITY.md`](docs/TRACEABILITY.md).

## Examples

Python callers use the SDK:

```python
from police_thief_p2p import SimulationSdk

report = SimulationSdk().check_readiness()
print(report.status.value)
```

No adapter may call an internal service directly.

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
