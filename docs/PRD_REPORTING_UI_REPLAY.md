# Mechanism PRD - Artifacts, Reporting, Live UI, and Replay

**Status:** M0 approved outline; finalize before M9/M10 implementation
**Owners:** Artifact Lead, Reporting Lead, UX Lead
**Requirements:** FR-ART-001..013, FR-RPT-001..013, FR-UI-001..015
**Rules:** Appendix E 8-9, 20, 28-35, 39-44, 49-51, 54-55

## Purpose and scope

Define four linked artifact families, atomic event evidence, mutually agreed Gmail JSON reporting, live local-truth monitoring, and post-audit replay verification. All entry points call the SDK; Gmail calls pass through Gatekeeper.

## Inputs

- typed SDK local-view, status, replay, artifact, and reporting use cases;
- verified shared config, declaration, sub-game events/audits, final result agreement;
- artifact root, naming policy, schemas, and retention classification;
- local GUI accessibility preferences;
- send-only OAuth handle and allowlisted recipient;
- durable outbox and Gatekeeper policies.

## Outputs

- one declaration and result per series;
- one exact config and finalized log per sub-game;
- atomic, schema-valid, digest-linked artifact manifest;
- live GUI containing own truth, public state, belief heatmap, status and metrics only;
- replay with navigation and prominent `Verified OK`/`TAMPERED`;
- idempotent durable JSON report dispatch record.

## Artifact families

| Family | Cardinality | Core linkage |
|---|---:|---|
| Declaration | one per series/group | game UID, identities, repos/commits, Step-0, config/scent/schedule digests |
| Played config | one per sub-game | exact bytes/digest, role assignment, schema/version |
| Sub-game log | one per sub-game/group | ordered commitments/reveals/events/nonces-after-audit/findings |
| Final result | one per series/group | six outcomes/scores/tokens, totals, winner/tie, audit and agreement digests, report metadata |

## Invariants

1. Artifact IDs/filenames are sanitized, unique, and confined under the configured root.
2. Writes are atomic; live journal is append-only; finalization is immutable.
3. Schema/version/digest/link validation precedes replay or send.
4. Operational logs never substitute for protocol evidence.
5. Live UI/retrieval receives local-view DTOs with no opponent truth.
6. UI is observational/lifecycle-only and cannot bypass SDK/state machine.
7. Headless mode retains full game capability.
8. Objective replay is unlocked only after final reveal and link/audit validation.
9. Report is an attached standard JSON to the allowlisted address; body cannot replace it.
10. Each group independently sends the same agreed logical result exactly once, with recoverable durable retry.
11. Color is never the sole critical-state channel; keyboard/text alternatives exist.

## Acceptance outline

| ID | Scenario | Planned evidence |
|---|---|---|
| RUR-AC-001 | Crash during each write leaves prior valid artifact or recoverable temp, never partial accepted JSON. | fault tests |
| RUR-AC-002 | Traversal, collision, wrong UID/digest/version, corrupt/truncated/oversized artifacts fail closed. | security corpus |
| RUR-AC-003 | Live GUI/log/prompt/screenshot contains no opponent truth or pre-audit nonce. | privacy tests |
| RUR-AC-004 | Headless and GUI runs produce the same domain/protocol evidence for same inputs. | differential test |
| RUR-AC-005 | Replay navigation never bypasses verification and clearly reports tamper. | UI/integration test |
| RUR-AC-006 | Gmail scope/destination/attachment are exact; free-text substitute and arbitrary recipient fail. | contract tests |
| RUR-AC-007 | Restart/429/timeout/retry preserves one logical report with visible pending/failed state. | outbox fault tests |
| RUR-AC-008 | Keyboard, contrast, scaling, text alternatives, status, errors, confirmation and recovery pass review. | SCREENSHOT/MANUAL |

## Finalization checklist

- four JSON schemas, filenames, atomicity and digest graph;
- journal/finalization permissions and retention;
- live-view DTO and complete forbidden-field list;
- GUI screens, states, threading, error/recovery and accessibility specification;
- replay verification/navigation state machine;
- OAuth/outbox/idempotency/allowlist contract;
- screenshot and deterministic sample-run procedure.

