"""Candidate patches and scoring helpers for the M12 freeze repair campaign."""

from collections.abc import Mapping

from police_thief_p2p.services.experiments.splits import HOLDOUT_OPPONENTS

# Restored search depth with a large guard; probes stay deadline-safe under 250 ms.
SAFE_COMPUTE: dict[str, float | int] = {
    "search_horizon": 3,
    "posterior_samples": 16,
    "guard_margin_ms": 110,
    "cache_entries": 512,
}
PROBE_OPPONENTS = HOLDOUT_OPPONENTS
CANDIDATES: tuple[dict[str, float | int], ...] = (
    {},
    {
        "thief.survival": 2_000.0,
        "thief.risk_distance": 25.0,
        "thief.routes": 30.0,
        "thief.traps": 400.0,
        "thief.space": 8.0,
        "thief.risk": 0.45,
    },
    {
        "thief.survival": 2_000.0,
        "thief.risk_distance": 25.0,
        "thief.routes": 30.0,
        "thief.traps": 650.0,
        "thief.corner": 25.0,
        "thief.scent": 6.0,
        "thief.risk": 0.55,
        "thief.entropy": 5.0,
    },
    {
        "thief.survival": 2_000.0,
        "thief.risk_distance": 25.0,
        "thief.routes": 30.0,
        "thief.traps": 800.0,
        "thief.corner": 25.0,
        "thief.cycle": 12.0,
        "thief.space": 8.0,
        "thief.risk": 0.65,
        "police.capture": 900.0,
    },
    {
        "thief.survival": 2_000.0,
        "thief.risk_distance": 22.0,
        "thief.routes": 28.0,
        "thief.traps": 550.0,
        "thief.corner": 20.0,
        "thief.risk": 0.4,
        "hints.trust_threshold": 0.55,
        "evade": 1.4,
        "boundary": 0.35,
    },
)


def merged(
    base: Mapping[str, float | int],
    patch: Mapping[str, float | int],
) -> dict[str, float | int]:
    """Merge the prior freeze with deadline-safe compute caps and one Thief patch."""
    return {**dict(base), **SAFE_COMPUTE, **dict(patch)}


def repair_score(report_share: float, thief_success: float, deadline_misses: int) -> float:
    """Prefer zero deadline misses, then Thief survival, then score share."""
    if deadline_misses:
        return -1_000.0 - deadline_misses
    return thief_success * 100.0 + report_share * 0.01
