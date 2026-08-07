"""Fraud Agent construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prompt import PROMPT_VERSION, build_prompt
from .schemas import FraudAgentOutput
from .toolset import FraudToolset

if TYPE_CHECKING:
    from app.llm.port import LLMProvider
    from app.mcp.adapters.fraud import FraudMCPAdapter


class FraudAgent:
    """Fraud Agent for risk assessment and alert management."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        fraud_adapter: FraudMCPAdapter,
        customer_id: str,
    ) -> None:
        self.llm_provider = llm_provider
        self.fraud_adapter = fraud_adapter
        self.customer_id = customer_id
        self.toolset = FraudToolset(fraud_adapter)
        self.prompt_version = PROMPT_VERSION

    def create_agent(self, transaction_context: str | None = None) -> dict[str, Any]:
        prompt = build_prompt(self.customer_id, transaction_context)
        llm = self.llm_provider.get_llm(temperature=0.0)
        tools = self.toolset.get_tool_definitions()
        agent_llm = llm.bind_tools(tools)
        structured_llm = agent_llm.with_structured_output(FraudAgentOutput)

        return {
            "llm": structured_llm,
            "prompt": prompt,
            "tools": tools,
            "toolset": self.toolset,
            "version": self.prompt_version,
        }
