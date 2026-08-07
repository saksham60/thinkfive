"""MCP client manager and protocol."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.exceptions import MCPError

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP client using Streamable HTTP protocol."""

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        timeout: int = 60,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> MCPClient:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None:
            raise MCPError("Client not initialized - use async context manager")
        return self._client

    async def initialize(self) -> dict[str, Any]:
        """Initialize MCP connection."""
        try:
            response = await self.client.post(
                f"{self.base_url}/init",
                json={},
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise MCPError(f"MCP initialization failed: {e}")

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools."""
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/list",
                json={},
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])
        except httpx.HTTPError as e:
            raise MCPError(f"Failed to list tools: {e}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call MCP tool."""
        try:
            payload = {
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {},
                }
            }
            response = await self.client.post(
                f"{self.base_url}/tools/call",
                json=payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )
            response.raise_for_status()
            result = response.json()

            # Extract content from MCP envelope
            if "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict) and "text" in first_content:
                        import json

                        return json.loads(first_content["text"])

            return result

        except httpx.HTTPError as e:
            logger.error(f"MCP tool call failed: {tool_name} - {e}")
            raise MCPError(f"MCP tool call failed: {tool_name} - {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling MCP tool {tool_name}: {e}")
            raise MCPError(f"Unexpected error: {e}")
