"""Pure presentation mapping over public SDK DTOs."""

from dataclasses import dataclass

from police_thief_p2p.sdk import LocalView, SdkError
from police_thief_p2p.sdk.live_view import assert_private_document

from .palette import STATUS_STYLES, StatusStyle


@dataclass(frozen=True, slots=True)
class SafeUiError:
    """Actionable redacted UI error without exception internals."""

    message: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class LiveViewModel:
    """UI-ready labels derived without game decisions."""

    view: LocalView
    status: StatusStyle
    role_label: str
    position_label: str
    belief_summary: str
    progress_label: str
    metrics_label: str
    accessible_board_label: str

    @classmethod
    def from_view(cls, view: LocalView) -> "LiveViewModel":
        """Map a privacy-checked SDK snapshot to accessible labels."""
        assert_private_document(view.as_dict())
        status = STATUS_STYLES[view.status.value]
        role_label = "Police" if view.role == "police" else "Thief"
        row, col = view.own_position
        return cls(
            view=view,
            status=status,
            role_label=f"Own role: {role_label}",
            position_label=f"Own position: row {row}, column {col}",
            belief_summary=(
                f"Opponent belief, not certainty: peak {view.belief_peak_probability:.3f}; "
                f"entropy {view.belief_entropy_bits:.3f} bits; "
                f"90% region {len(view.credible_region)} cells."
            ),
            progress_label=(
                f"Sub-game {view.sub_game_number}/{view.series_games}; step {view.step_number}"
            ),
            metrics_label=(
                f"Latency {view.metrics.latency_ms} ms; tokens "
                f"{view.metrics.input_tokens + view.metrics.output_tokens}; "
                f"fallback {'yes' if view.metrics.fallback_used else 'no'}"
            ),
            accessible_board_label=(
                f"{role_label} local board. Own position row {row}, column {col}. "
                f"{len(view.public_barriers)} public barriers. Opponent location is uncertain."
            ),
        )


def safe_ui_error(error: Exception) -> SafeUiError:
    """Return a stable safe error label with correlation ID and no traceback."""
    if isinstance(error, SdkError):
        correlation = error.correlation_id or "not-provided"
        return SafeUiError(str(error), correlation)
    return SafeUiError(
        "The operation could not complete. Retry or export diagnostics.",
        "local-ui-error",
    )
