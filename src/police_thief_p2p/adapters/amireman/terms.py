"""Flat 14 signed terms for the amireman wire."""

from __future__ import annotations

from typing import Any

TERMS_KEYS: tuple[str, ...] = (
    "board_size",
    "smell_grid_size",
    "decay_per_step",
    "emit_intensity",
    "min_center_intensity",
    "max_steps",
    "barriers_max",
    "setting",
    "hint_max_words",
    "axis_origin_corner",
    "axis_start_index",
    "thief_start",
    "cop_start",
    "num_games",
)

DEFAULTS: dict[str, Any] = {
    "board_size": 7,
    "smell_grid_size": 5,
    "decay_per_step": 0.1,
    "emit_intensity": 0.9,
    "min_center_intensity": 0.5,
    "max_steps": 35,
    "barriers_max": 14,
    "setting": "Haifa",
    "hint_max_words": 15,
    "axis_origin_corner": "top-left",
    "axis_start_index": 0,
    "thief_start": [3, 3],
    "cop_start": [0, 0],
    "num_games": 6,
}


def default_terms(**overrides: Any) -> dict[str, Any]:
    """Standard agreed terms with optional per-key overrides."""
    terms = {key: (list(value) if isinstance(value, list) else value) for key, value in DEFAULTS.items()}
    terms.update(overrides)
    return terms


def validate_terms(terms: dict[str, Any]) -> None:
    """Require the closed 14-key set before any port opens."""
    missing = [key for key in TERMS_KEYS if terms.get(key) is None]
    if missing:
        raise ValueError("missing required agreed term(s): " + ", ".join(missing))
    extra = sorted(set(terms) - set(TERMS_KEYS))
    if extra:
        raise ValueError("unexpected term key(s): " + ", ".join(extra))


def terms_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Parsed-object equality over the 14 keys."""
    return all(left.get(key) == right.get(key) for key in TERMS_KEYS)
