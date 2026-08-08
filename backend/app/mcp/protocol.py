"""FastMCP Streamable HTTP client and central response normalization."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastmcp import Client

from app.core.exceptions import MCPError

logger = logging.getLogger(__name__)


class MCPClient:
    """Long-lived FastMCP client for one deployed Streamable HTTP endpoint."""

    def __init__(self, base_url: str, auth_token: str, timeout: int = 60, max_retries: int = 3) -> None:
        self.base_url = f"{base_url.rstrip('/')}/"
        self._auth_token = auth_token
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = self._new_client()
        self._connected = False
        self._generation = 0
        self._lifecycle_lock = asyncio.Lock()

    def _new_client(self) -> Client:
        return Client(self.base_url, auth=self._auth_token)

    @property
    def initialized(self) -> bool:
        return self._connected

    async def initialize(self) -> None:
        async with self._lifecycle_lock:
            if self._connected:
                return
            await self._client.__aenter__()
            try:
                await self._client.ping()
            except Exception:
                await self._client.__aexit__(None, None, None)
                raise
            self._connected = True
            self._generation += 1

    async def close(self) -> None:
        async with self._lifecycle_lock:
            if self._connected:
                await self._client.__aexit__(None, None, None)
                self._connected = False

    async def __aenter__(self) -> MCPClient:
        await self.initialize()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _require_connected(self) -> None:
        if not self._connected:
            raise MCPError("MCP client is not initialized", code="MCP_NOT_INITIALIZED")

    async def list_tools(self) -> list[dict[str, Any]]:
        self._require_connected()
        try:
            tools = await self._client.list_tools()
            return [tool.model_dump(mode="json") if hasattr(tool, "model_dump") else dict(tool) for tool in tools]
        except Exception as exc:
            raise MCPError(f"Failed to list MCP tools: {exc}", code="MCP_LIST_TOOLS_FAILED") from exc

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        self._require_connected()
        for attempt in range(2):
            client = self._client
            generation = self._generation
            try:
                result = await client.call_tool(
                    tool_name, arguments or {}, timeout=float(self.timeout)
                )
                if getattr(result, "is_error", False):
                    raise MCPError(
                        self._content_text(result) or f"MCP tool {tool_name} failed",
                        code="MCP_TOOL_ERROR",
                    )
                payload = getattr(result, "data", None)
                if payload is None:
                    text = self._content_text(result)
                    payload = json.loads(text) if text else None
                return self._normalize_envelope(tool_name, payload)
            except MCPError:
                raise
            except Exception as exc:
                if attempt == 0 and self._is_stale_session_error(exc):
                    logger.warning(
                        "MCP session expired for %s; reconnecting once", self.base_url
                    )
                    await self._reconnect_if_current(client, generation)
                    continue
                logger.error("MCP tool call failed: %s - %s", tool_name, exc)
                raise MCPError(
                    f"MCP tool call failed: {tool_name}: {exc}",
                    code="MCP_CALL_FAILED",
                ) from exc
        raise MCPError(
            f"MCP tool call failed after session recovery: {tool_name}",
            code="MCP_CALL_FAILED",
        )

    async def _reconnect_if_current(self, stale_client: Client, generation: int) -> None:
        """Replace a session invalidated by an upstream MCP restart.

        The generation check prevents a burst of concurrent failed dashboard
        calls from each creating a separate replacement session.
        """
        async with self._lifecycle_lock:
            if self._client is not stale_client or self._generation != generation:
                return

            self._connected = False
            try:
                await stale_client.__aexit__(None, None, None)
            except Exception as exc:
                logger.debug("Failed to close stale MCP session cleanly: %s", exc)

            replacement = self._new_client()
            self._client = replacement
            try:
                await replacement.__aenter__()
                await replacement.ping()
            except Exception:
                try:
                    await replacement.__aexit__(None, None, None)
                except Exception:
                    pass
                raise

            self._connected = True
            self._generation += 1

    @staticmethod
    def _is_stale_session_error(exc: Exception) -> bool:
        """Recognize HTTP 404 responses produced for expired MCP session IDs."""
        current: BaseException | None = exc
        for _ in range(4):
            if current is None:
                break
            response = getattr(current, "response", None)
            status_code = getattr(response, "status_code", None) or getattr(
                current, "status_code", None
            )
            if status_code == 404:
                return True
            message = str(current).casefold()
            if "404" in message and ("not found" in message or "session" in message):
                return True
            current = current.__cause__ or current.__context__
        return False

    @staticmethod
    def _content_text(result: Any) -> str:
        parts = [getattr(item, "text", "") for item in (getattr(result, "content", None) or [])]
        return "\n".join(part for part in parts if part)

    @staticmethod
    def _normalize_envelope(tool_name: str, payload: Any) -> Any:
        if not isinstance(payload, dict) or "success" not in payload:
            return payload
        if payload.get("success") is True:
            return payload.get("data")
        code = str(payload.get("error_code") or "MCP_TOOL_ERROR")
        message = str(payload.get("message") or f"MCP tool {tool_name} failed")
        raise MCPError(message, code=code, retryable=bool(payload.get("retryable", False)))
