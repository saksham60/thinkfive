"""Supervisor Agent toolset.

The Supervisor does not call MCP tools directly - it only routes. This
module exists for structural consistency and future extension (e.g.,
inspecting run metadata).
"""

from __future__ import annotations

from typing import Any


class SupervisorToolset:
    """Supervisor has no external tools - routing only."""

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return []
