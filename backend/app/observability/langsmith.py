"""LangSmith trace formatting with conservative secret redaction."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, SecretStr

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
    "session",
    "token",
)
_SECRET_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)((?:api[_-]?key|password|secret|token)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\b(?:sk|lsv2|mcp)_[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)
_MAX_STRING_LENGTH = 50_000
_MAX_SEQUENCE_LENGTH = 200


def _redact_text(value: str) -> str:
    text = value[:_MAX_STRING_LENGTH]
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]" if match.lastindex else "[REDACTED]", text)
    if len(value) > _MAX_STRING_LENGTH:
        text += f"\n[TRUNCATED {len(value) - _MAX_STRING_LENGTH} CHARACTERS]"
    return text


def trace_value(value: Any) -> Any:
    """Convert trace data to JSON-safe values while removing credentials."""
    if isinstance(value, SecretStr):
        return "[REDACTED]"
    if isinstance(value, BaseMessage):
        return {
            "role": value.type,
            "content": trace_value(value.content),
            "name": value.name,
        }
    if isinstance(value, BaseModel):
        return trace_value(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(part in str(key).lower() for part in _SENSITIVE_KEY_PARTS)
                else trace_value(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items = list(value)
        serialized = [trace_value(item) for item in items[:_MAX_SEQUENCE_LENGTH]]
        if len(items) > _MAX_SEQUENCE_LENGTH:
            serialized.append(f"[TRUNCATED {len(items) - _MAX_SEQUENCE_LENGTH} ITEMS]")
        return serialized
    if isinstance(value, str):
        return _redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_text(str(value))


def trace_messages(messages: Sequence[BaseMessage]) -> list[dict[str, Any]]:
    """Serialize the exact messages supplied to an LLM, including the system prompt."""
    return [trace_value(message) for message in messages]


def llm_trace_config(agent_name: str, phase: str, prompt_version: str | None = None) -> dict[str, Any]:
    """Build a named RunnableConfig fragment for a LangSmith LLM child span."""
    metadata: dict[str, Any] = {"agent": agent_name, "phase": phase}
    if prompt_version:
        metadata["prompt_version"] = prompt_version
    return {
        "run_name": f"agent.{agent_name}.{phase}",
        "tags": ["thinkfive", f"agent:{agent_name}", f"phase:{phase}"],
        "metadata": metadata,
    }
