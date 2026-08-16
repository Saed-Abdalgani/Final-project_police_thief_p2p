"""Loopback integration: two amireman peers play a short DEMO series."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from police_thief_p2p.adapters.amireman.friendly import run_friendly
from police_thief_p2p.adapters.amireman.scent import (
    MULTIPLICATIVE_KERNEL_V1,
    SUBTRACTIVE_CHEBYSHEV_V1,
)
from police_thief_p2p.adapters.amireman.terms import default_terms


@pytest.mark.parametrize(
    ("scent_model", "base_port"),
    [(MULTIPLICATIVE_KERNEL_V1, 18900), (SUBTRACTIVE_CHEBYSHEV_V1, 19000)],
)
def test_amireman_loopback_six_games_both_scent_models(
    tmp_path: Path, scent_model: str, base_port: int
) -> None:
    terms = default_terms()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    errors: list[BaseException] = []
    results: dict[str, object] = {}

    def police() -> None:
        try:
            results["police"] = run_friendly(
                "saedshki",
                f"http://127.0.0.1:{base_port + 2}/mcp",
                "police",
                terms,
                out_a,
                host="127.0.0.1",
                port=base_port + 1,
                github_commit="a" * 40,
                num_games=6,
                seed=7,
                turn_timeout=60.0,
                members=["Alpha", "Beta"],
                public_mcp_url=f"http://127.0.0.1:{base_port + 1}/mcp",
                game_id="DEMO-LOOP",
                scent_model=scent_model,
            )
        except BaseException as exc:
            errors.append(exc)

    def thief() -> None:
        try:
            results["thief"] = run_friendly(
                "amireman",
                f"http://127.0.0.1:{base_port + 1}/mcp",
                "thief",
                terms,
                out_b,
                host="127.0.0.1",
                port=base_port + 2,
                github_commit="b" * 40,
                num_games=6,
                seed=11,
                turn_timeout=60.0,
                members=["Amir", "Eman"],
                public_mcp_url=f"http://127.0.0.1:{base_port + 2}/mcp",
                game_id="DEMO-LOOP",
                scent_model=scent_model,
            )
        except BaseException as exc:
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
    assert len(police_result.summaries) == 6  # type: ignore[attr-defined]
    assert police_result.results_agreed is True  # type: ignore[attr-defined]
    assert thief_result.results_agreed is True  # type: ignore[attr-defined]
    assert all(item["audit"]["passed"] for item in police_result.summaries)  # type: ignore[attr-defined]
    assert all(item["audit"]["passed"] for item in thief_result.summaries)  # type: ignore[attr-defined]
    assert (
        police_result.result_doc["consensus_sha"]
        == thief_result.result_doc[  # type: ignore[attr-defined]
            "consensus_sha"
        ]
    )
    assert police_result.training_sidecar.is_file()  # type: ignore[attr-defined]
    assert thief_result.training_sidecar.is_file()  # type: ignore[attr-defined]
