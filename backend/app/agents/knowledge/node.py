"""Knowledge Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)


async def knowledge_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Knowledge Agent node - retrieves and grounds policy evidence via RAG."""
    logger.info("Knowledge Agent node executing")

    current_goal = state.get("current_goal", "")
    knowledge_agent = config.get("configurable", {}).get("knowledge_agent")
    if not knowledge_agent:
        raise ValueError("Knowledge Agent not configured")

    # Retrieve first (tool call happens outside the LLM loop for determinism)
    rag_service = knowledge_agent.rag_service
    retrieved = await rag_service.retrieve(current_goal, top_k=5)

    if not retrieved:
        chunks_summary = "(no relevant policy documents retrieved)"
    else:
        chunks_summary = "\n\n".join(
            f"[chunk {i}] document_id={r.document_id} title={r.title} "
            f"version={r.version} section={r.section}\ncontent: {r.content}"
            for i, r in enumerate(retrieved)
        )

    agent_config = knowledge_agent.create_agent(chunks_summary)
    llm = agent_config["llm"]
    prompt = agent_config["prompt"]

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Goal: {current_goal}\n\nAnswer strictly from the retrieved evidence above."),
    ]

    try:
        response = await llm.ainvoke(messages)

        valid_document_ids = {str(item.document_id) for item in retrieved}
        citations = [
            citation.model_dump()
            for citation in response.citations
            if str(citation.document_id) in valid_document_ids
        ]
        policy_evidence = {
            "goal_completed": response.goal_completed,
            "findings": response.findings,
            "citations": citations,
            "retrieved_chunks": [item.model_dump() for item in retrieved],
            "evidence_available": response.evidence_available,
        }

        return {
            "policy_evidence": policy_evidence,
            "warnings": state.get("warnings", []) + response.warnings,
        }

    except Exception as e:
        logger.error(f"Knowledge Agent execution failed: {e}")
        return {"errors": state.get("errors", []) + [f"Knowledge Agent failed: {str(e)}"]}
