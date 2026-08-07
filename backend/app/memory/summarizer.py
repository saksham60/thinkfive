"""Conversation summarizer - prevents unbounded prompt context growth."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.conversation.entities import Message
    from app.llm.port import LLMProvider

logger = logging.getLogger(__name__)

SUMMARIZATION_PROMPT = """Summarize the following conversation between a customer and a banking
assistant. Preserve key facts, decisions, and references (account details discussed, cases/alerts
mentioned, customer preferences). Be concise - target 150 words or fewer.

Conversation:
{transcript}

Summary:"""


class ConversationSummarizer:
    """Summarizes older conversation turns while preserving original persisted messages."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    async def summarize(self, messages: list[Message]) -> str:
        """Produce a summary of the given messages. Originals remain persisted untouched."""
        transcript = "\n".join(f"{m.role}: {m.content}" for m in messages)
        prompt = SUMMARIZATION_PROMPT.format(transcript=transcript)

        llm = self.llm_provider.get_llm(temperature=0.0)
        response = await llm.ainvoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def should_summarize(self, message_count: int, threshold: int) -> bool:
        return message_count >= threshold
