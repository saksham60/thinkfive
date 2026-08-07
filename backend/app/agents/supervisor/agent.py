"""Supervisor Agent construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prompt import PROMPT_VERSION, build_prompt
from .schemas import SupervisorDecision
from .toolset import SupervisorToolset

if TYPE_CHECKING:
    from app.llm.port import LLMProvider


class SupervisorAgent:
    """Supervisor Agent - routes to specialist agents using structured output."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider
        self.toolset = SupervisorToolset()
        self.prompt_version = PROMPT_VERSION

    def create_agent(self, evidence_summary: str, iteration_count: int, max_iterations: int) -> dict[str, Any]:
        """Create configured Supervisor with structured routing output."""
        prompt = build_prompt(evidence_summary, iteration_count, max_iterations)
        llm = self.llm_provider.get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(SupervisorDecision)

        return {
            "llm": structured_llm,
            "prompt": prompt,
            "version": self.prompt_version,
        }
