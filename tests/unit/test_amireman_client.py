"""MCP URL normalization and handshake retry for Cloudflare quick tunnels."""

import pytest

from police_thief_p2p.adapters.amireman.client import McpTransport, mcp_url
from police_thief_p2p.adapters.amireman.queues import PeerInboxes


def test_mcp_url_appends_missing_path() -> None:
    assert mcp_url("https://whether-shoulder-doug-coral.trycloudflare.com") == (
        "https://whether-shoulder-doug-coral.trycloudflare.com/mcp"
    )


def test_mcp_url_keeps_existing_path() -> None:
    assert mcp_url("https://host.example/mcp") == "https://host.example/mcp"


def test_mcp_url_strips_trailing_slash() -> None:
    assert mcp_url("https://host.example/mcp/") == "https://host.example/mcp"


def test_call_with_retry_survives_transient_502() -> None:
    transport = McpTransport(
        "http://127.0.0.1:9/mcp", PeerInboxes(), connect_timeout=2.0, retry_interval=0.01
    )
    hits = {"n": 0}

    def fake_call(tool: str, argument: dict, *, timeout: float = 20.0) -> None:
        hits["n"] += 1
        if hits["n"] < 3:
            raise RuntimeError("502 Bad Gateway")

    try:
        transport._call = fake_call  # type: ignore[method-assign]
        transport._call_with_retry("negotiate", {}, timeout=1.0)
        assert hits["n"] == 3
    finally:
        transport.close()


def test_call_with_retry_fails_after_budget() -> None:
    transport = McpTransport(
        "http://127.0.0.1:9/mcp", PeerInboxes(), connect_timeout=0.05, retry_interval=0.01
    )

    def fake_call(tool: str, argument: dict, *, timeout: float = 20.0) -> None:
        raise RuntimeError("502 Bad Gateway")

    try:
        transport._call = fake_call  # type: ignore[method-assign]
        with pytest.raises(RuntimeError, match="unreachable"):
            transport._call_with_retry("negotiate", {}, timeout=0.05)
    finally:
        transport.close()
