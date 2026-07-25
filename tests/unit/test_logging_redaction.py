import io
import json
import logging
from pathlib import Path

from police_thief_p2p.constants import REDACTED
from police_thief_p2p.shared.logging import configure_logging, correlation_context
from police_thief_p2p.shared.redaction import (
    is_sensitive_key,
    redact_text,
    redact_value,
)


def test_recursive_redaction_covers_keys_bytes_email_bearer_and_url() -> None:
    value = {
        "api-token": "actual-value",
        "profile": {
            "email": "student@example.com",
            "endpoint": "https://user:pass@example.com/mcp?token=abc&mode=safe",  # pragma: allowlist secret
        },
        "raw": b"binary-secret",
        "items": ["Bearer abc.def", "ordinary"],
    }

    redacted = redact_value(value)

    assert redacted == {
        "api-token": REDACTED,
        "profile": {
            "email": REDACTED,
            "endpoint": f"https://example.com/mcp?token={REDACTED}&mode=safe",
        },
        "raw": REDACTED,
        "items": [f"Bearer {REDACTED}", "ordinary"],
    }
    assert is_sensitive_key("private-key")
    assert not is_sensitive_key("game_id")


def test_redact_text_handles_malformed_sensitive_url() -> None:
    assert REDACTED in redact_text("https://example.com:invalid?token=secret")


def test_structured_logging_emits_redacted_json_and_context() -> None:
    stream = io.StringIO()
    logger = configure_logging("foundation-test", level=logging.WARNING, stream=stream)
    with correlation_context("corr-123"):
        logger.warning("Contact student@example.com using Bearer secret")

    payload = json.loads(stream.getvalue())
    fixture_path = Path("tests/fixtures/structured_log_expected_keys.json")
    expected_keys = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert sorted(payload) == expected_keys
    assert payload["level"] == "WARNING"
    assert payload["correlation_id"] == "corr-123"
    assert "student@example.com" not in payload["message"]
    assert "secret" not in payload["message"]


def test_structured_logging_records_exception_type_without_trace() -> None:
    stream = io.StringIO()
    logger = configure_logging("exception-test", stream=stream)
    try:
        raise ValueError("unsafe internal detail")
    except ValueError:
        logger.exception("safe failure")

    payload = json.loads(stream.getvalue())
    assert payload["exception_type"] == "ValueError"
    assert "unsafe internal detail" not in stream.getvalue()
