"""Shared gate record types used by every M12 promotion decision."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GateResult:
    """One named promotion gate with its measured value and verdict."""

    gate_id: str
    requirement: str
    measured: float | int | bool
    passed: bool

    def __post_init__(self) -> None:
        """Require a documented identifier and requirement statement."""
        if not self.gate_id or not self.requirement:
            raise ValueError("every gate needs an identifier and a stated requirement")

    def as_document(self) -> dict[str, object]:
        """Return the serializable gate record."""
        measured = self.measured
        return {
            "gate_id": self.gate_id,
            "requirement": self.requirement,
            "measured": round(measured, 3) if isinstance(measured, float) else measured,
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class GateReport:
    """The complete promotion decision built from independent gates."""

    gates: tuple[GateResult, ...]

    def __post_init__(self) -> None:
        """Require at least one evaluated gate."""
        if not self.gates:
            raise ValueError("a gate report requires at least one gate")

    @property
    def passed(self) -> bool:
        """Return whether every gate passed."""
        return all(item.passed for item in self.gates)

    @property
    def failures(self) -> tuple[str, ...]:
        """Return the identifiers of every failing gate."""
        return tuple(item.gate_id for item in self.gates if not item.passed)

    def as_document(self) -> dict[str, object]:
        """Return the serializable promotion decision."""
        return {
            "gates": [item.as_document() for item in self.gates],
            "failures": list(self.failures),
            "passed": self.passed,
        }
