from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from case.app.errors import CaseMcpError
from case.app.models.domain import now


def serial(v: Any) -> Any:
    if isinstance(v, BaseModel):
        return v.model_dump(mode="json")
    if isinstance(v, list):
        return [serial(x) for x in v]
    if isinstance(v, dict):
        return {k: serial(x) for k, x in v.items()}
    return v


async def response(op: Callable[[], Awaitable[Any]]) -> dict[str, Any]:
    try:
        return {"success": True, "source": "case_mcp_supabase", "retrieved_at": now().isoformat(), "data": serial(await op()), "warnings": []}
    except CaseMcpError as e:
        return {"success": False, "error_code": e.code, "message": e.safe_message, "retryable": e.retryable}
    except (ValueError, ValidationError):
        return {"success": False, "error_code": "INVALID_INPUT", "message": "One or more inputs are invalid.", "retryable": False}
    except Exception:
        return {"success": False, "error_code": "INTERNAL_ERROR", "message": "The case workflow could not be completed safely.", "retryable": True}
