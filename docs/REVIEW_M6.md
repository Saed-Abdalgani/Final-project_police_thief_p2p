# M6 Scent and Bayesian Belief Review

- **Review date:** 2026-07-25
- **Milestone:** M6 - Scent and Bayesian belief
- **Current decision:** `READY`

## Rule and requirement review

- [x] E-008 exposes belief only through `LocalView`: own truth, public topology,
  heatmap, entropy, peak, credible region, and diagnostic argmax.
- [x] E-009 forbids an objective live board: scent DTOs, SDK signatures, service
  sources, schemas, and live views contain no opponent true-position field.
- [x] E-023 binds the exact kernel, center, decay, numeric example, rounding,
  model digest, frame digest, and protocol identity before dependent disclosure.
- [x] FR-BEL-001..007 implement post-MOVE/STAY emission, no BARRIER emission,
  exact clipping/accumulation/clamp/turn decay, reveal gating, and offline replay.
- [x] FR-BEL-008..015 implement normalized masked beliefs, prediction-first
  fusion, bounded hints, deterministic fallback, full-grid policy input,
  diagnostics, and post-audit-only calibration.

## Numeric, privacy, and architecture review

- [x] ADR-014 freezes exact Decimal scent arithmetic with no internal rounding,
  six-place `ROUND_HALF_EVEN` wire values, and `1e-12` belief normalization.
- [x] Center, edge, corner, overlap, repeated-stay, and decay vectors are
  committed under `data/conformance/scent/` and reproduced by independent SDKs.
- [x] Own unquantized scent/path history persists atomically across restart in an
  injected private repository and has no live SDK read operation.
- [x] Scent frames are sparse/bounded, canonical-digested, schema-valid, and
  matched to game, sub-game, actor step, actor, dimensions, model, and reveal.
- [x] Final audit reconstructs accumulated post-action fields and exact
  Police-plus-Thief turn decay before accepting each committed frame digest.
- [x] `BeliefGrid` is immutable, finite, non-negative, masked, deterministic, and
  normalized over reachable legal cells.
- [x] Uniform and mixture motion models use only legal/public/local features and
  conserve transition mass.
- [x] Semantic hint evidence is finite, positive, dimension-bound, ratio-capped,
  category-isolated, recency-aware, and incapable of issuing commands.
- [x] Fusion is log-space and recovers the reachable predicted prior without NaN
  when evidence degenerates.
- [x] Calibration truth enters only the offline module after final audit.

## Verification evidence

- **Full suite:** 345 tests passed with 93.92% branch-aware global coverage.
- **Interop:** independent SDK instances produced byte-identical frame JSON,
  identical SHA-256, and identical posterior digest.
- **Performance:** 25 samples of 35 updates measured p95 `146.068 ms` on 7x7 and
  `503.546 ms` on 15x15; both pass stored gates.
- **Contracts:** all packaged Draft 2020-12 schemas and positive/negative scent
  frame and belief-summary fixtures pass.
- **Static/quality:** Ruff, strict mypy, structure, traceability, import-boundary,
  CI-workflow, and 150-code-line source gates pass.

## Sign-off

Engineering review sign-off: Codex, 2026-07-25. The M6 exit gate and T266-T310
are satisfied with no unresolved P0/P1 finding.
