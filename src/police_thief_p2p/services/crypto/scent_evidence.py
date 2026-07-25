"""Signed scent-model identity for audit-bound commitments."""

from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.scent import KERNEL_TEXT, ScentPolicy


def scent_model_digest(policy: ScentPolicy) -> str:
    """Bind the exact formula, kernel, decimal, and decay policy."""
    return sha256_digest(
        {
            "formula": "center_intensity * kernel_weight",
            "kernel": KERNEL_TEXT,
            "center_intensity": str(policy.center_intensity),
            "decay": str(policy.decay),
            "decimal_places": policy.decimal_places,
            "rounding": policy.rounding.value,
            "numeric_example": {
                "center": str(policy.quantize(policy.center_intensity)),
                "after_full_turn": str(policy.after_full_turn(policy.center_intensity)),
            },
        }
    )
