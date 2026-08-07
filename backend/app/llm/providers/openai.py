"""OpenAI-compatible LLM provider for LiteLLM and Google Gemini."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.llm.models import LLMConfig


class GeminiChatOpenAI(ChatOpenAI):
    """ChatOpenAI adapter that round-trips Gemini thought signatures.

    Gemini 3 tool calls include a provider-specific ``extra_content`` field.
    LangChain's generic OpenAI converter currently drops that field, causing
    the next tool-result request to fail. Preserve it without leaking Gemini
    details into the graph or agent tool loop.
    """

    def _create_chat_result(
        self,
        response: dict[str, Any] | Any,
        generation_info: dict[str, Any] | None = None,
    ) -> Any:
        response_dict = response if isinstance(response, dict) else response.model_dump(warnings=False)
        result = super()._create_chat_result(response, generation_info)

        for generation, choice in zip(result.generations, response_dict.get("choices") or [], strict=False):
            message_dict = choice.get("message") or {}
            message = generation.message
            if not isinstance(message, AIMessage):
                continue
            if extra_content := message_dict.get("extra_content"):
                message.additional_kwargs["gemini_extra_content"] = extra_content
            tool_extras = {
                call.get("id"): call["extra_content"]
                for call in message_dict.get("tool_calls") or []
                if call.get("id") and call.get("extra_content")
            }
            if tool_extras:
                message.additional_kwargs["gemini_tool_call_extra_content"] = tool_extras
        return result

    def _get_request_payload(
        self,
        input_: Any,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        messages = self._convert_input(input_).to_messages()
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        outgoing_messages = payload.get("messages")
        if not isinstance(outgoing_messages, list):
            return payload

        for source, outgoing in zip(messages, outgoing_messages, strict=False):
            if not isinstance(source, AIMessage) or not isinstance(outgoing, dict):
                continue
            if extra_content := source.additional_kwargs.get("gemini_extra_content"):
                outgoing["extra_content"] = extra_content
            tool_extras = source.additional_kwargs.get("gemini_tool_call_extra_content") or {}
            for tool_call in outgoing.get("tool_calls") or []:
                if extra_content := tool_extras.get(tool_call.get("id")):
                    tool_call["extra_content"] = extra_content
        return payload


class OpenAICompatibleProvider:
    """LLM provider using an OpenAI-compatible endpoint."""

    def __init__(self, config: LLMConfig, api_key: str) -> None:
        self.config = config
        self.api_key = api_key

    def get_llm(self, temperature: float = 0.0, **kwargs: Any) -> ChatOpenAI:
        client_type = GeminiChatOpenAI if self.config.provider == "gemini" else ChatOpenAI
        return client_type(
            model=self.config.model,
            base_url=self.config.base_url,
            api_key=self.api_key,  # type: ignore[arg-type]
            temperature=temperature,
            default_headers=self.config.default_headers or None,
            **kwargs,  # type: ignore[arg-type]
        )

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def provider_name(self) -> str:
        return self.config.provider
