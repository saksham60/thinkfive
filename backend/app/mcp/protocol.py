"""FastMCP Streamable HTTP client and central response normalization."""

from __future__ import annotations

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
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = Client(self.base_url, auth=auth_token)
        self._connected = False

    @property
    def initialized(self) -> bool:
        return self._connected

    async def initialize(self) -> None:
        if self._connected:
            return
        await self._client.__aenter__()
        try:
            await self._client.ping()
        except Exception:
            await self._client.__aexit__(None, None, None)
            raise
        self._connected = True

    async def close(self) -> None:
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
        try:
            result = await self._client.call_tool(tool_name, arguments or {}, timeout=float(self.timeout))
            if getattr(result, "is_error", False):
                raise MCPError(self._content_text(result) or f"MCP tool {tool_name} failed", code="MCP_TOOL_ERROR")
            payload = getattr(result, "data", None)
            if payload is None:
                text = self._content_text(result)
                payload = json.loads(text) if text else None
            return self._normalize_envelope(tool_name, payload)
        except MCPError:
            raise
        except Exception as exc:
            logger.error("MCP tool call failed: %s - %s", tool_name, exc)
            raise MCPError(f"MCP tool call failed: {tool_name}: {exc}", code="MCP_CALL_FAILED") from exc

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
