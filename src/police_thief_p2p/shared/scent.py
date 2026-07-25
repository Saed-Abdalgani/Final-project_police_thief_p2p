"""Exact decimal scent-kernel representation and golden calculation."""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from enum import StrEnum

KERNEL_TEXT: tuple[tuple[str, ...], ...] = (
    ("0.0625", "0.125", "0.25", "0.125", "0.0625"),
    ("0.125", "0.25", "0.5", "0.25", "0.125"),
    ("0.25", "0.5", "1", "0.5", "0.25"),
    ("0.125", "0.25", "0.5", "0.25", "0.125"),
    ("0.0625", "0.125", "0.25", "0.125", "0.0625"),
)


class RoundingMode(StrEnum):
    """Supported interoperable decimal rounding modes."""

    HALF_EVEN = "ROUND_HALF_EVEN"


@dataclass(frozen=True, slots=True)
class ScentPolicy:
    """Signed scent emission, decay, and rounding policy."""

    center_intensity: Decimal = Decimal("0.9")
    decay: Decimal = Decimal("0.10")
    decimal_places: int = 6
    rounding: RoundingMode = RoundingMode.HALF_EVEN

    def __post_init__(self) -> None:
        """Reject invalid physical and representation values."""
        if not Decimal("0") <= self.center_intensity <= Decimal("1"):
            raise ValueError("center_intensity must be between zero and one")
        if not Decimal("0") <= self.decay <= Decimal("1"):
            raise ValueError("decay must be between zero and one")
        if not 0 <= self.decimal_places <= 12:
            raise ValueError("decimal_places must be between 0 and 12")

    def quantize(self, value: Decimal) -> Decimal:
        """Round one finite value according to the signed policy."""
        if not value.is_finite():
            raise ValueError("scent values must be finite")
        quantum = Decimal(1).scaleb(-self.decimal_places)
        return value.quantize(quantum, rounding=ROUND_HALF_EVEN)

    def emission(self) -> tuple[tuple[Decimal, ...], ...]:
        """Return the exact internal-precision center-scaled emission matrix."""
        with localcontext() as context:
            context.prec = 28
            return tuple(
                tuple(self.center_intensity * Decimal(weight) for weight in row)
                for row in KERNEL_TEXT
            )

    def after_full_turn(self, value: Decimal) -> Decimal:
        """Apply one full-turn decay without boundary quantization."""
        if not value.is_finite() or value < 0:
            raise ValueError("scent values must be finite and non-negative")
        return value * (Decimal(1) - self.decay)

    def serialize(self, value: Decimal) -> str:
        """Quantize one value only at a wire or audit boundary."""
        return format(self.quantize(value), "f")
