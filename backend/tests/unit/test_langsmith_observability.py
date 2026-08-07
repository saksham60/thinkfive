from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.observability.langsmith import llm_trace_config, trace_messages, trace_value


def test_trace_value_redacts_credentials_without_hiding_business_ids() -> None:
    value = trace_value(
        {
            "customer_id": "demo_customer_001",
            "api_key": "sk-super-secret",
            "arguments": {"authorization": "Bearer secret-token", "transaction_id": "txn_123"},
            "prompt": "Use token=mcp_abcdefghijklmnop for this request",
        }
    )

    assert value["customer_id"] == "demo_customer_001"
    assert value["api_key"] == "[REDACTED]"
    assert value["arguments"]["authorization"] == "[REDACTED]"
    assert value["arguments"]["transaction_id"] == "txn_123"
    assert "mcp_abcdefghijklmnop" not in value["prompt"]


def test_trace_messages_include_the_exact_prompt_and_roles() -> None:
    messages = trace_messages(
        [SystemMessage(content="System prompt version 2"), HumanMessage(content="Show my balance")]
    )

    assert messages == [
        {"role": "system", "content": "System prompt version 2", "name": None},
        {"role": "human", "content": "Show my balance", "name": None},
    ]


def test_llm_trace_config_names_agent_phase_and_prompt_version() -> None:
    config = llm_trace_config("fraud", "tool_selection", "fraud-v3")

    assert config["run_name"] == "agent.fraud.tool_selection"
    assert config["metadata"] == {
        "agent": "fraud",
        "phase": "tool_selection",
        "prompt_version": "fraud-v3",
    }
