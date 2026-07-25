# Assumption Register

**Baseline:** `1.0.0`
**Owner of register:** Architecture Lead
**Review cadence:** at every milestone gate and whenever a source, protocol, schema, or competition condition changes.

An assumption is not permission to weaken a requirement. If validation fails, the owner opens an ambiguity or ADR, updates PRD/PLAN/TODO, and blocks dependent work until the change is approved.

## 1. Hard constraints carried from PRD 8.1

These are constraints, not hypotheses. Their validation date records the last source review.

| ID | Constraint | Owner | Validation method | Last validated | Status |
|---|---|---|---|---|---|
| CON-001 | Python dependencies use `uv` only. | Engineering Lead | Tooling and CI audit | 2026-07-25 | Confirmed by SRC-002 |
| CON-002 | Each live peer runs in an independent process. | Architecture Lead | Process-isolation integration test | 2026-07-25 | Confirmed by SRC-001 |
| CON-003 | League peers run on separate machines through public tunnel URLs. | Operations Lead | Remote dress rehearsal | 2026-07-25 | Confirmed by SRC-001 |
| CON-004 | Police and Thief are submitted as two standalone GitHub repositories. | Release Lead | Clean-clone verification of both exports | 2026-07-25 | Confirmed by SRC-001 |
| CON-005 | Both repositories are lecturer-accessible and cross-link each other. | Submission Owner | Access/link review | 2026-07-25 | Confirmed by SRC-001 |
| CON-006 | Shared match configuration is byte-identical and cryptographically locked. | Protocol Lead | Digest negotiation tests | 2026-07-25 | Confirmed by SRC-001 |
| CON-007 | Movement is one orthogonal cell or `STAY`. | Domain Lead | Property and contract tests | 2026-07-25 | Confirmed by SRC-001 |
| CON-008 | Natural-language hints are the only legal deception channel. | Strategy Lead | Protocol and prompt-output tests | 2026-07-25 | Confirmed by SRC-001 |
| CON-009 | Competitive mode cannot replace verbal hints with a numeric position protocol. | Strategy Lead | Schema and adversarial tests | 2026-07-25 | Confirmed by SRC-001 |
| CON-010 | Nonces remain secret until final audit. | Security Lead | Log scan and protocol tests | 2026-07-25 | Confirmed by SRC-001 |
| CON-011 | Gmail OAuth uses send-only scope. | Security Lead | OAuth manifest/token-scope review | 2026-07-25 | Confirmed by SRC-001 |
| CON-012 | Reports are attached standard JSON, never a free-form substitute. | Reporting Lead | Artifact schema and dry-run tests | 2026-07-25 | Confirmed by SRC-001 |
| CON-013 | Every group independently sends its own agreed result. | League Owner | Result agreement and outbox evidence | 2026-07-25 | Confirmed by SRC-001 |

## 2. Engineering assumptions carried from PRD 8.2

| ID | Assumption | Owner | Validation and trigger | Validate by | Status |
|---|---|---|---|---|---|
| ASM-001 | One canonical development workspace can deterministically export two independent role repositories. | Release Lead | Build both exports and compare manifests; trigger before M12 rehearsal | M13 entry | Open-validating |
| ASM-002 | Both releases may share reviewed source at export time while remaining independently installable and sharing no live state. | Architecture Lead | Clean-clone and process-isolation tests | M13 entry | Open-validating |
| ASM-003 | FastMCP `3.4.3` or a deliberately tested compatible release supports the required server/client and transport behavior. | Protocol Lead | Lock version, run contract suite, record compatibility matrix | M3 entry | Open-validating |
| ASM-004 | A public tunnel can carry MCP HTTP and expose a readiness endpoint within competition constraints. | Operations Lead | External bidirectional preflight and fault run | M5 exit | Open-validating |
| ASM-005 | Clock drift exists; sequence numbers and monotonic deadlines are sufficient without wall-clock equality. | Reliability Lead | Skew/fault tests and state-machine review | M5 exit | Open-validating |
| ASM-006 | The agreed config fully defines axes and start cells. | Domain Lead | Schema completeness and golden vectors | M2 exit | Open-validating |
| ASM-007 | Opponent input is hostile until schema, identity, sequence, state, and phase checks pass. | Security Lead | Threat-model and negative protocol tests | M4 exit | Accepted security posture |
| ASM-008 | A deterministic template language provider permits zero-token default play. | Strategy Lead | Six-game offline series and token ledger | M7 exit | Open-validating |
| ASM-009 | A scored league series contains six sub-games despite the public example's demonstration behavior. | Product Owner | Appendix F and league conformance test | 2026-07-25 | Confirmed by SRC-001 |

## 3. Chosen interpretations carried from PRD 8.3

These items are decisions rather than untested assumptions. Their detailed rationale is in `docs/AMBIGUITIES.md`.

| ID | Interpretation | Owner | Revalidation trigger | Last validated |
|---|---|---|---|---|
| INT-001 | A Police barrier on its own cell is engine-legal; strategy treats it as a terminal self-block risk. | Domain Lead | Rule or config revision | 2026-07-25 |
| INT-002 | `STAY` does not prevent enclosure capture when there is no legal spatial escape. | Domain Lead | Rule or scoring revision | 2026-07-25 |
| INT-003 | The exact normalized 5x5 radial scent kernel and numeric example are signed match terms. | Belief Lead | Kernel/schema revision | 2026-07-25 |
| INT-004 | Commitments seal versioned canonical JSON containing every outcome-relevant field. | Security Lead | Protocol/schema revision | 2026-07-25 |
| INT-005 | Transport is at-least-once; application effects are exactly once. | Reliability Lead | Transport revision | 2026-07-25 |
| INT-006 | Recovery resumes only from mutually acknowledged checkpoints. | Reliability Lead | Recovery/state-machine revision | 2026-07-25 |
| INT-007 | LLM movement is disabled unless both peers sign the capability. | Strategy Lead | Capability schema revision | 2026-07-25 |
| INT-008 | Live UI controls lifecycle; autonomous policy chooses moves. | UX Lead | UI authority revision | 2026-07-25 |
| INT-009 | Objective replay view is available only after final reveal in the offline verifier. | Security Lead | Replay/privacy revision | 2026-07-25 |

## 4. Closure rules

- `Confirmed` means a normative source settled the item.
- `Accepted security posture` means the project intentionally assumes the hostile case.
- `Open-validating` is allowed during implementation only when the named milestone has not reached its exit gate.
- `Invalidated` blocks every dependent task until PRD, PLAN, TODO, ADRs, tests, and compatibility versions are reconciled.
- Assumptions may not be silently converted into requirements or vice versa.

