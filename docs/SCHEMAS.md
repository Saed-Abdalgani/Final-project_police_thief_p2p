# Artifact and Protocol Schemas

**Schema family:** `0.2.0`
**Package:** `0.11.0`
**Canonicalization:** ADR-004 and `src/police_thief_p2p/shared/canonical_json.py`

## 1. Four artifact families

Every counted sub-game writes four independently rooted families under the peer
artifact root. Linkage is declared by the official artifact manifest; digests are
SHA-256 over canonical JSON bytes.

| Family | Typical path | Purpose | Governing schema |
|---|---|---|---|
| protocol | `artifacts/protocol/` | envelopes, proposals, accepts, reveals | `protocol_envelope.schema.json`, `match_proposal.schema.json`, `match_acceptance.schema.json`, `live_reveal.schema.json`, `final_reveal.schema.json` |
| official | `artifacts/official/` | immutable manifest and scored result | `artifact_manifest.schema.json`, `final_result.schema.json`, `sub_game_config.schema.json` |
| audit | `artifacts/audit/` | mutual audit reports and capture statements | `audit_report.schema.json`, `capture_statement.schema.json`, `declaration.schema.json`, `commitment_body.schema.json` |
| replay | `artifacts/replay/` | local logs and verified replay audits | `log.schema.json`, `replay_audit.schema.json`, `belief_summary.schema.json`, `scent_frame.schema.json` |

Schema sources live in `src/police_thief_p2p/schemas/`. Shared game and rate-limit
contracts use `game.schema.json` and `rate_limits.schema.json`.

## 2. Canonicalization rules

- Unicode NFC, UTF-8, lexicographic object keys, separators `,` and `:`.
- Non-finite numbers rejected; non-integers as decimal strings where required.
- Digests are lowercase hex; comparisons are constant-time.
- Normative crypto vector: `data/conformance/crypto/commitment.v1.json`.

## 3. Linkage

`artifact_manifest.schema.json` enumerates relative paths and digests for every
retained artifact. Replay and report construction admit only manifest-linked,
schema-valid files. Dual-log objective reconstruction is gated behind mutual
audit success in the SDK.

## 4. Conformance examples

| Area | Path |
|---|---|
| Domain golden scenarios | `data/conformance/domain/golden_scenarios.json` |
| Commitment / Step-0 digests | `data/conformance/crypto/commitment.v1.json` |
| Valid final result fixture | `data/conformance/artifacts/final_result.valid.json` |

## 5. Version compatibility

| Contract | Version | Notes |
|---|---|---|
| Package | `0.11.0` | M12 experiment surface + M13 export tooling |
| Protocol tools | `0.7.0` | Tool names stable; payload contracts advanced since `0.6.0` docs freeze |
| Schema family | `0.2.0` | Artifact and envelope schemas |
| Strategy profile | `1.0.0` | Private TOML `profile_version` |

Cross-role exports must share the same protocol/schema family or refuse
negotiation.
