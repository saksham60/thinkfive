"""Case Agent construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prompt import PROMPT_VERSION, build_prompt
from .schemas import CaseAgentOutput
from .toolset import CaseToolset

if TYPE_CHECKING:
    from app.llm.port import LLMProvider
    from app.mcp.adapters.case import CaseMCPAdapter


class CaseAgent:
    """Case Agent for case management and approval requests (never approvals themselves)."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        case_adapter: CaseMCPAdapter,
        customer_id: str,
    ) -> None:
        self.llm_provider = llm_provider
        self.case_adapter = case_adapter
        self.customer_id = customer_id
        self.toolset = CaseToolset(case_adapter)
        self.prompt_version = PROMPT_VERSION

    def create_agent(self) -> dict[str, Any]:
        prompt = build_prompt(self.customer_id)
        llm = self.llm_provider.get_llm(temperature=0.0)
        tools = self.toolset.get_tool_definitions()
        agent_llm = llm.bind_tools(tools)
        structured_llm = agent_llm.with_structured_output(CaseAgentOutput)

        return {
            "llm": structured_llm,
            "prompt": prompt,
            "tools": tools,
            "toolset": self.toolset,
            "version": self.prompt_version,
        }
