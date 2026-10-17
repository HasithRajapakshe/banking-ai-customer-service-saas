"""Real providers via LangChain chat models (ollama, gemini, openai, anthropic).

Every provider is driven through the same LangChain API (`bind_tools` +
`ainvoke`), which normalises tool calls across vendors. Integration packages
are imported lazily so only the configured provider needs to be importable.
"""

from typing import Any

from app.llm.base import ChatMessage, LLMError, LLMResponse, ToolCall, ToolSpec


def _build_chat_model(provider: str, model: str, settings: Any):
    temperature = settings.llm_temperature
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
            num_ctx=settings.ollama_num_ctx,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.google_api_key:
            raise LLMError("MODEL_PROVIDER=gemini requires GOOGLE_API_KEY")
        return ChatGoogleGenerativeAI(
            model=model, google_api_key=settings.google_api_key, temperature=temperature
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise LLMError("MODEL_PROVIDER=openai requires OPENAI_API_KEY")
        return ChatOpenAI(model=model, api_key=settings.openai_api_key, temperature=temperature)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.anthropic_api_key:
            raise LLMError("MODEL_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
        return ChatAnthropic(model=model, api_key=settings.anthropic_api_key, temperature=temperature)
    raise LLMError(f"Unknown model provider: {provider!r}")


def _to_langchain(messages: list[ChatMessage]):
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    kinds = {"system": SystemMessage, "user": HumanMessage, "assistant": AIMessage}
    return [kinds[m.role](content=m.content) for m in messages]


def _tool_definition(tool: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


class LangChainProvider:
    def __init__(self, provider: str, model: str, settings: Any):
        self.name = provider
        self.model_name = model
        self._model = _build_chat_model(provider, model, settings)

    async def achat(self, messages: list[ChatMessage], tools: list[ToolSpec] | None = None) -> LLMResponse:
        model = self._model.bind_tools([_tool_definition(t) for t in tools]) if tools else self._model
        try:
            result = await model.ainvoke(_to_langchain(messages))
        except Exception as exc:  # provider SDKs raise many different types
            raise LLMError(f"{self.name} call failed: {type(exc).__name__}: {exc}") from exc

        content = result.content if isinstance(result.content, str) else _flatten(result.content)
        calls = tuple(
            ToolCall(name=call["name"], arguments=dict(call.get("args") or {}))
            for call in (getattr(result, "tool_calls", None) or [])
        )
        return LLMResponse(content=content, tool_calls=calls)


def _flatten(content: Any) -> str:
    """Some providers return a list of content blocks instead of a string."""
    parts = []
    for block in content or []:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)
