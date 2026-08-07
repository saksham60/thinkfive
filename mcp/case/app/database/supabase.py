from __future__ import annotations

from typing import Any

from case.app.config import Settings
from common.supabase import create_data_client


def create_supabase_client(settings: Settings) -> Any:
    return create_data_client(settings.supabase_url, settings.service_key.get_secret_value())
