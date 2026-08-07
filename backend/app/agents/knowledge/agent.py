"""Knowledge Agent construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .prompt import PROMPT_VERSION, build_prompt
from .schemas import KnowledgeAgentOutput
from .toolset import KnowledgeToolset

if TYPE_CHECKING:
    from app.llm.port import LLMProvider
    from app.rag.service import RAGService


class KnowledgeAgent:
    """Knowledge Agent for RAG-grounded policy retrieval."""

    def __init__(self, llm_provider: LLMProvider, rag_service: RAGService) -> None:
        self.llm_provider = llm_provider
        self.rag_service = rag_service
        self.toolset = KnowledgeToolset(rag_service)
        self.prompt_version = PROMPT_VERSION

    def create_agent(self, retrieved_chunks_summary: str) -> dict[str, Any]:
        prompt = build_prompt(retrieved_chunks_summary)
        llm = self.llm_provider.get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(KnowledgeAgentOutput)

        return {
            "llm": structured_llm,
            "prompt": prompt,
            "toolset": self.toolset,
            "version": self.prompt_version,
        }
