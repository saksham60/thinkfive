"""Per-agent architecture tests (section 66) - every agent has the required files."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).parent.parent.parent / "app" / "agents"
TOOL_USING_AGENTS = ["banking", "fraud", "knowledge", "case"]
ALL_AGENTS = ["supervisor", "banking", "fraud", "knowledge", "case", "synthesis"]


class TestAgentArchitecture:
    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_agent_has_prompt_module(self, agent_name: str) -> None:
        module = importlib.import_module(f"app.agents.{agent_name}.prompt")
        assert hasattr(module, "PROMPT_VERSION")
        assert hasattr(module, "DEFAULT_SYSTEM_PROMPT")
        assert hasattr(module, "build_prompt")

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_agent_has_schemas_module(self, agent_name: str) -> None:
        module = importlib.import_module(f"app.agents.{agent_name}.schemas")
        assert module is not None

    @pytest.mark.parametrize("agent_name", TOOL_USING_AGENTS)
    def test_tool_using_agent_has_toolset_module(self, agent_name: str) -> None:
        module = importlib.import_module(f"app.agents.{agent_name}.toolset")
        assert module is not None

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_agent_has_agent_module(self, agent_name: str) -> None:
        module = importlib.import_module(f"app.agents.{agent_name}.agent")
        assert module is not None

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_agent_has_node_module(self, agent_name: str) -> None:
        module = importlib.import_module(f"app.agents.{agent_name}.node")
        assert module is not None

    def test_no_giant_global_prompts_file_exists(self) -> None:
        """Ensure no giant agents/prompts.py exists (non-negotiable rule)."""
        assert not (AGENTS_DIR / "prompts.py").exists()

    def test_no_giant_global_agents_file_exists(self) -> None:
        assert not (AGENTS_DIR / "agents.py").exists()
