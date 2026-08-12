"""Map flat amireman terms / nested game.json into documented internal knobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from police_thief_p2p.adapters.amireman.terms import DEFAULTS, default_terms, validate_terms


def terms_from_nested_game(document: dict[str, Any]) -> dict[str, Any]:
    """Accept opponent nested game.json and project the flat 14 signed terms."""
    board = document.get("board_and_agents", {})
    world = document.get("world", {})
    movement = document.get("movement_and_barriers", {})
    pheromones = document.get("pheromones", {})
    network = document.get("network_and_league", {})
    return default_terms(
        board_size=int(board.get("grid_size", DEFAULTS["board_size"])),
        smell_grid_size=int(pheromones.get("pheromone_grid_size", DEFAULTS["smell_grid_size"])),
        decay_per_step=float(pheromones.get("pheromone_decay", DEFAULTS["decay_per_step"])),
        emit_intensity=float(
            pheromones.get("pheromone_center_intensity", DEFAULTS["emit_intensity"])
        ),
        max_steps=int(movement.get("max_moves", DEFAULTS["max_steps"])),
        barriers_max=int(movement.get("max_barriers", DEFAULTS["barriers_max"])),
        setting=str(world.get("map_area", DEFAULTS["setting"])),
        hint_max_words=int(world.get("hint_max_words", DEFAULTS["hint_max_words"])),
        axis_origin_corner=str(board.get("axis_origin_corner", DEFAULTS["axis_origin_corner"])),
        axis_start_index=int(board.get("axis_start_index", DEFAULTS["axis_start_index"])),
        thief_start=list(board.get("thief_start", DEFAULTS["thief_start"])),
        cop_start=list(board.get("cop_start", DEFAULTS["cop_start"])),
        num_games=int(network.get("num_games", DEFAULTS["num_games"])),
    )


def load_terms(path: Path | None) -> dict[str, Any]:
    """Load flat terms, nested game.json, or fall back to defaults."""
    if path is None:
        terms = default_terms()
    else:
        document = json.loads(path.read_text(encoding="utf-8"))
        if all(key in document for key in ("board_size", "max_steps", "setting")):
            terms = default_terms(**{key: document[key] for key in document if key in DEFAULTS})
        else:
            terms = terms_from_nested_game(document)
    validate_terms(terms)
    return terms


def to_internal_knobs(terms: dict[str, Any]) -> dict[str, Any]:
    """Documented mapping into our familiar internal names (not used on the wire)."""
    return {
        "grid_size": terms["board_size"],
        "cop_start": list(terms["cop_start"]),
        "thief_start": list(terms["thief_start"]),
        "pheromone_decay": terms["decay_per_step"],
        "pheromone_center_intensity": terms["emit_intensity"],
        "pheromone_grid_size": terms["smell_grid_size"],
        "max_barriers": terms["barriers_max"],
        "survival_threshold": terms["max_steps"],
        "max_moves": terms["max_steps"],
        "map_area": terms["setting"],
        "hint_max_words": terms["hint_max_words"],
        "num_games": terms["num_games"],
    }
