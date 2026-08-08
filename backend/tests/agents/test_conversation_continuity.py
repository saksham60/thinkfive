from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.banking.node import banking_node
from app.agents.banking.schemas import BankingAgentOutput
from app.agents.banking.toolset import BankingToolset
from app.agents.fraud.schemas import FraudAgentOutput
from app.agents.fraud.toolset import FraudToolset
from app.agents.graph.builder import build_graph
from app.agents.graph.runner import GraphRunner
from app.agents.graph.state import GraphState
from app.agents.supervisor.node import supervisor_node
from app.agents.supervisor.schemas import SupervisorDecision
from app.agents.synthesis.schemas import SynthesisOutput


def configured_agent(**config: object) -> SimpleNamespace:
    return SimpleNamespace(create_agent=Mock(return_value=config))


async def test_five_turn_checkpoint_has_no_duplicate_messages_and_preserves_active_entity() -> None:
    async def respond(state: GraphState) -> dict:
        latest = state["messages"][-1].content
        update = {
            "final_response": f"response:{latest}",
            "messages": [AIMessage(content=f"response:{latest}", id=f"ai:{latest}")],
        }
        if latest == "turn-1":
            update["active_transaction_id"] = "txn-grounded"
        return update

    builder = StateGraph(GraphState)
    builder.add_node("respond", respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    conversation_id = uuid4()
    thread_id = str(conversation_id)
    conversation_repo = SimpleNamespace(
        has_assistant_message_for_run=AsyncMock(return_value=False),
        add_message=AsyncMock(),
        get_messages=AsyncMock(return_value=[]),
    )
    runner = GraphRunner(
        graph,
        SimpleNamespace(update_status=AsyncMock()),
        SimpleNamespace(),
        SimpleNamespace(publish=AsyncMock()),
        SimpleNamespace(),
        conversation_repo,
        SimpleNamespace(maybe_summarize=AsyncMock()),
    )

    for position in range(1, 6):
        await runner.start_run(
            run_id=uuid4(),
            conversation_id=conversation_id,
            thread_id=thread_id,
            customer_id="demo_customer_001",
            message=f"turn-{position}",
            message_id=f"user-{position}",
            runtime_context={},
        )

    snapshot = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    messages = snapshot.values["messages"]
    assert [message.content for message in messages] == [
        value
        for position in range(1, 6)
        for value in (f"turn-{position}", f"response:turn-{position}")
    ]
    assert len({message.id for message in messages}) == 10
    assert snapshot.values["active_transaction_id"] == "txn-grounded"


async def test_supervisor_maps_ordinal_to_grounded_candidate_id() -> None:
    decision = SupervisorDecision(
        next_agent="banking",
        goal="Validate the customer's selected transaction",
        primary_user_goal="Assess the selected transaction for fraud",
        reason="The customer selected the second displayed transaction",
        reference_type="ordinal",
        candidate_position=2,
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor prompt",
        version="test",
    )
    candidates = [
        {"position": 1, "transaction_id": "txn-one", "description": "Coffee"},
        {"position": 2, "transaction_id": "txn-two", "description": "Electronics"},
    ]

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="check the second one")],
            "recent_transaction_candidates": candidates,
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["requested_transaction_id"] == "txn-two"
    assert result["primary_user_goal"] == "Assess the selected transaction for fraud"
    assert "pending_human_action" not in result


async def test_pending_confirmation_is_separate_from_operational_hitl() -> None:
    candidate = {"position": 1, "transaction_id": "txn-one", "description": "Coffee"}
    decision = SupervisorDecision(
        next_agent="banking",
        goal="Validate the confirmed transaction",
        reason="The customer accepted the pending selection",
        reference_type="pending_confirmation",
        confirmation="accept",
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor prompt",
        version="test",
    )

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="yes, that one")],
            "pending_confirmation": {
                "type": "transaction_selection",
                "candidate": candidate,
                "question": "Did you mean Coffee?",
                "continuation_goal": "Report the selected transaction as fraud",
                "customer_requested_formal_case": True,
            },
            "recent_transaction_candidates": [candidate],
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["requested_transaction_id"] == "txn-one"
    assert result["pending_confirmation"] is None
    assert result["current_goal"] == "Report the selected transaction as fraud"
    assert result["primary_user_goal"] == "Report the selected transaction as fraud"
    assert result["customer_requested_formal_case"] is True
    assert "pending_human_action" not in result


