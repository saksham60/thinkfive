from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.banking.node import banking_node
from app.agents.banking.schemas import BankingAgentOutput
from app.agents.banking.toolset import BankingToolset
from app.agents.fraud.node import fraud_node
from app.agents.fraud.schemas import FraudAgentOutput
from app.agents.fraud.toolset import FraudToolset
from app.agents.graph.builder import build_graph
from app.agents.supervisor.node import supervisor_node
from app.agents.supervisor.schemas import SupervisorDecision
from app.agents.synthesis.schemas import SynthesisOutput
from app.agents.tool_loop import run_grounded_tool_loop


def configured_agent(**config: object) -> SimpleNamespace:
    return SimpleNamespace(create_agent=Mock(return_value=config))


def async_llm(*, return_value: object = None, side_effect: object = None) -> SimpleNamespace:
    return SimpleNamespace(
        ainvoke=AsyncMock(return_value=return_value, side_effect=side_effect)
    )


def banking_output(
    *, requires_clarification: bool = False
) -> BankingAgentOutput:
    return BankingAgentOutput(
        goal_completed=not requires_clarification,
        evidence=[],
        findings="Grounded Banking MCP transaction evidence collected.",
        requires_clarification=requires_clarification,
        clarification_question=("Which transaction did you mean?" if requires_clarification else None),
        warnings=[],
    )


def transaction(transaction_id: str) -> dict[str, object]:
    return {
        "transaction_id": transaction_id,
        "amount": 2500,
        "transaction_name": "International Electronics Purchase",
        "date": "2026-08-08",
    }


def tool_call(name: str, arguments: dict[str, object], call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": arguments, "id": call_id}],
    )


async def test_banking_promotes_single_grounded_transaction_id() -> None:
    tool_llm = async_llm(
        side_effect=[
            tool_call("get_recent_transactions", {"limit": 1}, "bank-1"),
            AIMessage(content="Grounded transaction retrieved."),
        ]
    )
    toolset = SimpleNamespace(execute_tool=AsyncMock(return_value=[transaction("real-plaid-id")]))
    agent = configured_agent(
        llm=tool_llm,
        output_llm=async_llm(return_value=banking_output()),
        prompt="banking prompt",
        toolset=toolset,
        version="test",
    )

    result = await banking_node(
        {"current_goal": "Resolve the latest transaction", "messages": []},
        {"configurable": {"banking_agent": agent}},
    )

    assert result["active_transaction_id"] == "real-plaid-id"
    assert result["banking_evidence"]["transaction_resolution_status"] == "resolved"


async def test_client_transaction_id_is_promoted_only_after_exact_banking_validation() -> None:
    toolset = SimpleNamespace(
        execute_tool=AsyncMock(return_value=transaction("txn-client"))
    )
    agent = configured_agent(
        llm=async_llm(return_value=AIMessage(content="Validation complete.")),
        output_llm=async_llm(return_value=banking_output()),
        prompt="banking prompt",
        toolset=toolset,
        version="test",
    )

    result = await banking_node(
        {
            "current_goal": "Validate the selected transaction",
            "messages": [],
            "requested_transaction_id": "txn-client",
            "active_transaction_id": None,
        },
        {"configurable": {"banking_agent": agent}},
    )

    toolset.execute_tool.assert_awaited_once_with(
        "get_transaction", {"transaction_id": "txn-client"}
    )
    assert result["active_transaction_id"] == "txn-client"


async def test_invalid_client_transaction_is_not_promoted_or_sent_to_fraud() -> None:
    banking_toolset = SimpleNamespace(
        execute_tool=AsyncMock(side_effect=ValueError("Transaction was not found for this customer."))
    )
    banking_agent = configured_agent(
        llm=async_llm(),
        output_llm=async_llm(),
        prompt="banking prompt",
        toolset=banking_toolset,
        version="test",
    )

    banking_result = await banking_node(
        {
            "current_goal": "Validate the selected transaction",
            "messages": [],
            "requested_transaction_id": "does-not-exist",
            "active_transaction_id": None,
        },
        {"configurable": {"banking_agent": banking_agent}},
    )
    fraud_agent = SimpleNamespace(create_agent=Mock())
    fraud_result = await fraud_node(
        {**banking_result, "active_transaction_id": None},
        {"configurable": {"fraud_agent": fraud_agent}},
    )

    assert "active_transaction_id" not in banking_result
    assert banking_result["banking_evidence"]["transaction_resolution_status"] == "unresolved"
    fraud_agent.create_agent.assert_not_called()
    assert fraud_result["fraud_evidence"]["assessment_id"] is None


async def test_multiple_banking_transactions_are_not_arbitrarily_promoted() -> None:
    tool_llm = async_llm(
        side_effect=[
            tool_call("get_recent_transactions", {"limit": 20}, "bank-many"),
            AIMessage(content="Multiple transactions remain."),
        ]
    )
    toolset = SimpleNamespace(
        execute_tool=AsyncMock(
            return_value=[transaction("plaid-1"), transaction("plaid-2")]
        )
    )
    agent = configured_agent(
        llm=tool_llm,
        output_llm=async_llm(
            return_value=banking_output(requires_clarification=True)
        ),
        prompt="banking prompt",
        toolset=toolset,
        version="test",
    )

    result = await banking_node(
        {"current_goal": "Resolve the transaction", "messages": []},
        {"configurable": {"banking_agent": agent}},
    )

    assert "active_transaction_id" not in result
    assert result["banking_evidence"]["transaction_resolution_status"] == "ambiguous"


