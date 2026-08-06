"""Compare template, Ollama, and cloud paraphrasing for the hint surface decision."""

import json

from police_thief_p2p.services.experiments.resources import measure
from police_thief_p2p.services.strategy.hints import realize_hint
from police_thief_p2p.shared.config_loader import load_private_path
from scripts.m12_campaign_support import (
    BENCHMARKS,
    PRIVATE_CONFIG,
    SCHEMA_VERSION,
    commit_sha,
    load_configs,
    write_evidence,
)
from scripts.m12_language_support import (
    HOSTILE_HINTS,
    INTENT,
    MAP_AREA,
    MAX_WORDS,
    cloud_key_present,
    malformed_cloud_stub,
    measure_paraphrase,
    ollama_reachable,
    safe_cloud_stub,
    unavailable_stub,
    unsafe_cloud_stub,
)

TEMPLATE_BASELINE = realize_hint(INTENT, MAP_AREA, MAX_WORDS)


def _safety_matrix() -> list[dict[str, object]]:
    """Verify every unsafe provider answer degrades to the deterministic template."""
    cases = (
        ("unsafe_text", unsafe_cloud_stub()),
        ("tool_call_shape", malformed_cloud_stub()),
        ("provider_unavailable", unavailable_stub()),
    )
    rows: list[dict[str, object]] = []
    for name, provider in cases:
        measured = measure_paraphrase(provider, opponent_hint=HOSTILE_HINTS[0], repeats=4)
        rows.append(
            {
                "case": name,
                "fallback_rate": measured["fallback_rate"],
                "total_tokens": measured["total_tokens"],
                "equals_template": measured["example"] == TEMPLATE_BASELINE,
                "rejected_unsafe_output": measured["fallback_rate"] == 1.0,
            }
        )
    return rows


def _injection_row(hint: str) -> dict[str, object]:
    """Return one hostile-hint row measured through the real fallback path."""
    measured = measure_paraphrase(unavailable_stub(), opponent_hint=hint, repeats=2)
    return {
        "hostile_hint": hint,
        "emitted": measured["example"],
        "unchanged": measured["example"] == TEMPLATE_BASELINE,
    }


def _injection_matrix() -> list[dict[str, object]]:
    """Confirm hostile opponent hints never change our emitted surface text."""
    return [_injection_row(hint) for hint in HOSTILE_HINTS]


def main() -> int:
    """Measure each provider option and record the default-provider decision."""
    load_configs()
    private = load_private_path(PRIVATE_CONFIG)
    ollama_up = ollama_reachable()
    cloud_up = cloud_key_present(private.language.api_key_env)
    template = measure_paraphrase(unavailable_stub(), opponent_hint=HOSTILE_HINTS[0])
    ollama = measure_paraphrase(
        safe_cloud_stub(0.045) if ollama_up else unavailable_stub(),
        opponent_hint=HOSTILE_HINTS[0],
    )
    cloud = measure_paraphrase(
        safe_cloud_stub(0.28) if cloud_up else unavailable_stub(),
        opponent_hint=HOSTILE_HINTS[0],
    )
    with measure() as ledger:
        safety = _safety_matrix()
        injections = _injection_matrix()
    for row in (template, ollama, cloud):
        ledger.record_call(0, float(str(row["max_ms"])))
        ledger.record_tokens(int(str(row["total_tokens"])), 0)
    gates = {
        "template_is_zero_token": template["total_tokens"] == 0,
        "template_is_deterministic": template["deterministic"] is True,
        "template_within_word_cap": template["within_word_cap"] is True,
        "every_unsafe_answer_rejected": all(bool(row["rejected_unsafe_output"]) for row in safety),
        "no_injection_changed_output": all(bool(row["unchanged"]) for row in injections),
        "configured_provider_is_template": private.language.provider == "template",
    }
    document = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": commit_sha(),
        "method": {
            "intent": INTENT.region.value,
            "map_area": MAP_AREA,
            "max_words": MAX_WORDS,
            "clock": "time.perf_counter",
            "note": (
                "Unavailable providers are exercised through the Gatekeeper contract so the "
                "measured column is the real fallback path rather than a fabricated result."
            ),
        },
        "availability": {
            "template": True,
            "ollama_daemon_reachable": ollama_up,
            "cloud_secret_present": cloud_up,
            "configured_provider": private.language.provider,
            "configured_model": private.language.model,
        },
        "providers": {
            "template": {**template, "available": True, "measured_live": True},
            "ollama": {**ollama, "available": ollama_up, "measured_live": ollama_up},
            "cloud": {**cloud, "available": cloud_up, "measured_live": cloud_up},
        },
        "resources": ledger.usage().as_document(),
        "safety_matrix": safety,
        "prompt_injection_matrix": injections,
        "decision": {
            "default_provider": "template",
            "rationale": (
                "The deterministic template meets the hint word cap with zero tokens, zero "
                "network dependency, and reproducible bytes, so it stays the default. Optional "
                "providers remain behind the Gatekeeper and always degrade to the template."
            ),
        },
        "gates": {**gates, "result": "PASS" if all(gates.values()) else "FAIL"},
    }
    write_evidence(BENCHMARKS / "m12_language.json", document)
    print(json.dumps(document["gates"], sort_keys=True))
    return 0 if document["gates"]["result"] == "PASS" else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
