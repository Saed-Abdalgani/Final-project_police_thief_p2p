"""Loopback integration: two amireman peers play a short DEMO series."""

from __future__ import annotations

import threading
from pathlib import Path

from police_thief_p2p.adapters.amireman.friendly import run_friendly
from police_thief_p2p.adapters.amireman.terms import default_terms


def test_amireman_loopback_two_games(tmp_path: Path) -> None:
    terms = default_terms()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    errors: list[BaseException] = []
    results: dict[str, object] = {}

    def police() -> None:
        try:
            results["police"] = run_friendly(
                "saedshki",
                "http://127.0.0.1:18902/mcp",
                "police",
                terms,
                out_a,
                host="127.0.0.1",
                port=18901,
                github_commit="a" * 40,
                num_games=2,
                seed=7,
                turn_timeout=60.0,
                members=["Alpha", "Beta"],
                public_mcp_url="http://127.0.0.1:18901/mcp",
                game_id="DEMO-LOOP",
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def thief() -> None:
        try:
            results["thief"] = run_friendly(
                "amireman",
                "http://127.0.0.1:18901/mcp",
                "thief",
                terms,
                out_b,
                host="127.0.0.1",
                port=18902,
                github_commit="b" * 40,
                num_games=2,
                seed=11,
                turn_timeout=60.0,
                members=["Amir", "Eman"],
                public_mcp_url="http://127.0.0.1:18902/mcp",
                game_id="DEMO-LOOP",
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=police), threading.Thread(target=thief)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=240)
    assert not errors, errors
    police_result = results["police"]
    thief_result = results["thief"]
    assert police_result.game_id == "DEMO-LOOP"  # type: ignore[attr-defined]
    assert thief_result.game_uid == police_result.game_uid  # type: ignore[attr-defined]
    assert police_result.sha_match is True  # type: ignore[attr-defined]
    assert thief_result.sha_match is True  # type: ignore[attr-defined]
    assert police_result.lecturer_report_sent is False  # type: ignore[attr-defined]
    assert len(police_result.summaries) == 2  # type: ignore[attr-defined]
