from __future__ import annotations

import hashlib
import json
from typing import Any

from plaidbanking.app.container import Container
from plaidbanking.app.repositories.item_repository import ItemNotFoundError

SUPPORTED_TRANSACTION_CODES = {"SYNC_UPDATES_AVAILABLE", "INITIAL_UPDATE", "HISTORICAL_UPDATE", "DEFAULT_UPDATE", "TRANSACTIONS_REMOVED"}


async def handle_webhook(container: Container, raw_body: bytes) -> tuple[dict[str, Any], int]:
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"accepted": False, "error": "Malformed JSON body."}, 400
    if not isinstance(payload, dict):
        return {"accepted": False, "error": "Webhook body must be a JSON object."}, 400
    item_id = payload.get("item_id")
    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")
    event_id = hashlib.sha256(raw_body).hexdigest()
    if not await container.webhook_events.claim(event_id, 600):
        return {"accepted": True, "duplicate": True}, 200
    if webhook_type != "TRANSACTIONS" or webhook_code not in SUPPORTED_TRANSACTION_CODES:
        return {"accepted": True, "handled": False}, 200
    if not isinstance(item_id, str):
        return {"accepted": False, "error": "Missing Item identifier."}, 400
    try:
        customer_id = await container.items.get_customer_id(item_id)
    except ItemNotFoundError:
        return {"accepted": True, "handled": False, "reason": "unknown_item"}, 202
    await container.sync_states.mark_stale(customer_id)
    return {"accepted": True, "handled": True}, 200
