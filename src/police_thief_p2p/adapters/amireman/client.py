"""Outbound push client to the opponent's amireman MCP endpoint."""

from __future__ import annotations

import asyncio
import contextlib
import queue
import threading
import time
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from police_thief_p2p.adapters.amireman.queues import PeerInboxes


def mcp_url(url: str) -> str:
    """Return an MCP endpoint, appending /mcp when the caller omitted it."""
    trimmed = url.strip().rstrip("/")
    if trimmed.endswith("/mcp"):
        return trimmed
    return f"{trimmed}/mcp"


class McpTransport:
    """Push to opponent; pull from own inboxes.

    One FastMCP session is kept on a private event loop so each turn is not a
    fresh TLS handshake plus initialize/terminate (that is what printed
    ``Session termination failed: 502`` after the last series).
    """

    def __init__(
        self,
        opponent_url: str,
        inboxes: PeerInboxes,
        *,
        connect_timeout: float = 180.0,
        retry_interval: float = 1.0,
    ) -> None:
        """Keep opponent URL, inboxes, and a long-lived client loop."""
        self._url = mcp_url(opponent_url)
        self._inboxes = inboxes
        self._connect_timeout = connect_timeout
        self._retry = retry_interval
        self._client: Client | None = None
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="mcp-client")
        self._thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def close(self) -> None:
        """Drop the kept session and stop the client loop."""
        if self._loop.is_closed():
            return
        fut = asyncio.run_coroutine_threadsafe(self._aclose(), self._loop)
        with contextlib.suppress(Exception):
            fut.result(timeout=5.0)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=3.0)

    async def _aclose(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return
        with contextlib.suppress(Exception):
            await client.__aexit__(None, None, None)

    async def _invoke(self, tool: str, argument: dict[str, Any]) -> None:
        key = "payload" if tool == "submit_audit" else "message"
        last_exc: BaseException | None = None
        for _ in range(3):
            try:
                if self._client is None:
                    self._client = Client(StreamableHttpTransport(self._url))
                    await self._client.__aenter__()
                await self._client.call_tool(tool, {key: argument})
                return
            except Exception as exc:
                last_exc = exc
                await self._aclose()
                await asyncio.sleep(self._retry)
        raise last_exc if last_exc is not None else RuntimeError("MCP invoke failed")

    def _call(self, tool: str, argument: dict[str, Any]) -> None:
        fut = asyncio.run_coroutine_threadsafe(self._invoke(tool, argument), self._loop)
        fut.result(timeout=self._connect_timeout)

    def _call_with_retry(self, tool: str, argument: dict[str, Any], timeout: float | None = None) -> None:
        deadline = time.time() + (timeout if timeout is not None else self._connect_timeout)
        while True:
            try:
                self._call(tool, argument)
                return
            except Exception as exc:
                if time.time() >= deadline:
                    raise RuntimeError(f"opponent MCP unreachable at {self._url}: {exc}") from exc
                time.sleep(self._retry)

    def exchange_agreement(self, signed: dict[str, Any]) -> dict[str, Any]:
        """Push our signed terms and wait for the opponent greeting."""
        self._call_with_retry("negotiate", signed, timeout=self._connect_timeout)
        try:
            return self._inboxes.agreements.get(timeout=240.0)
        except queue.Empty as exc:
            raise RuntimeError("opponent never sent its agreement") from exc

    def send_turn(self, message: dict[str, Any]) -> None:
        """Push one public turn to the opponent."""
        self._call_with_retry("receive_turn", message)

    def poll_turn(self, timeout: float) -> dict[str, Any] | None:
        """Pop an inbound turn, or None on timeout."""
        try:
            return self._inboxes.turns.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_audit(self, payload: dict[str, Any]) -> None:
        """Push an audit blob; ignore a dead opponent."""
        with contextlib.suppress(RuntimeError):
            self._call_with_retry("submit_audit", payload, timeout=10.0)

    def poll_audit(self, timeout: float) -> dict[str, Any] | None:
        """Pop an inbound audit, or None on timeout."""
        try:
            return self._inboxes.audits.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_control(self, message: dict[str, Any]) -> None:
        """Push a control frame; ignore a dead opponent."""
        with contextlib.suppress(RuntimeError):
            self._call_with_retry("receive_control", message, timeout=2.0)
