"""Run one independently rooted FastMCP peer process."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.adapters.mcp.server import build_mcp_server
from police_thief_p2p.sdk import ProtocolLimits, SimulationSdk, create_protocol_runtime


def build_parser() -> argparse.ArgumentParser:
    """Build the isolated-peer process arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-config", required=True, type=Path)
    parser.add_argument("--private-config", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Load through the SDK and run one streamable-HTTP FastMCP server."""
    args = build_parser().parse_args(argv)
    shared_document = args.shared_config.resolve().read_bytes()
    private_document = args.private_config.resolve().read_bytes()
    base_sdk = SimulationSdk()
    effective = base_sdk.load_configuration(shared_document, private_document)
    network = effective.private.network
    limits = ProtocolLimits(
        max_request_bytes=network.max_request_bytes,
        max_json_depth=network.max_json_depth,
        max_string_length=network.max_string_length,
        max_collection_items=network.max_collection_items,
        max_concurrent_requests=effective.shared.rate_limiter_gatekeeper.concurrent_requests,
        reorder_window=network.reorder_window,
    )
    runtime = create_protocol_runtime(
        local_group=effective.private.identity.group_id,
        shared_document=shared_document,
        storage_root=effective.private.paths.artifact_root.resolve() / "protocol",
        limits=limits,
    )
    sdk = SimulationSdk(runtime)
    server = build_mcp_server(
        sdk,
        max_request_bytes=limits.max_request_bytes,
        concurrent_requests=limits.max_concurrent_requests,
    )
    server.run(
        transport="http",
        host=network.listen_host,
        port=network.listen_port,
        path="/mcp",
        show_banner=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
