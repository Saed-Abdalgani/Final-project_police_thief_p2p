"""MCP URL normalization for Cloudflare quick tunnels."""

from police_thief_p2p.adapters.amireman.client import mcp_url


def test_mcp_url_appends_missing_path() -> None:
    assert mcp_url("https://whether-shoulder-doug-coral.trycloudflare.com") == (
        "https://whether-shoulder-doug-coral.trycloudflare.com/mcp"
    )


def test_mcp_url_keeps_existing_path() -> None:
    assert mcp_url("https://host.example/mcp") == "https://host.example/mcp"


def test_mcp_url_strips_trailing_slash() -> None:
    assert mcp_url("https://host.example/mcp/") == "https://host.example/mcp"
