# M0 Formal Consistency and Approval Review

**Review date:** 2026-07-25
**Candidate baseline:** `1.0.0`
**Reviewed artifacts:** SRC-001/SRC-002, PRD, PLAN, TODO, M0 governance documents, and seven mechanism PRD outlines
**Technical reviewer:** Codex acting as Principal Engineer, QA Lead, and Security Reviewer under the user's execution instruction
**Decision:** `APPROVED FOR M1 ENTRY`

This approval means the specification/governance gate is complete enough to begin M1. It is not a claim that the software, league candidate, or submission is `READY`.

## 1. Mechanical audit results

| Check | Expected | Result | Status |
|---|---:|---:|---|
| Physical PDF page coverage | pages 1-160 once each | 160, no gap/overlap | Pass |
| Appendix E rule IDs | `E-001..E-055` | 55 unique | Pass |
| Appendix E source rule numbers | `1..55` | 55 unique | Pass |
| Appendix F quantitative rows | physical pages 152-155 | 32 unique keys | Pass |
| PRD requirement declarations | unique FR/NFR IDs | 227, no duplicate declaration | Pass |
| Expanded requirement mappings | exact PRD set | 227, no missing/extra/duplicate | Pass |
| Requirement component owners | component exists in PLAN | 227/227 | Pass |
| Requirement TODO links | at least one valid task anchor | 227/227 | Pass |
| Requirement evidence types | allowed controlled type | 227/227 | Pass |
| TODO IDs | `T001..T645` | 645 unique, sequential | Pass |
| Mechanism PRD outlines | 7 named files | 7/7 | Pass |

Validation was executed against the current files using PowerShell parsing of requirement declarations, traceability ranges, rule/parameter rows, PLAN component names, TODO IDs, and page-range coverage. The validator exited successfully.

## 2. PRD/PLAN/TODO consistency checklist

| Area | Review question | Finding |
|---|---|---|
| Authority | Do all documents apply root engineering rules and PDF precedence identically? | Yes; `docs/SOURCES.md` is canonical and PRD examples match it. |
| Product boundary | Do all documents describe two symmetric isolated peers with local truth and no central judge? | Yes. |
| SDK | Is every adapter/integration constrained to `SimulationSdk`? | Yes; ADR-001, PLAN components, mechanism PRDs, and tasks agree. |
| Architecture | Are dependency direction and responsibilities unambiguous? | Yes; ADR-002 and PLAN component table name primary owners. |
| Gatekeeper | Are all external API calls centrally bounded/configured? | Yes; PRD, PLAN, tunnel/reporting PRDs, and tasks agree. |
| Configuration | Are JSON/TOML precedence, Appendix F status semantics, and canonical bytes consistent? | Yes. |
| Domain | Are movement, barriers, enclosure, terminal order, and fixed scores consistently represented? | Yes, including the `STAY` interpretation. |
| Local truth | Are forbidden live objective fields and permitted post-audit replay separated? | Yes; standalone invariants and privacy evidence exist. |
| Protocol | Are at-least-once delivery and exactly-once effects consistent with recovery? | Yes; ADR-005 and MCP PRD agree. |
| Cryptography | Are nonce, canonicalization, SHA-256, reveal order, and audit boundaries consistent? | Yes; ADR-004 and crypto PRD agree. |
| Strategy | Are advanced policies subordinate to legality, deadlines, privacy, and reliability? | Yes. |
| Language/scent | Are kernel signing, hint bounds, zero-token default, and LLM exception consistent? | Yes. |
| Artifacts/reporting | Are four artifact families, JSON attachment, independent sends, and send-only OAuth consistent? | Yes. |
| UI/replay | Is live local truth distinct from verified offline objective replay? | Yes. |
| League/release | Are counted ledger, six balanced games, two repositories, tags, and access requirements aligned? | Yes. |
| Milestones | Do PRD, PLAN, and TODO use the same M0-M13 identities/outcomes? | Yes after correction D-002. |
| Acceptance/evidence | Does every requirement have planned evidence and do KPIs have units/sources? | Yes. |
| Security | Does the initial threat model cover remote trust boundaries and secret/path/DOS concerns? | Yes; controls await implementation evidence. |

## 3. Discrepancies found and resolved

| ID | Severity | Original discrepancy | Resolution | Files |
|---|---|---|---|---|
| D-001 | P0 | PRD listed `scoring.technical_loss` as a sixth Appendix F scoring parameter, but rendered physical page 154 contains five scoring rows. | Removed it from the Appendix F table and retained zero technical/tamper behavior as a mandatory typed outcome requirement. Traceability now has the exact 32 source parameters. | PRD, TRACEABILITY |
| D-002 | P0 | PRD/PLAN used older M0-M10 labels while executable TODO uses M0-M13; equal IDs referred to different scopes. | Normalized PRD and PLAN to the TODO M0-M13 structure and exit outcomes. | PRD, PLAN |
| D-003 | P1 | Several requirement families lacked an explicitly named accountable PLAN component (configuration, league, reporting, observability, experiments, release/CI policy). | Added single-responsibility planned components and mapped all 227 requirements. | PLAN, TRACEABILITY |
| D-004 | P1 | Initial planned documentation trees did not enumerate the M0 governance artifacts. | Added all M0 documents to PRD deliverables and PLAN file structure. | PRD, PLAN |

All four discrepancies are closed. No unresolved P0 specification issue remains.

## 4. M0 deliverable review

- Source checksum, version, path, authority, reference revision, and 160-page map are recorded.
- All 55 Appendix E rules and all 32 Appendix F quantitative rows have owners, task anchors, and evidence.
- Assumptions, ambiguities, vocabulary, RACI, change control, severity, classifications, retention, and architecture invariants are approved.
- Threat model, risk register, KPIs, evidence policy, baselines, split policy, and experiment manifest are actionable.
- ADR-001..005 are Accepted with consequences and verification.
- All seven mechanism PRD outlines contain scope, inputs, outputs, invariants, acceptance cases, and finalization gates.
- Academic integrity, two-repository release, counted ledger, and final readiness rubric are explicit.
- The baseline version and changes are recorded in `CHANGELOG.md`.

## 5. Conditions for implementation

M1 may begin. Later implementation remains governed by these conditions:

1. The owning mechanism PRD must be finalized before its corresponding code milestone.
2. Tests are written with or before public behavior where practical.
3. Only `uv` commands manage/run the Python environment.
4. No milestone closes on narrative claims; retained evidence is required.
5. Any new P0 ambiguity, source discrepancy, or incompatible contract change reopens M0 change control for the affected scope.

## 6. Approval record

| Role | Decision | Date | Scope |
|---|---|---|---|
| Architecture | Approve | 2026-07-25 | boundaries, components, ADRs, milestone alignment |
| QA | Approve | 2026-07-25 | traceability completeness, evidence policy, mechanical audit |
| Security | Approve with implementation verification pending | 2026-07-25 | threat/control design sufficient for M1; no control claimed implemented |
| Product/specification | Approve | 2026-07-25 | authority, rules, parameters, assumptions, ambiguities |

Baseline freeze: documentation `1.0.0`, approved for M1 entry on 2026-07-25.

