"""Synthesis Agent construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prompt import PROMPT_VERSION, build_prompt
from .schemas import SynthesisOutput

if TYPE_CHECKING:
    from app.llm.port import LLMProvider


class SynthesisAgent:
    """Synthesis Agent - produces the final grounded customer response."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider
        self.prompt_version = PROMPT_VERSION

    def create_agent(self, evidence_bundle: str) -> dict[str, Any]:
        prompt = build_prompt(evidence_bundle)
        llm = self.llm_provider.get_llm(temperature=0.1)
        structured_llm = llm.with_structured_output(SynthesisOutput)

        return {
            "llm": structured_llm,
            "prompt": prompt,
            "version": self.prompt_version,
        }
