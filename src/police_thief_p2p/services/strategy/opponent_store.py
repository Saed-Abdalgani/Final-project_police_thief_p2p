"""Durable isolation for audited cross-sub-game opponent profiles."""

import json
import re

from police_thief_p2p.domain.values import Direction
from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.services.strategy.opponent import OpponentProfile
from police_thief_p2p.shared.canonical_json import canonical_json_bytes

_KEY_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class OpponentProfileStore:
    """Persist exact opponent/version records with no cross-opponent sharing."""

    __slots__ = ("_repository",)

    def __init__(self, repository: RepositoryPort) -> None:
        """Create a store over an injected private repository."""
        self._repository = repository

    def load(self, opponent_group: str, strategy_version: str) -> OpponentProfile:
        """Load an exact profile or return a fresh isolated prior."""
        key = self._key(opponent_group, strategy_version)
        data = self._repository.load(key)
        if data is None:
            return OpponentProfile(opponent_group, strategy_version)
        try:
            value = json.loads(data)
            return OpponentProfile(
                opponent_group=str(value["opponent_group"]),
                strategy_version=str(value["strategy_version"]),
                counts=tuple(float(item) for item in value["counts"]),  # type: ignore[arg-type]
                observations=int(value["observations"]),
                hint_truth=float(value["hint_truth"]),
                hint_lie=float(value["hint_lie"]),
                last_direction=(
                    None
                    if value["last_direction"] is None
                    else Direction(str(value["last_direction"]))
                ),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("stored opponent profile is invalid") from exc

    def save_audited(self, profile: OpponentProfile) -> None:
        """Persist one profile only after the caller's completed audit boundary."""
        document = {
            "opponent_group": profile.opponent_group,
            "strategy_version": profile.strategy_version,
            "counts": [format(value, ".12g") for value in profile.counts],
            "observations": profile.observations,
            "hint_truth": format(profile.hint_truth, ".12g"),
            "hint_lie": format(profile.hint_lie, ".12g"),
            "last_direction": (
                None if profile.last_direction is None else profile.last_direction.value
            ),
        }
        self._repository.save(
            self._key(profile.opponent_group, profile.strategy_version),
            canonical_json_bytes(document),
        )

    @staticmethod
    def _key(opponent_group: str, strategy_version: str) -> str:
        if (
            _KEY_PART.fullmatch(opponent_group) is None
            or _KEY_PART.fullmatch(strategy_version) is None
        ):
            raise ValueError("opponent profile key is unsafe")
        safe_version = strategy_version.replace(".", "-").replace("_", "-")
        return f"opponent-{opponent_group.casefold()}-{safe_version.casefold()}"
