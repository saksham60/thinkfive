from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from fraudMCP.app.errors import InvalidInputError
from fraudMCP.app.models.blacklist import BlacklistCheckResult


class BlacklistProvider(Protocol):
    async def check(self, entity_type: str, value: str) -> BlacklistCheckResult: ...


class InMemoryBlacklistProvider(BlacklistProvider):
    ALLOWED_ENTITY_TYPES = frozenset({"merchant", "account", "device", "ip", "email", "phone"})

    def __init__(self, data_path: Path) -> None:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        self._source = str(raw.get("source") or "synthetic_demo_data")
        self._list_name = str(raw.get("list_name") or "demo_blacklist")
        self._entries: dict[tuple[str, str], dict[str, Any]] = {}
        for entry in raw.get("entries", []):
            normalized_type = self._normalize_entity_type(str(entry.get("entity_type", "")))
            normalized_value = self._normalize_value(str(entry.get("value", "")))
            if not normalized_type or not normalized_value:
                continue
            self._entries[(normalized_type, normalized_value)] = {
                "reason": str(entry.get("reason") or "listed entity"),
                "metadata": self._safe_metadata(entry.get("metadata")),
            }

    async def check(self, entity_type: str, value: str) -> BlacklistCheckResult:
        normalized_type = self._normalize_entity_type(entity_type)
        if normalized_type not in self.ALLOWED_ENTITY_TYPES:
            raise InvalidInputError(f"entity_type must be one of: {', '.join(sorted(self.ALLOWED_ENTITY_TYPES))}")

        normalized_value = self._normalize_value(value)
        if not normalized_value:
            raise InvalidInputError("value must not be empty")

        record = self._entries.get((normalized_type, normalized_value))
        if record is None:
            return BlacklistCheckResult(
                entity_type=normalized_type,
                value=self._display_value(normalized_type, value),
                matched=False,
                list_name=self._list_name,
                source=self._source,
            )

        return BlacklistCheckResult(
            entity_type=normalized_type,
            value=self._display_value(normalized_type, value),
            matched=True,
            reason=str(record.get("reason") or "listed entity"),
            list_name=self._list_name,
            source=self._source,
            metadata=record.get("metadata"),
        )

    @staticmethod
    def _normalize_entity_type(value: str) -> str:
        return value.strip().casefold()

    @staticmethod
    def _normalize_value(value: str) -> str:
        return value.strip().casefold()

    @staticmethod
    def _safe_metadata(metadata: Any) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None
        safe: dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                safe[str(key)] = value
        return safe or None

    @staticmethod
    def _display_value(entity_type: str, value: str) -> str:
        stripped = value.strip()
        if entity_type in {"email", "phone"} and len(stripped) > 4:
            return f"***{stripped[-4:]}"
        return stripped
