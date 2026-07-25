# Dependency Policy and Rationale

- **Package baseline:** `0.1.0`
- **Manager:** `uv` only
- **Lock:** `uv.lock`

## Runtime dependencies

| Dependency | Constraint | Purpose | Boundary |
|---|---|---|---|
| `fastmcp` | `>=3.4.3,<4` | Required symmetric MCP server/client foundation for M4 | Adapter only; no domain import |
| `pydantic` | `>=2.12,<3` | Strict typed external/configuration DTO validation | Boundary models; domain remains framework-light |
| `jsonschema` | `>=4.25,<5` | Portable validation of signed artifacts and shared config schemas | Configuration/artifact services |

No runtime dependency is added for hashing, nonces, TOML reads, clocks, logging,
queues, or baseline strategy. The Python standard library owns those capabilities.

## Development dependencies

| Dependency | Purpose |
|---|---|
| `pytest` | Test discovery and execution |
| `pytest-cov` | Branch/statement coverage gate |
| `hypothesis` | Property-based input generation |
| `ruff` | Lint and format gate |
| `mypy` | Strict static typing |
| `pre-commit` | Reproducible local quality hooks |
| `detect-secrets` | Credential-pattern scanning |
| `pyyaml` | Parse and structurally validate GitHub Actions YAML |

## Rules

- Add or remove packages only with `uv add`, `uv add --dev`, or `uv remove`.
- Review `pyproject.toml` and `uv.lock` together.
- Prefer bounded compatible ranges plus the exact lockfile.
- Record security, license, transitive-size, and optional-service implications.
- No dependency may bypass the SDK, Gatekeeper, local-truth, or deterministic-core
  boundaries.
