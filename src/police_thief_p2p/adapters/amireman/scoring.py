"""Fixed course scoring and role alternation for amireman series."""

from __future__ import annotations

SCORES: dict[str, tuple[int, int]] = {
    "capture": (20, 5),
    "survival": (5, 10),
    "timeout": (0, 0),
    "technical_loss": (0, 0),
    "tamper_forfeit": (0, 0),
}
TIE_SCORE = 2


def score_for(outcome: str, role: str) -> int:
    police, thief = SCORES.get(outcome, (0, 0))
    return police if role == "police" else thief


def role_for(natural: str, sub_game_number: int) -> str:
    """Odd sub-games play natural role; even play the opposite."""
    if sub_game_number % 2 == 1:
        return natural
    return "thief" if natural == "police" else "police"


def canonical_rows(summaries: list, ours: str, theirs: str) -> list[dict]:
    """Per-sub-game consensus facts keyed by group id."""
    rows = []
    for summary in summaries:
        outcome, our_role = summary["result"], summary["role"]
        their_role = "thief" if our_role == "police" else "police"
        ours_score = score_for(outcome, our_role)
        theirs_score = score_for(outcome, their_role)
        rows.append(
            {
                "sub_game_number": summary["sub_game_number"],
                "result": outcome,
                "roles": {ours: our_role, theirs: their_role},
                "score": {ours: ours_score, theirs: theirs_score},
                "winner_group": (
                    ours if ours_score > theirs_score else (theirs if theirs_score > ours_score else None)
                ),
            }
        )
    return rows
