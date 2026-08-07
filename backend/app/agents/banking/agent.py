"""Banking Agent construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prompt import PROMPT_VERSION, build_prompt
from .schemas import BankingAgentOutput
from .toolset import BankingToolset

if TYPE_CHECKING:
    from app.llm.port import LLMProvider
    from app.mcp.adapters.banking import BankingMCPAdapter


class BankingAgent:
    """Banking Agent for retrieving banking data."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        banking_adapter: BankingMCPAdapter,
        customer_id: str,
    ) -> None:
        self.llm_provider = llm_provider
        self.banking_adapter = banking_adapter
        self.customer_id = customer_id
        self.toolset = BankingToolset(banking_adapter)
        self.prompt_version = PROMPT_VERSION

    def create_agent(self) -> Any:
        """Create configured Banking Agent with tools and structured output."""
        # Build prompt
        prompt = build_prompt(self.customer_id)

        # Get LLM from provider
        llm = self.llm_provider.get_llm(temperature=0.0)

        # Attach tools
        tools = self.toolset.get_tool_definitions()
        agent_llm = llm.bind_tools(tools)

        # Bind structured output schema
        structured_llm = agent_llm.with_structured_output(BankingAgentOutput)

        return {
            "llm": structured_llm,
            "prompt": prompt,
            "tools": tools,
            "toolset": self.toolset,
            "version": self.prompt_version,
        }