async def test_fraud_uses_verified_transaction_and_only_grounded_result_ids() -> None:
    adapter = SimpleNamespace(
        assess_transaction_risk=AsyncMock(
            return_value={
                "assessment_id": "assessment-real",
                "risk_score": 0.94,
                "severity": "HIGH",
            }
        ),
        create_fraud_alert=AsyncMock(return_value={"alert_id": "alert-real"}),
    )
    toolset = FraudToolset(adapter, "demo_customer_001")
    agent = configured_agent(
        llm=async_llm(
            side_effect=[
                tool_call(
                    "assess_transaction_risk",
                    {"transaction_id": "real-plaid-id"},
                    "fraud-assess",
                ),
                tool_call(
                    "create_fraud_alert",
                    {"assessment_id": "assessment-real"},
                    "fraud-alert",
                ),
                AIMessage(content="Assessment and alert complete."),
            ]
        ),
        output_llm=async_llm(
            return_value=FraudAgentOutput(
                goal_completed=True,
                findings="High risk assessment completed.",
                assessment_id="llm-fabricated-assessment",
                alert_id="llm-fabricated-alert",
                risk_score=0.01,
                severity="LOW",
                requires_case=True,
            )
        ),
        prompt="fraud prompt",
        toolset=toolset,
        version="test",
    )

    result = await fraud_node(
        {
            "current_goal": "Assess this transaction and create an alert if warranted",
            "active_transaction_id": "real-plaid-id",
        },
        {"configurable": {"fraud_agent": agent}},
    )

    adapter.assess_transaction_risk.assert_awaited_once_with(
        customer_id="demo_customer_001",
        transaction_id="real-plaid-id",
        device_id=None,
        channel=None,
    )
    adapter.create_fraud_alert.assert_awaited_once_with(
        assessment_id="assessment-real", customer_id="demo_customer_001"
    )
    assert result["fraud_evidence"]["assessment_id"] == "assessment-real"
    assert result["fraud_evidence"]["risk_score"] == 0.94
    assert result["fraud_evidence"]["severity"] == "HIGH"
    assert result["fraud_evidence"]["alert_id"] == "alert-real"


async def test_fraud_toolset_rejects_non_verified_transaction_id() -> None:
    adapter = SimpleNamespace(assess_transaction_risk=AsyncMock())
    toolset = FraudToolset(adapter, "demo_customer_001")
    toolset.bind_verified_transaction("verified-id")

    with pytest.raises(ValueError, match="does not match"):
        await toolset.execute_tool(
            "assess_transaction_risk", {"transaction_id": "llm-invented-id"}
        )

    adapter.assess_transaction_risk.assert_not_awaited()


async def test_supervisor_prevents_repeating_failed_banking_route() -> None:
    decision = SupervisorDecision(
        next_agent="banking",
        goal="Try the same transaction lookup again",
        reason="Transaction evidence is missing",
        evidence_required=["transaction"],
    )
    llm = async_llm(return_value=decision)
    supervisor_agent = configured_agent(llm=llm, prompt="supervisor prompt", version="test")

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="Check my latest transaction for fraud")],
            "iteration_count": 1,
            "banking_evidence": {
                "findings": "Banking Agent exceeded maximum tool rounds (4)",
                "attempt_status": "failed",
                "transaction_resolution_status": "failed",
            },
        },
        {
            "configurable": {
                "supervisor_agent": supervisor_agent,
                "max_iterations": 15,
            }
        },
    )

    assert result["next_agent"] == "synthesis"
    assert result["pending_human_action"]["type"] == "clarification"
    assert "Repeated unresolved Banking route prevented" in result["warnings"]


def test_specialist_tool_round_limit_remains_four() -> None:
    assert inspect.signature(run_grounded_tool_loop).parameters["max_rounds"].default == 4