async def test_supervisor_routes_confirmed_customer_report_to_case_after_medium_assessment() -> None:
    decision = SupervisorDecision(
        next_agent="synthesis",
        goal="Summarize the completed medium-risk assessment",
        primary_user_goal="Report my last transaction as fraud",
        reason="The fraud assessment is complete",
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor prompt",
        version="test",
    )

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="yes please")],
            "active_transaction_id": "txn-125",
            "requested_transaction_id": "txn-125",
            "primary_user_goal": "Report my last transaction as fraud",
            "customer_requested_formal_case": True,
            "fraud_evidence": {
                "assessment_id": "assessment-medium",
                "alert_id": None,
                "risk_score": 0.5,
                "severity": "MEDIUM",
                "requires_case": False,
                "transaction_id": "txn-125",
                "findings": "Medium risk assessment completed.",
            },
            "iteration_count": 2,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["next_agent"] == "case", result
    assert "TRANSACTION_DISPUTE" in result["current_goal"]
    assert "Do not ask" in result["current_goal"]
    assert result["customer_requested_formal_case"] is True


async def test_banking_preserves_mcp_order_as_structured_candidates() -> None:
    transactions = [
        {
            "transaction_id": "txn-newest",
            "transaction_name": "Groceries",
            "amount": 42.5,
            "date": "2026-08-08",
        },
        {
            "transaction_id": "txn-older",
            "merchant_name": "Coffee Shop",
            "amount": 8.25,
            "date": "2026-08-07",
        },
    ]
    tool_response = AIMessage(
        content="",
        tool_calls=[
            {"name": "get_recent_transactions", "args": {"limit": 10}, "id": "recent"}
        ],
    )
    output = BankingAgentOutput(
        goal_completed=True,
        evidence=[],
        findings="Recent transactions retrieved.",
        requires_clarification=True,
        clarification_question="Which transaction?",
    )
    agent = configured_agent(
        llm=SimpleNamespace(
            ainvoke=AsyncMock(side_effect=[tool_response, AIMessage(content="done")])
        ),
        output_llm=SimpleNamespace(ainvoke=AsyncMock(return_value=output)),
        prompt="banking prompt",
        toolset=SimpleNamespace(execute_tool=AsyncMock(return_value=transactions)),
        version="test",
    )

    result = await banking_node(
        {"current_goal": "Show recent transactions", "messages": []},
        {"configurable": {"banking_agent": agent}},
    )

    assert [candidate["transaction_id"] for candidate in result["recent_transaction_candidates"]] == [
        "txn-newest",
        "txn-older",
    ]
    assert [candidate["position"] for candidate in result["recent_transaction_candidates"]] == [1, 2]
    assert "active_transaction_id" not in result


async def test_exact_reference_validation_skips_redundant_banking_llm_calls() -> None:
    toolset = SimpleNamespace(
        execute_tool=AsyncMock(
            return_value={"transaction_id": "txn-two", "transaction_name": "Electronics"}
        )
    )
    tool_llm = SimpleNamespace(ainvoke=AsyncMock())
    output_llm = SimpleNamespace(ainvoke=AsyncMock())
    agent = configured_agent(
        llm=tool_llm,
        output_llm=output_llm,
        prompt="banking prompt",
        toolset=toolset,
        version="test",
    )

    result = await banking_node(
        {
            "current_goal": "Validate the selected transaction",
            "messages": [],
            "requested_transaction_id": "txn-two",
            "recent_transaction_candidates": [
                {"position": 2, "transaction_id": "txn-two", "description": "Electronics"}
            ],
        },
        {"configurable": {"banking_agent": agent}},
    )

    toolset.execute_tool.assert_awaited_once_with("get_transaction", {"transaction_id": "txn-two"})
    tool_llm.ainvoke.assert_not_awaited()
    output_llm.ainvoke.assert_not_awaited()
    assert result["active_transaction_id"] == "txn-two"
    assert result["active_transaction"]["position"] == 2


