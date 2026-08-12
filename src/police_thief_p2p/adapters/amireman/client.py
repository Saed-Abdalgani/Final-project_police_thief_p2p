"""Outbound push client to the opponent's amireman MCP endpoint."""

from __future__ import annotations

import asyncio
import contextlib
import queue
import time
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from police_thief_p2p.adapters.amireman.queues import PeerInboxes


class McpTransport:
    """Push to opponent; pull from own inboxes."""

    def __init__(
        self,
        opponent_url: str,
        inboxes: PeerInboxes,
        *,
        connect_timeout: float = 60.0,
        retry_interval: float = 1.0,
    ) -> None:
        self._url = opponent_url
        self._inboxes = inboxes
        self._connect_timeout = connect_timeout
        self._retry = retry_interval

    def _call(self, tool: str, argument: dict[str, Any]) -> None:
        key = "payload" if tool == "submit_audit" else "message"

        async def invoke() -> None:
            async with Client(StreamableHttpTransport(self._url)) as client:
                await client.call_tool(tool, {key: argument})

        asyncio.run(invoke())

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
        self._call_with_retry("negotiate", signed)
        try:
            return self._inboxes.agreements.get(timeout=self._connect_timeout)
        except queue.Empty as exc:
            raise RuntimeError("opponent never sent its agreement") from exc

    def send_turn(self, message: dict[str, Any]) -> None:
        self._call_with_retry("receive_turn", message)

    def poll_turn(self, timeout: float) -> dict[str, Any] | None:
        try:
            return self._inboxes.turns.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_audit(self, payload: dict[str, Any]) -> None:
        with contextlib.suppress(RuntimeError):
            self._call_with_retry("submit_audit", payload, timeout=10.0)

    def poll_audit(self, timeout: float) -> dict[str, Any] | None:
        try:
            return self._inboxes.audits.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_control(self, message: dict[str, Any]) -> None:
        with contextlib.suppress(RuntimeError):
            self._call_with_retry("receive_control", message, timeout=2.0)
