# M11 Cryptographic Design Review

**Scope:** entropy, canonicalization, key handling, nonce lifecycle, replay
context, and sanctions in candidate `0.10.0`
**Review date:** 2026-07-26
**Decision:** PASS — no open P0/P1 finding

## Findings

Entropy comes from the operating-system CSPRNG through the injected entropy
boundary. Strategy/experiment seeds cannot reach nonce generation. Nonces have
at least 128 bits, are bound to one commitment identity, are rejected on reuse,
and remain sealed until the final-reveal phase.

Commitments hash versioned canonical JSON containing the complete game,
sub-game, step, role, action/effect, state, scent, strategy, and nonce context.
Unicode normalization, key ordering, duplicate-key rejection, integer-only
numeric representation, field mutation, order mutation, and context
substitution are covered by golden/property/mutation tests.

Signing keys are caller-owned and are not retained by the SDK. OAuth credentials
are unrelated to game signing and remain behind the send-only reporting
boundary. No key, nonce, token, raw prompt, or opponent truth is admitted to
structured logs or pre-audit public DTOs.

Acknowledgement locks the exact digest before live reveal. Final reveal requires
the legal protocol phase and discloses the nonce graph only for offline mutual
verification. Replay independently recomputes commitment bytes, reveal identity,
state transitions, scent evidence, capture answers, terminal reason, and scores.

Invalid commitments/reveals, nonce reuse, corrupt/gapped journals, forged
capture/results, and peer audit disagreement fail closed into typed tamper or
technical outcomes. No code path awards a score from unverified evidence.

## Residual design limits

SHA-256 commitments are not encryption and do not authenticate an internet
endpoint by themselves. Concealment depends on nonce secrecy until final reveal;
peer identity depends on negotiated/signed Step-0 material and the configured
tunnel trust boundary. These are documented operational constraints, not open
implementation defects.