async def test_greeting_routes_directly_to_natural_synthesis_without_specialists() -> None:
    supervisor_llm = SimpleNamespace(
        ainvoke=AsyncMock(
            return_value=SupervisorDecision(
                next_agent="synthesis",
                goal="Reply naturally to the greeting",
                reason="No banking evidence or action is required",
            )
        )
    )
    synthesis_llm = SimpleNamespace(
        ainvoke=AsyncMock(
            return_value=SynthesisOutput(
                final_response="Hi! How can I help with your banking today?",
                workflow_status="RESOLVED",
            )
        )
    )
    banking_agent = SimpleNamespace(create_agent=Mock())
    fraud_agent = SimpleNamespace(create_agent=Mock())
    case_agent = SimpleNamespace(create_agent=Mock())
    graph = build_graph(InMemorySaver())
    thread_id = str(uuid4())

    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="hi")],
            "run_id": str(uuid4()),
            "thread_id": thread_id,
            "customer_id": "customer-a",
            "iteration_count": 0,
        },
        config={
            "configurable": {
                "thread_id": thread_id,
                "max_iterations": 15,
                "supervisor_agent": configured_agent(
                    llm=supervisor_llm, prompt="supervisor", version="test"
                ),
                "synthesis_agent": configured_agent(
                    llm=synthesis_llm, prompt="synthesis", version="test"
                ),
                "banking_agent": banking_agent,
                "fraud_agent": fraud_agent,
                "case_agent": case_agent,
            }
        },
    )

    assert result["final_response"].startswith("Hi!")
    banking_agent.create_agent.assert_not_called()
    fraud_agent.create_agent.assert_not_called()
    case_agent.create_agent.assert_not_called()


async def test_unique_partial_reference_uses_grounded_candidate_and_validates_it() -> None:
    decision = SupervisorDecision(
        next_agent="banking",
        goal="Resolve the described transaction",
        reason="One recent candidate matches the merchant",
        reference_type="merchant_amount",
        reference_merchant="Olive Garden",
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor",
        version="test",
    )
    candidates = [
        {"position": 1, "transaction_id": "txn-coffee", "description": "Coffee Shop"},
        {
            "position": 4,
            "transaction_id": "txn-olive",
            "description": "Olive Garden",
            "amount": 121.41,
        },
    ]

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="the Olive Garden one")],
            "recent_transaction_candidates": candidates,
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["next_agent"] == "banking"
    assert result["requested_transaction_id"] == "txn-olive"
    assert result["pending_confirmation"] is None


async def test_invalid_ordinal_never_fabricates_a_candidate() -> None:
    decision = SupervisorDecision(
        next_agent="banking",
        goal="Resolve transaction number 20",
        reason="The customer used an ordinal reference",
        reference_type="ordinal",
        candidate_position=20,
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor",
        version="test",
    )

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="number 20")],
            "recent_transaction_candidates": [
                {"position": 1, "transaction_id": "txn-one"}
            ],
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["next_agent"] == "synthesis"
    assert result.get("requested_transaction_id") is None
    assert result["pending_confirmation"]["type"] == "transaction_details"


async def test_explicit_topic_switch_is_not_blocked_by_prior_transaction_failure() -> None:
    decision = SupervisorDecision(
        next_agent="banking",
        goal="Retrieve the checking account balance",
        reason="The new request is about an account balance",
        reference_type="none",
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor",
        version="test",
    )

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="what is my checking balance?")],
            "run_id": "new-run",
            "active_transaction_id": "txn-previous",
            "banking_evidence": {
                "run_id": "previous-run",
                "attempt_status": "failed",
                "transaction_resolution_status": "failed",
            },
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["next_agent"] == "banking"
    assert "Repeated unresolved Banking route prevented" not in result["warnings"]


async def test_negative_confirmation_clears_candidate_without_selecting_it() -> None:
    decision = SupervisorDecision(
        next_agent="synthesis",
        goal="Ask the customer to choose another transaction",
        reason="The customer rejected the proposed transaction",
        reference_type="pending_confirmation",
        confirmation="reject",
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor",
        version="test",
    )

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="no, not that one")],
            "pending_confirmation": {
                "type": "transaction_selection",
                "candidate": {"position": 4, "transaction_id": "txn-olive"},
            },
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["pending_confirmation"] is None
    assert result.get("requested_transaction_id") is None


