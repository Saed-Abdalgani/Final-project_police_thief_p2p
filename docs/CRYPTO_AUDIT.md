# Commit-Reveal and Mutual Audit

Protocol `0.5.0` binds every outcome-relevant action before dependent disclosure
and reconstructs the game without a central judge.

## Evidence graph

```text
shared config ─┐
scent policy ──┼─> signed Step-0 declarations
role schedule ─┘              │
                              v
local pre-state -> commitment body + fresh nonce -> SHA-256 commitment
                              │                         │
                              ├─ acknowledgement lock ──┤
                              └─ live reveal (no nonce) ┘
                                             │
event journal hash chain --------------------┤
capture claim/response commitments ----------┤
final nonce manifest ------------------------┘
                                             v
             independent deterministic replay/audit reports
                                             │
                              manifest + result agreement
```

## Verification order

1. Recompute the shared constitution, scent-model, and role-schedule digests.
2. Verify both Step-0 HMACs, clean counted commits, and exact bindings.
3. Verify journal chain/coverage and final-manifest identity/linkage.
4. Enforce unique global/actor order and nonce uniqueness.
5. Recompute every commitment from its final body and nonce.
6. Compare the local pre-state and scent-frame digests.
7. Replay the action through domain legality and compare public effects.
8. Resolve capture/terminal truth and fixed sub-game/series scores.
9. Compare independent manifest/report digests before reporting.

The auditor is pure: it imports no adapter, network, GUI, clock, persistence, or
randomness. Any mismatch yields `TAMPERED` and zero points.

## Reproducible evidence

```text
uv run pytest tests/contract/test_crypto_contracts.py -q
uv run pytest tests/unit/test_crypto_primitives.py -q
uv run pytest tests/unit/test_step_zero_and_evidence.py -q
uv run pytest tests/integration/test_mutual_audit.py -q
uv run pytest tests/integration/test_dual_process_mcp.py -q
```

The dual-process campaign sends real commitment digests, nonce-free live
reveals, final nonce manifest, audit report, and result agreement through each
isolated localhost FastMCP peer in both startup orders.
