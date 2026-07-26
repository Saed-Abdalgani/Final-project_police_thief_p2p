"""WCAG-aware fixed colors for live and replay presentation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StatusStyle:
    """Text, icon, and colors for one critical state."""

    icon: str
    label: str
    background: str
    foreground: str


STATUS_STYLES = {
    "ready": StatusStyle("●", "READY", "#E6FCF5", "#064E3B"),
    "thinking": StatusStyle("◆", "THINKING", "#FFF3BF", "#5F3B00"),
    "waiting": StatusStyle("…", "WAITING", "#E7F5FF", "#0B3A5B"),
    "locked": StatusStyle("▣", "LOCKED", "#F3F0FF", "#3B2A6F"),
    "paused": StatusStyle("Ⅱ", "PAUSED", "#FFF4E6", "#663C00"),
    "degraded": StatusStyle("!", "DEGRADED", "#FFF0F6", "#7A1737"),
    "terminal": StatusStyle("■", "TERMINAL", "#E6FCF5", "#064E3B"),
    "error": StatusStyle("⚠", "ERROR", "#FFF5F5", "#7F1D1D"),
}

HEAT_COLORS = (
    "#F8FAFC",
    "#DBEAFE",
    "#93C5FD",
    "#3B82F6",
    "#1E3A8A",
)


def heat_color(probability: float) -> str:
    """Map the fixed [0, 1] probability scale to a stable color."""
    if not 0 <= probability <= 1:
        raise ValueError("heat probability must be in [0, 1]")
    return HEAT_COLORS[min(len(HEAT_COLORS) - 1, int(probability * len(HEAT_COLORS)))]


def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG contrast ratio for two hexadecimal RGB colors."""

    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)
