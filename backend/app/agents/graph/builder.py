"""LangGraph graph builder - wires all agent nodes into the state graph."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agents.banking.node import banking_node
from app.agents.case.node import case_node
from app.agents.fraud.node import fraud_node
from app.agents.graph.checkpoint import hitl_interrupt_node
from app.agents.graph.routing import route_after_specialist, route_from_supervisor
from app.agents.graph.state import GraphState
from app.agents.knowledge.node import knowledge_node
from app.agents.supervisor.node import supervisor_node
from app.agents.synthesis.node import synthesis_node


def build_graph(checkpointer: BaseCheckpointSaver) -> Any:
    """Build and compile the ThinkFive multi-agent LangGraph.

    Nodes: supervisor -> {banking, fraud, knowledge, case} -> supervisor (loop)
           specialist -> hitl_interrupt (when approval pending) -> supervisor
           supervisor -> synthesis -> END
    """
    graph = StateGraph(GraphState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("banking", banking_node)
    graph.add_node("fraud", fraud_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("case", case_node)
    graph.add_node("hitl_interrupt", hitl_interrupt_node)
    graph.add_node("synthesis", synthesis_node)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "banking": "banking",
            "fraud": "fraud",
            "knowledge": "knowledge",
            "case": "case",
            "synthesis": "synthesis",
        },
    )

    for specialist in ("banking", "fraud", "knowledge"):
        graph.add_edge(specialist, "supervisor")

    # Case agent may trigger a HITL interrupt (approval requested)
    graph.add_conditional_edges(
        "case",
        route_after_specialist,
        {
            "hitl_interrupt": "hitl_interrupt",
            "supervisor": "supervisor",
        },
    )
    graph.add_edge("hitl_interrupt", "supervisor")

    graph.add_edge("synthesis", END)

    return graph.compile(checkpointer=checkpointer)
