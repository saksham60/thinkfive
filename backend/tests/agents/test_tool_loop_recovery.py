from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.tool_loop import find_grounded_value, run_grounded_tool_loop


async def test_optional_tool_failure_preserves_prior_grounded_evidence() -> None:
    tool_llm = SimpleNamespace(
        ainvoke=AsyncMock(
            side_effect=[
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "assess_transaction_risk",
                            "args": {"transaction_id": "txn-125"},
                            "id": "assessment-call",
                        }
                    ],
                ),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "create_fraud_alert",
                            "args": {"assessment_id": "assessment-medium"},
                            "id": "alert-call",
                        }
                    ],
                ),
            ]
        )
    )
    output = SimpleNamespace(goal_completed=True, requires_case=True)
    output_llm = SimpleNamespace(ainvoke=AsyncMock(return_value=output))
    toolset = SimpleNamespace(
        execute_tool=AsyncMock(
            side_effect=[
                {
                    "assessment_id": "assessment-medium",
                    "transaction_id": "txn-125",
                    "risk_score": 0.5,
                    "severity": "MEDIUM",
                },
                RuntimeError("Alert threshold not met"),
            ]
        )
    )

    result = await run_grounded_tool_loop(
        tool_llm,
        output_llm,
        toolset,
        [HumanMessage(content="Assess and report the confirmed transaction")],
        agent_name="fraud",
    )

    assert result.output is output
    assert find_grounded_value(result.tool_results, "assessment_id") == "assessment-medium"
    assert find_grounded_value(result.tool_results, "severity") == "MEDIUM"
    assert result.tool_results[-1]["tool"] == "create_fraud_alert"
    assert result.tool_results[-1]["error"]["error_code"] == "RuntimeError"
    assert output_llm.ainvoke.await_count == 1
