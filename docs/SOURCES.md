# Source and Authority Ledger

**Project:** Distributed Cops-and-Robbers over a Peer-to-Peer Network
**Documentation baseline:** `1.0.0`
**Ledger reviewed:** 2026-07-25

## 1. Precedence

When two sources conflict, the project shall resolve the conflict in this order:

1. The root `system prompt.txt` controls engineering process, architecture, quality, security, tooling, and readiness claims.
2. Appendix F of the supplied PDF controls every quantitative value and its `Fixed`, `Minimum`, or `Negotiable` status.
3. Appendix E of the PDF controls its 55 enumerated behavioral and submission rules.
4. Other text explicitly marked mandatory in the PDF controls the applicable behavior.
5. A mutually signed `config/game.json` controls a particular match only within the preceding rules; it may not weaken a fixed rule or a minimum protection.
6. `docs/PRD.md`, accepted ADRs, and the other baseline documents control implementation choices left open by the book.
7. The public reference repository and all examples are informative. They never override the PDF.

If an unresolved P0 conflict remains, implementation of the affected behavior is blocked. The conflict must be entered in `docs/AMBIGUITIES.md`, resolved in an ADR, and linked from the PRD before work resumes.

## 2. Source ledger

| ID | Source | Version / revision | Integrity / location | Authority | Use |
|---|---|---|---|---|---|
| SRC-001 | Supplied rules book, *Distributed Cops-and-Robbers over a Peer-to-Peer Network* | Book `3.0.0`; example code `3.0.0`; generated 2026-07-12 | SHA-256 `7C9E1D7527582C3AEF9AFD71709981CEA50EA60B8FABEFE85EFCCAB0A5FDD02E`; 160 A4 pages; `C:\Users\saedn\Desktop\AI Agents orchestration\police_thief_p2p.pdf` | Normative according to the precedence above | Product, protocol, league, integrity, reporting, and submission requirements |
| SRC-002 | Root engineering authority | Current workspace revision | `C:\Users\saedn\Desktop\AI Agents orchestration\Final project_police_thief_p2p\system prompt.txt` | Normative for engineering execution | SDK boundary, Gatekeeper, `uv`, testing, security, documentation, and final readiness |
| SRC-003 | Public example repository | Inspected commit `960499fd5e8777b4929625f5d8fdcf2ab4677b54` | `https://github.com/rmisegal/Game-P2P-Cop-Chase` | Informative only | Learning, interoperability comparison, and attribution; no blind runtime reuse |
| SRC-004 | Product Requirements Document | Baseline `1.0.0` | `docs/PRD.md` | Normative project interpretation after SRC-001/SRC-002 | Stable requirements and acceptance criteria |
| SRC-005 | Architecture and Project Plan | Baseline `1.0.0` | `docs/PLAN.md` | Normative architecture after accepted ADRs | Components, boundaries, sequence, verification |
| SRC-006 | Execution backlog | Baseline `1.0.0` | `docs/TODO.md` | Normative execution order | Task ownership, gates, and evidence |

The source PDF is intentionally outside the repository working root. Implementations and reviews shall refer to SRC-001 by checksum, not merely by filename.

## 3. Reproducible verification

PowerShell:

```powershell
$pdf = 'C:\Users\saedn\Desktop\AI Agents orchestration\police_thief_p2p.pdf'
Get-FileHash -Algorithm SHA256 -LiteralPath $pdf
pdfinfo $pdf
```

Expected SHA-256:

```text
7C9E1D7527582C3AEF9AFD71709981CEA50EA60B8FABEFE85EFCCAB0A5FDD02E
```

Expected page count: `160`.

## 4. Physical PDF page map

Page numbers in this table are physical PDF pages. The book's printed Arabic page 1 begins at physical page 17.

| Physical pages | Printed pages | Topic |
|---:|---:|---|
| 1 | cover | Title, copyright, book version, example-code version |
| 2 | ii | Abstract |
| 3 | iii | Personal introduction |
| 4 | iv | Binding rules versus illustrative material; Appendix F supremacy for quantitative values |
| 5 | v | General guidance, conflict handling, book structure, keywords |
| 6-11 | vi-xi | Table of contents |
| 12-13 | xii-xiii | List of figures |
| 14-15 | xiv-xv | List of tables |
| 16 | xvi | Front-matter spacer |
| 17-23 | 1-7 | Chapter 1 - theoretical framework, orchestration, Dec-POMDP, uncertainty |
| 24-32 | 8-16 | Chapter 2 - decentralized P2P architecture, MCP/FastMCP, tunneling and isolation |
| 33-39 | 17-23 | Chapter 3 - board physics, movement, barriers, terminal outcomes, scoring |
| 40-47 | 24-31 | Chapter 4 - dynamic pheromones, emission, decay, scent tactics |
| 48-56 | 32-40 | Chapter 5 - security, SHA-256 Commit-Reveal, mutual audit, Step-0 |
| 57-68 | 41-52 | Chapter 6 - strategy, belief, heuristics, optional RL and LLM integration |
| 69-76 | 53-60 | Chapter 7 - live GUI, local truth, replay, integrity verification |
| 77-84 | 61-68 | Chapter 8 - agent architecture, Orchestrator, state machine, deadlines, Watchdog |
| 85-98 | 69-82 | Chapter 9 - league, computational fairness, Gmail reporting, GitHub submission |
| 99-106 | 83-90 | Chapter 10 - seven development priorities and milestone discipline |
| 107-115 | 91-99 | Chapter 11 - synthesis, success metrics, pre-submission checklist, outlook |
| 116-119 | 100-103 | References |
| 120-125 | 104-109 | Appendix A - Gmail API and OAuth 2.0 setup |
| 126-132 | 110-116 | Appendix B - shared JSON constitution and private TOML configuration |
| 133-137 | 117-121 | Appendix C - GitHub repository, academic README, and submission checklist |
| 138-141 | 122-125 | Appendix D - example repository, layout, execution, and permitted use |
| 142-150 | 126-134 | Appendix E - mandatory rules, prohibitions, recommendations, and cross-check additions |
| 151-159 | 135-143 | Appendix F - binding parameters, statuses, mandatory files/addresses, language modes, strategy selectors |
| 160 | end | End-of-book page |

Coverage assertion: the union of the physical page ranges above is exactly `1..160`, with no gaps or overlaps.

## 5. Reference-code handling

SRC-003 may be read to understand intent, public names, or expected interoperability. Any reused fragment must be:

- legally permitted;
- minimal and attributed in the file and `CREDITS.md`;
- reviewed against SRC-001 and the current architecture;
- covered by project-owned tests;
- free of imported defects, secrets, hidden state sharing, or obsolete parameters.

Copying the example runtime as the submission architecture is prohibited. The PDF and this project's accepted decisions win every conflict.

