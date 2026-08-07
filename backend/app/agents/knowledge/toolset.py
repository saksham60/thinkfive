"""Knowledge Agent toolset - wraps RAG retrieval as a tool."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.rag.service import RAGService


class KnowledgeToolset:
    """Knowledge Agent tool definitions - RAG retrieval only."""

    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "retrieve_policy",
                    "description": "Retrieve relevant policy/compliance document chunks using hybrid search.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "retrieve_policy":
            results = await self.rag_service.retrieve(
                arguments["query"], top_k=arguments.get("top_k", 5)
            )
            return {"chunks": [r.model_dump() for r in results]}
        raise ValueError(f"Unknown tool: {tool_name}")
