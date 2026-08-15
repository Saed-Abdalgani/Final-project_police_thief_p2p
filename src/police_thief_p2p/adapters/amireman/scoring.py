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


def aggregate(rows: list[dict], tie_score: int = TIE_SCORE) -> dict:
    """Series totals in the course-reference shape used for mutual_agreement."""
    scores = [row["score"] for row in rows]
    groups = sorted({group for item in scores for group in item})
    totals = {group: sum(item.get(group, 0) for item in scores) for group in groups}
    won = dict.fromkeys(groups, 0)
    ties = 0
    for item in scores:
        if not item:
            continue
        best = max(item.values())
        leaders = [group for group, value in item.items() if value == best]
        if len(leaders) == 1:
            won[leaders[0]] += 1
        else:
            ties += 1
    if len(groups) == 2 and totals[groups[0]] == totals[groups[1]]:
        for group in groups:
            totals[group] += tie_score
        return {
            "total_score": totals,
            "sub_games_won": won,
            "ties": ties,
            "winner_group": None,
            "series_tie": True,
        }
    return {
        "total_score": totals,
        "sub_games_won": won,
        "ties": ties,
        "winner_group": max(totals, key=lambda group: totals[group]) if totals else None,
        "series_tie": False,
    }
