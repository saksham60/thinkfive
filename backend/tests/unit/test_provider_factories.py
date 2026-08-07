from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import SecretStr

from app.infrastructure.embeddings.factory import EmbeddingFactory
from app.llm.factory import LLMFactory
from app.llm.providers.openai import GeminiChatOpenAI


def settings(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "llm_provider": "gemini",
        "gemini_api_key": SecretStr("gemini-key"),
        "gemini_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini_model": "gemini-flash-latest",
        "litellm_api_key": SecretStr("litellm-key"),
        "litellm_base_url": "https://litellm.example/v1",
        "litellm_team_id": "team-123",
        "litellm_model": "gateway-model",
        "embedding_provider": "gemini",
        "gemini_embedding_model": "gemini-embedding-2",
        "litellm_embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_gemini_chat_provider_uses_google_configuration() -> None:
    provider = LLMFactory(settings()).create()

    assert provider.provider_name == "gemini"
    assert provider.model_name == "gemini-flash-latest"
    assert provider.config.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert provider.api_key == "gemini-key"
    assert provider.config.default_headers == {}


def test_litellm_chat_provider_is_switchable_and_sends_team_header() -> None:
    provider = LLMFactory(settings(llm_provider="litellm")).create()

    assert provider.provider_name == "litellm"
    assert provider.model_name == "gateway-model"
    assert provider.config.base_url == "https://litellm.example/v1"
    assert provider.api_key == "litellm-key"
    assert provider.config.default_headers == {"x-litellm-team-id": "team-123"}


def test_legacy_openai_provider_name_routes_to_litellm() -> None:
    provider = LLMFactory(settings(llm_provider="openai")).create()

    assert provider.provider_name == "litellm"
    assert provider.config.base_url == "https://litellm.example/v1"


def test_selected_chat_provider_requires_its_own_key() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        LLMFactory(settings(gemini_api_key=None)).create()


async def test_gemini_embedding_provider_preserves_pgvector_dimensions() -> None:
    response = SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])
    embeddings = SimpleNamespace(create=AsyncMock(return_value=response))
    client = Mock(embeddings=embeddings)

    with patch("app.infrastructure.embeddings.factory.AsyncOpenAI", return_value=client) as client_type:
        provider = EmbeddingFactory(settings()).create()
        result = await provider.embed("banking policy")

    client_type.assert_called_once_with(
        api_key="gemini-key",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    embeddings.create.assert_awaited_once_with(
        model="gemini-embedding-2",
        input="banking policy",
        dimensions=1536,
    )
    assert result == [0.1, 0.2]


def test_litellm_embedding_provider_remains_selectable() -> None:
    with patch("app.infrastructure.embeddings.factory.AsyncOpenAI") as client_type:
        EmbeddingFactory(settings(embedding_provider="litellm")).create()

    client_type.assert_called_once_with(
        api_key="litellm-key",
        base_url="https://litellm.example/v1",
    )


def test_gemini_chat_adapter_round_trips_tool_thought_signature() -> None:
    llm = GeminiChatOpenAI(model="gemini-flash-latest", api_key="test-key")
    signature = {"google": {"thought_signature": "signed-thought"}}
    result = llm._create_chat_result(
        {
            "id": "completion-1",
            "model": "gemini-flash-latest",
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {"name": "get_accounts", "arguments": "{}"},
                                "extra_content": signature,
                            }
                        ],
                    },
                }
            ],
        }
    )
    assistant = result.generations[0].message

    payload = llm._get_request_payload(
        [
            HumanMessage(content="What is my balance?"),
            assistant,
            ToolMessage(content='{"accounts": []}', tool_call_id="call-1"),
        ]
    )

    assert assistant.additional_kwargs["gemini_tool_call_extra_content"] == {"call-1": signature}
    assert payload["messages"][1]["tool_calls"][0]["extra_content"] == signature
