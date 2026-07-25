# Mechanism PRD - Language, Scent, and Bayesian Belief

**Status:** M6 frozen and approved
**Owner:** Belief Lead with Strategy Lead
**Protocol:** `0.6.0`
**Requirements:** FR-BEL-001..015, FR-STR-010..017
**Rules/parameters:** Appendix E 23, 25-27; F-007, F-008, F-013..F-015, F-024

## Scope and privacy boundary

Each peer emits scent from its own post-action local position and estimates the
opponent from commitment-linked scent plus bounded semantic hints. During live
play no component receives, requests, logs, serializes, or displays the opponent's
true position. The actor's path and unquantized scent history are private durable
state. They become audit input only after terminal final reveal.

The live data flow is:

```text
own post-action state -> private exact scent field -> digested ScentFrame
opponent ScentFrame + nonce-free reveal -> verified evidence
prior -> motion prediction -> legal mask -> scent -> bounded hint -> posterior
```

There is no SDK operation for setting a belief, injecting arbitrary scent, or
supplying opponent truth. `update_belief_from_reveal` is the sole live observation
entry point and requires a frame whose identity, model digest, and frame digest
match the revealed commitment.

## Normative scent model

The signed scalar parameters are:

- center intensity `I = 0.9`;
- decay fraction `d = 0.10`;
- cell range `[0, 1]`;
- 6 boundary decimal places using `ROUND_HALF_EVEN`.

The exact radial kernel `K` is:

```text
0.0625  0.125  0.25  0.125  0.0625
0.125   0.25   0.5   0.25   0.125
0.25    0.5    1     0.5    0.25
0.125   0.25   0.5   0.25   0.125
0.0625  0.125  0.25  0.125  0.0625
```

For an actor at canonical cell `(r,c)`, one emission updates every on-board
offset `(i,j)` in `[-2,2]²`:

```text
S'[r+i,c+j] = min(1, S[r+i,c+j] + I * K[i+2,j+2])
```

Off-board targets are discarded, never wrapped or renormalized. Barriers do not
block scent. A MOVE or STAY emits once from the resulting local position; BARRIER
does not emit. Repeated and overlapping emissions accumulate before clamping.

One full Police-plus-Thief turn has this exact order:

1. scheduled Police MOVE/STAY emission;
2. scheduled Thief MOVE/STAY emission;
3. after both scheduled actions complete, every private field applies
   `S'' = S' * (1-d)` exactly once.

No half-turn, duplicate-turn, or out-of-order decay is allowed. The center of one
fresh emission is `0.900000`; after one complete turn it is `0.810000`. The outer
corner is `0.056250`, then `0.050625`. Normative center, edge, corner, overlap,
repeated-stay, and decay vectors are in
`data/conformance/scent/emission_decay.json`.

## Numeric interoperability

Internal scent arithmetic uses finite base-10 `Decimal` values with at least 28
digits of context precision. Emission, accumulation, clamp, and decay do not
round. Values are quantized only while creating wire/audit cells. Cells serialize
as plain fixed-point decimal strings with exactly six places; exponent notation,
NaN, and infinity are forbidden.

Belief arithmetic uses finite binary `float` in log space. A grid is accepted only
when all values are non-negative, masked cells are zero, and `math.fsum` is within
absolute tolerance `1e-12` of one. Audit/diagnostic belief serialization uses
row-major fixed-point strings with 12 decimal places; it is not fed back into the
live posterior.

## Scent frame and commitment linkage

`scent_frame.schema.json` defines a sparse frame with:

- frame version, canonical game UUID, sub-game, actor step, and actor role;
- equal bounded board dimensions;
- exact negotiated scent-model SHA-256;
- at most 2,048 unique, in-bounds cells with decimal-string values in `[0,1]`;
- SHA-256 of all preceding canonical frame fields.

The frame digest is included in the step commitment before acknowledgement.
Reception compares game, sub-game, step, actor, model digest, and frame digest
using exact/constant-time digest comparison. Dimensions must also equal the local
belief board. Any mismatch rejects the entire observation without mutation.

## Prior and prediction

The initial prior is uniform over the opponent start's publicly reachable
connected component. Public barriers and cells proven unreachable are masked to
zero. A topology change remasks and renormalizes before prediction.

The baseline transition is uniform over every legal orthogonal move plus STAY, so
each source row sums to one. The advanced injectable mixture scores the same legal
targets with bounded chase/evade distance delta, boundary, revisit, and two-cycle
features. Scores are clipped before exponentiation and normalized per source.
Prediction distributes all prior mass through those legal rows.

## Observation likelihood and Bayesian fusion

For cell `x`, scent likelihood is:

```text
L_scent(x) = epsilon + observed_scent(x), epsilon = 1e-6 by default
```

The configurable floor must be strictly between zero and one. Missing cells
therefore remain possible, while a signed strong peak dominates contradictory
language.

The deterministic hint parser recognizes only one coarse category: north, south,
east, west, center, edge, corner, or neutral. More than the negotiated word cap,
multiple categories, digits, coordinates, URLs, protocol/tool terms, prompt
instructions, malformed text, or unrecognized locale text produce neutral
all-one likelihoods. The parser returns semantic likelihoods only—never an
action, command, provider call, coordinate, or configuration change.

Each category owns an independent `Beta(2,2)` reliability prior. Consistent
post-audit evidence increments alpha; inconsistent evidence increments beta.
At live step `t`, its mean shrinks toward `0.5` by `0.95^age`. No hidden verdict
or live truth updates reliability. Raw hint ratios are capped to `[1/C,C]`, with
default `C=3`, then tempered by the category mean.

The posterior is computed in log space:

```text
log w(x) = log prediction(x) + log L_scent(x) + log L_hint(x)
P(x) = exp(log w(x) - max(log w)) / sum(exp(...))
```

Masked cells never enter the calculation. If no finite weight remains, the
deterministic remasked predicted prior is used; if no legal cell exists, the
update fails rather than fabricating a location.

## Diagnostics and offline calibration

Every update returns the full immutable grid plus entropy in bits, peak
probability, deterministic minimum credible region for a configurable cumulative
target, fallback flag, and hint category. Row-major coordinate ordering breaks
ties. The most-likely cell is explicitly diagnostic; advanced policy receives the
full grid.

`LocalView` exposes own position, public barriers, quantized belief heatmap,
entropy, peak, credible region, and diagnostic argmax. Its schema forbids opponent
truth fields. Brier score, log loss, and top-one accuracy accept revealed
positions only in the offline post-audit module.

## Acceptance

| ID | Frozen evidence |
|---|---|
| LSB-AC-001 | Two independent SDKs reproduce identical frame JSON/digest and posterior digest. |
| LSB-AC-002 | Golden center/edge/corner/overlap/repeat/decay vectors and turn-order tests pass. |
| LSB-AC-003 | Extreme, contradictory, long-run, and all-zero cases remain finite and normalized. |
| LSB-AC-004 | Barriers/impossible cells stay zero through topology changes and prediction. |
| LSB-AC-005 | Category-isolated Beta/recency math passes without live truth feedback. |
| LSB-AC-006 | Coordinate/protocol/injection-like and ambiguous hints are neutral. |
| LSB-AC-007 | Source, DTO, SDK, schema, and log scans expose no live opponent truth. |
| LSB-AC-008 | 35-step minimum/expanded board p95 measurements satisfy the stored gate. |
