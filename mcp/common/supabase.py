from __future__ import annotations

import ssl

import httpx
import truststore
from postgrest import SyncPostgrestClient


def create_data_client(url: str, secret_key: str) -> SyncPostgrestClient:
    """Create a server-only data client compatible with modern sb_secret keys."""
    return SyncPostgrestClient(
        f"{url.rstrip('/')}/rest/v1",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "apikey": secret_key,
        },
        http_client=httpx.Client(
            timeout=15,
            trust_env=False,
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        ),
    )