async def test_real_banking_id_reaches_fraud_assessment_and_alert_end_to_end() -> None:
    banking_adapter = SimpleNamespace(
        get_transaction=AsyncMock(return_value=transaction("plaid-fraud-001"))
    )
    fraud_adapter = SimpleNamespace(
        assess_transaction_risk=AsyncMock(
            return_value={
                "assessment_id": "assessment-001",
                "risk_score": 0.97,
                "severity": "HIGH",
            }
        ),
        create_fraud_alert=AsyncMock(return_value={"alert_id": "alert-001"}),
    )
    supervisor_llm = async_llm(
        side_effect=[
            SupervisorDecision(
                next_agent="banking",
                goal="Validate the selected transaction",
                reason="A grounded transaction is required",
                evidence_required=["transaction"],
            ),
            SupervisorDecision(
                next_agent="fraud",
                goal="Assess the verified transaction and create an alert if warranted",
                reason="Banking resolved the transaction",
                evidence_required=["risk_assessment", "fraud_alert"],
            ),
            SupervisorDecision(
                next_agent="synthesis",
                goal="Respond with grounded fraud evidence",
                reason="Assessment and alert evidence are available",
            ),
        ]
    )
    banking_agent = configured_agent(
        llm=async_llm(return_value=AIMessage(content="Validated.")),
        output_llm=async_llm(return_value=banking_output()),
        prompt="banking prompt",
        toolset=BankingToolset(banking_adapter, "demo_customer_001"),
        version="test",
    )
    fraud_agent = configured_agent(
        llm=async_llm(
            side_effect=[
                tool_call(
                    "assess_transaction_risk",
                    {"transaction_id": "plaid-fraud-001"},
                    "assess-e2e",
                ),
                tool_call(
                    "create_fraud_alert",
                    {"assessment_id": "assessment-001"},
                    "alert-e2e",
                ),
                AIMessage(content="Grounded fraud work complete."),
            ]
        ),
        output_llm=async_llm(
            return_value=FraudAgentOutput(
                goal_completed=True,
                findings="High-risk transaction assessment and alert created.",
                requires_case=False,
            )
        ),
        prompt="fraud prompt",
        toolset=FraudToolset(fraud_adapter, "demo_customer_001"),
        version="test",
    )
    synthesis_agent = configured_agent(
        llm=async_llm(
            return_value=SynthesisOutput(
                final_response="The transaction was assessed as high risk and an alert was created.",
                workflow_status="RESOLVED",
            )
        ),
        prompt="synthesis prompt",
        version="test",
    )
    graph = build_graph(InMemorySaver())
    thread_id = str(uuid4())

    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="Check this transaction")],
            "conversation_id": str(uuid4()),
            "run_id": str(uuid4()),
            "thread_id": thread_id,
            "customer_id": "demo_customer_001",
            "requested_transaction_id": "plaid-fraud-001",
            "active_transaction_id": None,
            "iteration_count": 0,
            "warnings": [],
            "errors": [],
            "memory_context": {},
        },
        config={
            "configurable": {
                "thread_id": thread_id,
                "max_iterations": 15,
                "supervisor_agent": configured_agent(
                    llm=supervisor_llm, prompt="supervisor prompt", version="test"
                ),
                "banking_agent": banking_agent,
                "fraud_agent": fraud_agent,
                "synthesis_agent": synthesis_agent,
            },
            "recursion_limit": 60,
        },
    )

    banking_adapter.get_transaction.assert_awaited_once_with(
        "demo_customer_001", "plaid-fraud-001"
    )
    fraud_adapter.assess_transaction_risk.assert_awaited_once_with(
        customer_id="demo_customer_001",
        transaction_id="plaid-fraud-001",
        device_id=None,
        channel=None,
    )
    assert result["active_transaction_id"] == "plaid-fraud-001"
    assert result["fraud_evidence"]["assessment_id"] == "assessment-001"
    assert result["fraud_evidence"]["risk_score"] == 0.97
    assert result["fraud_evidence"]["severity"] == "HIGH"
    assert result["fraud_evidence"]["alert_id"] == "alert-001"


async def test_graph_terminates_after_one_failed_banking_attempt() -> None:
    supervisor_llm = async_llm(
        return_value=SupervisorDecision(
            next_agent="banking",
            goal="Resolve a transaction",
            reason="Banking evidence is needed",
            evidence_required=["transaction"],
        )
    )
    banking_llm = async_llm(
        side_effect=RuntimeError("Agent exceeded maximum tool rounds (4)")
    )
    synthesis_agent = configured_agent(
        llm=async_llm(
            return_value=SynthesisOutput(
                final_response="I could not resolve a specific transaction. Please provide more details.",
                workflow_status="NEEDS_CLARIFICATION",
            )
        ),
        prompt="synthesis prompt",
        version="test",
    )
    graph = build_graph(InMemorySaver())
    thread_id = str(uuid4())

    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="Check my latest transaction for fraud")],
            "conversation_id": str(uuid4()),
            "run_id": str(uuid4()),
            "thread_id": thread_id,
            "customer_id": "demo_customer_001",
            "iteration_count": 0,
            "warnings": [],
            "errors": [],
            "memory_context": {},
        },
        config={
            "configurable": {
                "thread_id": thread_id,
                "max_iterations": 15,
                "supervisor_agent": configured_agent(
                    llm=supervisor_llm, prompt="supervisor prompt", version="test"
                ),
                "banking_agent": configured_agent(
                    llm=banking_llm,
                    output_llm=async_llm(),
                    prompt="banking prompt",
                    toolset=SimpleNamespace(execute_tool=AsyncMock()),
                    version="test",
                ),
                "synthesis_agent": synthesis_agent,
            },
            "recursion_limit": 60,
        },
    )

    assert banking_llm.ainvoke.await_count == 1
    assert supervisor_llm.ainvoke.await_count == 2
    assert result["final_response"].startswith("I could not resolve")
    assert "Repeated unresolved Banking route prevented" in result["warnings"]
