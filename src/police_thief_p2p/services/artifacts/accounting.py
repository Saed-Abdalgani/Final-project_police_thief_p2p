"""Exact step, sub-game, and series token-accounting verification."""

from police_thief_p2p.services.artifacts.result import FinalResultArtifact


def verify_token_accounting(result: FinalResultArtifact) -> None:
    """Prove group totals equal every linked sub-game accounting record."""
    totals: dict[str, tuple[int, int]] = {group.group_id: (0, 0) for group in result.groups}
    if len(totals) != 2:
        raise ValueError("result requires two distinct group totals")
    for sub_game in result.sub_games:
        if set(sub_game.tokens) != set(totals):
            raise ValueError("sub-game token groups do not match series groups")
        for group_id, usage in sub_game.tokens.items():
            current_input, current_output = totals[group_id]
            totals[group_id] = (
                current_input + usage.input_tokens,
                current_output + usage.output_tokens,
            )
    for group in result.groups:
        expected = totals[group.group_id]
        actual = (group.tokens.input_tokens, group.tokens.output_tokens)
        if actual != expected:
            raise ValueError(f"series token total mismatch for {group.group_id}")


def verify_result_totals(result: FinalResultArtifact) -> None:
    """Recompute exact scores, wins, ties, and series winner from six records."""
    group_ids = {group.group_id for group in result.groups}
    scores = dict.fromkeys(group_ids, 0)
    wins = dict.fromkeys(group_ids, 0)
    ties = dict.fromkeys(group_ids, 0)
    if {item.sub_game_number for item in result.sub_games} != set(range(1, 7)):
        raise ValueError("result must contain each sub-game number exactly once")
    for sub_game in result.sub_games:
        if set(sub_game.scores) != group_ids:
            raise ValueError("sub-game score groups do not match series groups")
        for group_id, score in sub_game.scores.items():
            scores[group_id] += score
        if sub_game.tie:
            for group_id in group_ids:
                ties[group_id] += 1
        elif sub_game.winner in group_ids:
            wins[sub_game.winner] += 1
        else:
            raise ValueError("sub-game winner is invalid")
    for group in result.groups:
        if (group.score, group.wins, group.ties) != (
            scores[group.group_id],
            wins[group.group_id],
            ties[group.group_id],
        ):
            raise ValueError(f"series totals mismatch for {group.group_id}")
    maximum = max(scores.values())
    leaders = {group_id for group_id, score in scores.items() if score == maximum}
    expected_tie = len(leaders) == 2
    expected_winner = None if expected_tie else next(iter(leaders))
    if result.series_tie != expected_tie or result.series_winner != expected_winner:
        raise ValueError("series winner/tie does not match scores")