async def test_pronoun_continuation_routes_grounded_active_transaction_to_fraud() -> None:
    decision = SupervisorDecision(
        next_agent="fraud",
        goal="Assess the verified active transaction and report it if warranted",
        primary_user_goal="Report the active transaction as fraud",
        reason="The pronoun refers to the verified active transaction",
        reference_type="active_transaction",
    )
    supervisor_agent = configured_agent(
        llm=SimpleNamespace(ainvoke=AsyncMock(return_value=decision)),
        prompt="supervisor",
        version="test",
    )

    result = await supervisor_node(
        {
            "messages": [HumanMessage(content="yes, report it")],
            "active_transaction_id": "txn-olive",
            "active_transaction": {
                "position": 4,
                "transaction_id": "txn-olive",
                "description": "Olive Garden",
                "amount": 121.41,
            },
            "iteration_count": 0,
        },
        {"configurable": {"supervisor_agent": supervisor_agent, "max_iterations": 15}},
    )

    assert result["next_agent"] == "fraud"
    assert result.get("requested_transaction_id") is None
    assert result["primary_user_goal"] == "Report the active transaction as fraud"


async def test_five_turn_conversational_fraud_acceptance_flow() -> None:
    transactions = [
        {
            "transaction_id": f"txn-{position}",
            "transaction_name": f"Merchant {position}",
            "amount": float(position * 10),
            "date": "2026-08-08",
        }
        for position in range(1, 11)
    ]
    transactions[3] = {
        "transaction_id": "txn-olive",
        "transaction_name": "Olive Garden",
        "amount": 121.41,
        "date": "2026-08-08",
    }
    banking_adapter = SimpleNamespace(
        get_recent_transactions=AsyncMock(return_value={"transactions": transactions}),
        get_transaction=AsyncMock(return_value=transactions[3]),
    )
    fraud_adapter = SimpleNamespace(
        assess_transaction_risk=AsyncMock(
            return_value={
                "assessment_id": "assessment-olive",
                "risk_score": 0.96,
                "severity": "HIGH",
            }
        ),
        create_fraud_alert=AsyncMock(return_value={"alert_id": "alert-olive"}),
    )
    supervisor_decisions = [
        SupervisorDecision(
            next_agent="synthesis",
            goal="Greet the customer",
            reason="No external evidence is required",
        ),
        SupervisorDecision(
            next_agent="banking",
            goal="Retrieve the ten most recent transactions",
            reason="Banking evidence is required",
        ),
        SupervisorDecision(
            next_agent="synthesis",
            goal="Present the numbered transaction list",
            reason="The recent transactions are available",
        ),
        SupervisorDecision(
            next_agent="banking",
            goal="Validate the fourth displayed transaction",
            primary_user_goal="Assess and report the selected transaction as fraud",
            reason="The customer selected position four",
            reference_type="ordinal",
            candidate_position=4,
        ),
        SupervisorDecision(
            next_agent="fraud",
            goal="Assess the verified active transaction and create an alert if warranted",
            primary_user_goal="Assess and report the selected transaction as fraud",
            reason="Banking validated the transaction",
            reference_type="active_transaction",
        ),
        SupervisorDecision(
            next_agent="synthesis",
            goal="Report the grounded fraud result",
            reason="The fraud assessment and alert are available",
            reference_type="active_transaction",
        ),
        SupervisorDecision(
            next_agent="synthesis",
            goal="Acknowledge that the transaction is already reported",
            reason="The active alert already completes the requested workflow",
            reference_type="active_transaction",
        ),
        SupervisorDecision(
            next_agent="synthesis",
            goal="Give the status of the active fraud alert",
            reason="The active alert and prior evidence answer the status question",
            reference_type="active_transaction",
        ),
    ]
    supervisor_llm = SimpleNamespace(
        ainvoke=AsyncMock(side_effect=supervisor_decisions)
    )
    banking_tool_llm = SimpleNamespace(
        ainvoke=AsyncMock(
            side_effect=[
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "get_recent_transactions",
                            "args": {"limit": 10},
                            "id": "recent-10",
                        }
                    ],
                ),
                AIMessage(content="Recent transactions retrieved."),
            ]
        )
    )
    fraud_tool_llm = SimpleNamespace(
        ainvoke=AsyncMock(
            side_effect=[
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "assess_transaction_risk",
                            "args": {"transaction_id": "txn-olive"},
                            "id": "assess-olive",
                        }
                    ],
                ),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "create_fraud_alert",
                            "args": {"assessment_id": "assessment-olive"},
                            "id": "alert-olive",
                        }
                    ],
                ),
                AIMessage(content="Fraud workflow complete."),
            ]
        )
    )
    synthesis_llm = SimpleNamespace(
        ainvoke=AsyncMock(
            side_effect=[
                SynthesisOutput(
                    final_response="Hi! How can I help with your banking today?",
                    workflow_status="RESOLVED",
                ),
                SynthesisOutput(
                    final_response=(
                        "Here are your latest transactions:\n"
                        "1. Merchant 1 — $10.00\n2. Merchant 2 — $20.00\n"
                        "3. Merchant 3 — $30.00\n4. Olive Garden — $121.41"
                    ),
                    workflow_status="RESOLVED",
                ),
                SynthesisOutput(
                    final_response=(
                        "The Olive Garden transaction for $121.41 was assessed as high risk, "
                        "and a fraud alert was created."
                    ),
                    workflow_status="RESOLVED",
                ),
                SynthesisOutput(
                    final_response="It has already been reported under the active fraud alert.",
                    workflow_status="RESOLVED",
                ),
                SynthesisOutput(
                    final_response="The fraud alert is active for the Olive Garden transaction.",
                    workflow_status="RESOLVED",
                ),
            ]
        )
    )
    banking_agent = configured_agent(
        llm=banking_tool_llm,
        output_llm=SimpleNamespace(
            ainvoke=AsyncMock(
                return_value=BankingAgentOutput(
                    goal_completed=True,
                    evidence=[],
                    findings="Ten recent transactions retrieved.",
                )
            )
        ),
        prompt="banking",
        toolset=BankingToolset(banking_adapter, "customer-a"),
        version="test",
    )
    fraud_agent = configured_agent(
        llm=fraud_tool_llm,
        output_llm=SimpleNamespace(
            ainvoke=AsyncMock(
                return_value=FraudAgentOutput(
                    goal_completed=True,
                    findings="High-risk assessment and alert created.",
                )
            )
        ),
        prompt="fraud",
        toolset=FraudToolset(fraud_adapter, "customer-a"),
        version="test",
    )
    graph = build_graph(InMemorySaver())
    conversation_id = str(uuid4())
    config = {
        "configurable": {
            "thread_id": conversation_id,
            "max_iterations": 15,
            "supervisor_agent": configured_agent(
                llm=supervisor_llm, prompt="supervisor", version="test"
            ),
            "banking_agent": banking_agent,
            "fraud_agent": fraud_agent,
            "synthesis_agent": configured_agent(
                llm=synthesis_llm, prompt="synthesis", version="test"
            ),
        },
        "recursion_limit": 60,
    }
    user_turns = [
        "hi",
        "what are my last transactions",
        "this number 4 I have not done looks like fraud",
        "yes please report it",
        "what's the status of that?",
    ]
    result: dict = {}
    for position, content in enumerate(user_turns, start=1):
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=content, id=f"user-{position}")],
                "conversation_id": conversation_id,
                "run_id": f"run-{position}",
                "thread_id": conversation_id,
                "customer_id": "customer-a",
                "requested_transaction_id": None,
                "current_goal": "",
                "primary_user_goal": "",
                "iteration_count": 0,
                "warnings": [],
                "errors": [],
                "final_response": None,
            },
            config=config,
        )

    banking_adapter.get_recent_transactions.assert_awaited_once_with(
        "customer-a", limit=10, account_id=None
    )
    banking_adapter.get_transaction.assert_awaited_once_with("customer-a", "txn-olive")
    fraud_adapter.assess_transaction_risk.assert_awaited_once_with(
        customer_id="customer-a",
        transaction_id="txn-olive",
        device_id=None,
        channel=None,
    )
    fraud_adapter.create_fraud_alert.assert_awaited_once_with(
        assessment_id="assessment-olive", customer_id="customer-a"
    )
    assert result["active_transaction_id"] == "txn-olive"
    assert result["active_alert_id"] == "alert-olive"
    assert result["recent_transaction_candidates"][3]["transaction_id"] == "txn-olive"
    assert result["final_response"].startswith("The fraud alert is active")
    assert len(result["messages"]) == 10
