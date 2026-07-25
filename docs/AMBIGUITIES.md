# Ambiguity and Interpretation Register

**Baseline:** `1.0.0`
**Decision rule:** Appendix F controls numbers; Appendix E and explicitly mandatory text control behavior; unresolved P0 ambiguity blocks implementation.

## 1. Active interpretations

| ID | Topic | Ambiguity | Chosen interpretation | Rationale | Enforcement / evidence | Owner | Status |
|---|---|---|---|---|---|---|---|
| AMB-001 | Barrier on Police cell | The book permits a barrier on the Police current or adjacent cell, but self-placement can make subsequent occupancy semantics surprising. | Placement on the current cell is legal and immediately public. The engine applies the exact rule. The strategy heavily penalizes it and may choose it only if a formally legal terminal benefit is demonstrated. | Preserves mandatory mechanics without inventing a prohibition. | Domain golden vector, legality property test, strategy safety test | Domain Lead | Resolved |
| AMB-002 | `STAY` and enclosure | `STAY` is always in the move set, while the book also declares capture when the Thief has no legal escape. | Enclosure considers legal spatial exits `N/S/E/W`; `STAY` does not negate enclosure. The terminal check runs after relevant public barrier effects and before accepting a survival continuation. | Otherwise enclosure capture is impossible whenever `STAY` exists, contradicting the explicit capture rule. | Enclosure vectors, rule 47 test, scoring test | Domain Lead | Resolved |
| AMB-003 | Scent radial kernel | The 5x5 size and center intensity are fixed, but prose does not provide a single complete interoperable matrix. | A normalized, symmetric, non-negative 5x5 radial kernel is included in signed `game.json` with a signed numeric emission/decay example. Kernel digest equality is a negotiation precondition. | Makes the model deterministic without pretending an illustrative example is normative. | Schema, digest vector, kernel validation, cross-peer conformance | Belief Lead | Resolved |
| AMB-004 | Role alternation | Six games and role balance are mandatory, but exact alternation order is not uniquely prescribed. | The signed series schedule is `P,T,P,T,P,T` for the initiating group and the complement for its opponent. A negotiated alternative is allowed only if each group plays exactly three games per role and the full schedule is digest-bound before game 1. | Deterministic default, balanced roles, no mid-series selection bias. | Schedule schema and balance validator | League Owner | Resolved |
| AMB-005 | Recovery | The book requires Watchdog/reliability but cannot safely infer whether an unacknowledged remote mutation occurred. | Resume only from a mutually acknowledged, durably persisted checkpoint. If checkpoint agreement cannot be proven, terminate with a typed technical outcome and preserve evidence; never invent an acknowledgement or replay a non-idempotent effect. | Safety and auditability are more important than optimistic continuation. | Crash matrix, journal/recovery tests, ADR-005 | Reliability Lead | Resolved |
| AMB-006 | LLM-chosen moves | Movement is algorithmic by recommendation/default, while an exception is discussed. | LLM move selection is disabled by default. It requires an explicit, versioned, mutually signed capability and still passes the deterministic legal-action guard and deadline fallback. | Preserves zero-token operation and interoperability while retaining the documented option. | Config schema, negotiation test, legality/fallback tests | Strategy Lead | Resolved |
| AMB-007 | Commit byte representation | Prose examples may suggest concatenation and do not fully settle escaping and numeric representation. | Hash UTF-8 bytes of versioned canonical JSON: sorted keys, separators `,` and `:`, no insignificant whitespace, NFC strings, JSON booleans/null, finite numbers only, and integer representation where schema says integer. The nonce is a payload field. | Prevents cross-runtime ambiguity and substitution. | ADR-004 and golden byte/hash vectors | Security Lead | Resolved |
| AMB-008 | Gatekeeper `Minimum` status | Appendix F labels request rate/concurrency rows `Minimum`, though their meanings are maximum safe limits. | `Minimum` means minimum protection. Rate and concurrency may become more restrictive; retry delay, assurance, and bounded queue capacity may increase. Shared game-visible changes still require agreement. | Literal numeric increase would weaken DOS protection. | Config validator truth table and ADR note | Security Lead | Resolved |
| AMB-009 | Example values versus Appendix F | Body examples can show values different from Appendix F. | Ignore example numbers for binding behavior. Use Appendix F defaults/statuses and record any deliberate legal negotiation in signed config. | Physical PDF pages 4-5 expressly make Appendix F the sole source for quantitative values. | Source ledger, parameter table, config tests | Product Owner | Resolved |
| AMB-010 | Live manual controls | GUI examples can be read as enabling move selection. | Operator controls start, pause request, safe shutdown, and evidence export only. Policy chooses moves. No GUI event may call a domain service directly. | Maintains autonomous competition and SDK boundary. | UI command map and integration tests | UX Lead | Resolved |
| AMB-011 | Replay truth | A useful replay wants both tracks, which would violate live local truth. | Objective tracks may be reconstructed only after nonce/log reveal and artifact linkage verification, in an offline replay context. | Separates live epistemology from post-game audit evidence. | Privacy test and replay verifier state gate | Security Lead | Resolved |

## 2. Escalation workflow

1. Add a row with the exact source pages and affected requirement IDs.
2. Classify it P0 if it affects legality, scoring, secrets, integrity, league eligibility, or interoperability.
3. Enumerate options and test implications.
4. Apply the authority order in `docs/SOURCES.md`.
5. Record the decision in `docs/DECISIONS.md` when it changes architecture, protocol, schema, security, or cross-repository behavior.
6. Update PRD, PLAN, TODO, mechanism PRD, schemas, and tests atomically.
7. Obtain the approver named by the RACI in `docs/GOVERNANCE.md`.

## 3. Open-issue gate

As of baseline `1.0.0`, there are no unresolved P0 specification ambiguities. Future open P0 rows automatically make the implementation status `NOT READY` for the affected milestone.

