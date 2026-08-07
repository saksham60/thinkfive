"""Supabase client wrapper (used for storage / auxiliary features)."""

from __future__ import annotations

import logging

from supabase import Client, create_client

from app.core.config import Settings

logger = logging.getLogger(__name__)


class SupabaseClientFactory:
    """Factory for Supabase client (service-role)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Client | None = None

    def get_client(self) -> Client:
        """Get or create Supabase client with service-role credentials."""
        if self._client is None:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key.get_secret_value(),
            )
            logger.info("Supabase client initialized")
        return self._client
