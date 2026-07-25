# Configuration and Contract Guide

## Authority and files

The byte-identical, mutually agreed `game.json` is the match constitution. The
private `game.toml` belongs to one peer and is never transmitted. Shared terms
always win, and the private typed model intentionally has no field capable of
overriding board, movement, scent, scoring, league, or Gatekeeper rules.

Safe examples:

- `config/shared/game.example.json`
- `config/private/game.example.toml`
- `config/rate_limits.example.json`

The schemas are package resources under `police_thief_p2p.schemas`, so validation
works from source and from an installed wheel.

## Shared contract

The shared document requires schema version `0.2.0`, two distinct group IDs, all 32
Appendix F fields, the signed scent kernel/rounding/example, and an optional
`extensions` object. Every object rejects unknown properties. Extension keys must
be namespaces such as `example.policy`; an unqualified key such as `policy` fails.

Fixed and minimum values are maintained once in the typed rule tables. In
particular, requests per minute and concurrency are safety maxima: 30 and 2 are
accepted ceilings, while lower values are stricter. Retry backoff, retry count, and
bounded queue capacity become stricter by increasing.

## Private contract and secrets

The private TOML has exactly these sections:

`identity`, `network`, `paths`, `strategy`, `language`, `email`, `gui`, `tunnel`,
and `observability`.

Provider keys and OAuth client secrets are referenced by uppercase environment
variable name. The resolver reads only names declared in `language.api_key_env` or
`email.oauth_client_secret_env`. Environment variables such as `GRID_SIZE` have no
configuration effect. Resolved secret containers permanently redact their
representation.

## Canonical JSON

Canonicalization recursively normalizes strings and keys to Unicode NFC, sorts
keys by code point, preserves array order, emits UTF-8 with separators `,` and `:`,
and rejects floats, decimal objects, NaN, infinity, unsupported types, and keys
that collide after normalization. Non-integers are schema-defined decimal strings.

The semantic digest is:

```text
SHA256(canonical_utf8(validated_shared_model))
```

Negotiation must check exact raw bytes separately. A whitespace-only difference
can preserve semantic digest equality while failing the raw-byte requirement.

## Schema inventory

| Schema | Boundary |
|---|---|
| `game.schema.json` | Complete shared constitution |
| `rate_limits.schema.json` | Per-service Gatekeeper policies |
| `declaration.schema.json` | Step-0 identity/config/scent declaration |
| `sub_game_config.schema.json` | Exact played config artifact |
| `log.schema.json` | Ordered sealed-step and audit log |
| `final_result.schema.json` | Commits, tokens, scores, links, and agreement |
| `protocol_envelope.schema.json` | Versioned IDs, sender, sequence, and payload |

All schemas use JSON Schema Draft 2020-12. Valid and invalid artifacts, canonical
bytes, digests, and scent math are indexed by `data/conformance/manifest.json`.

## SDK usage

Adapters call `SimulationSdk.load_configuration(...)`; they do not import loaders
directly. `SimulationSdk.check_readiness()` reports `config.contracts` and fails
readiness if packaged schema and protocol versions drift.

Configuration failures have stable `CFG_*` codes, the safe source, and an exact
JSON/TOML path. Raw input and secret values are never retained in the exception.
