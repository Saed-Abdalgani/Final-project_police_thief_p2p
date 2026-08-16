"""Pinned clean-room opponent revision and family catalog."""

from typing import Final

OPPONENT_REVISIONS: Final[dict[str, str | None]] = {
    "smngrp05-police": "2b41147664c9d7a76a7bcf70a47bfce36ec03885",
    "smngrp05-thief": "82206d6f384e2c031b01f927bc8d26e9e455bf5d",
    "ahk-yosi-police": "3893ff0ed6ed8703331d9d39a270500c8c6d7a28",
    "ahk-yosi-thief": "5f2942c79f411b2166ec54f039278ef744c19b03",
    "g005": None,
}
FAMILY_IDS: Final[tuple[str, ...]] = (
    "smngrp05",
    "ahk-yosi",
    "g005-unknown",
    "corner-squeeze",
    "boundary",
    "cycle",
    "random",
    "aggressive-barrier",
    "anti-intercept",
    "policy-switch",
)
TRAINING_FAMILIES: Final[tuple[str, ...]] = (
    "smngrp05",
    "ahk-yosi",
    "g005-unknown",
    "corner-squeeze",
    "boundary",
    "cycle",
    "anti-intercept",
    "policy-switch",
)
