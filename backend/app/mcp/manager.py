"""MCP manager for client lifecycle."""

from __future__ import annotations

import logging

from app.core.config import Settings

from .protocol import MCPClient

logger = logging.getLogger(__name__)


class MCPManager:
    """Manager for MCP client instances."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._banking_client: MCPClient | None = None
        self._fraud_client: MCPClient | None = None
        self._case_client: MCPClient | None = None

    def get_banking_client(self) -> MCPClient:
        """Get Banking MCP client."""
        if self._banking_client is None:
            self._banking_client = MCPClient(
                base_url=self.settings.banking_mcp_url,
                auth_token=self.settings.mcp_auth_token.get_secret_value(),
                timeout=self.settings.mcp_timeout,
                max_retries=self.settings.mcp_max_retries,
            )
        return self._banking_client

    def get_fraud_client(self) -> MCPClient:
        """Get Fraud MCP client."""
        if self._fraud_client is None:
            self._fraud_client = MCPClient(
                base_url=self.settings.fraud_mcp_url,
                auth_token=self.settings.mcp_auth_token.get_secret_value(),
                timeout=self.settings.mcp_timeout,
                max_retries=self.settings.mcp_max_retries,
            )
        return self._fraud_client

    def get_case_client(self) -> MCPClient:
        """Get Case MCP client."""
        if self._case_client is None:
            self._case_client = MCPClient(
                base_url=self.settings.case_mcp_url,
                auth_token=self.settings.mcp_auth_token.get_secret_value(),
                timeout=self.settings.mcp_timeout,
                max_retries=self.settings.mcp_max_retries,
            )
        return self._case_client

    async def close_all(self) -> None:
        """Close all MCP clients."""
        for client in [self._banking_client, self._fraud_client, self._case_client]:
            if client:
                await client.close()

    async def initialize(self) -> None:
        """Connect and negotiate all three MCP sessions once during lifespan startup."""
        clients = [self.get_banking_client(), self.get_fraud_client(), self.get_case_client()]
        initialized: list[MCPClient] = []
        try:
            for client in clients:
                await client.initialize()
                initialized.append(client)
        except Exception:
            for client in reversed(initialized):
                await client.close()
            raise

    @property
    def initialized(self) -> bool:
        return all(
            client is not None and client.initialized
            for client in (self._banking_client, self._fraud_client, self._case_client)
        )
