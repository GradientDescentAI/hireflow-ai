"""
LLM client abstraction.

Wraps OpenAI, Anthropic, and Gemini (via OpenAI-compatible endpoint) behind
a single interface. All callers go through llm.router to get the right
(provider, model, params) for their pipeline stage.
"""

import os
from dataclasses import dataclass
from typing import Any

import anthropic
import openai


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    raw: Any = None


class OpenAIClient:
    def __init__(self) -> None:
        self._client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        response_format: dict | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            raw=resp,
        )


class AnthropicClient:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system

        resp = self._client.messages.create(**kwargs)
        return LLMResponse(
            content=resp.content[0].text if resp.content else "",
            model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            raw=resp,
        )


class GeminiClient:
    """
    Gemini via Google's OpenAI-compatible endpoint.
    Uses the openai SDK — no extra package needed.
    """
    _GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(self) -> None:
        self._client = openai.OpenAI(
            api_key=os.environ["GOOGLE_API_KEY"],
            base_url=self._GEMINI_BASE,
        )

    def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        response_format: dict | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # Disable Gemini 2.5 internal "thinking" so max_tokens covers visible output only
            "extra_body": {"reasoning_effort": "none"},
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            raw=resp,
        )


_openai_client: OpenAIClient | None = None
_anthropic_client: AnthropicClient | None = None
_gemini_client: GeminiClient | None = None


def get_openai() -> OpenAIClient:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client


def get_anthropic() -> AnthropicClient:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AnthropicClient()
    return _anthropic_client


def get_gemini() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def call_llm(
    stage: str,
    messages: list[dict],
    *,
    plan: str = "free",
    system: str | None = None,
    response_format: dict | None = None,
) -> "LLMResponse":
    """
    One-stop shop: look up the route for *stage*, pick the right client,
    and call it.  All agents should use this instead of get_openai() / etc.
    """
    from packages.llm.router import get_route  # local import avoids circular dep
    route = get_route(stage, plan=plan)

    if route.provider == "gemini":
        return get_gemini().complete(
            messages=messages,
            model=route.model,
            temperature=route.temperature,
            response_format=response_format,
            max_tokens=route.max_tokens,
        )
    elif route.provider == "anthropic":
        return get_anthropic().complete(
            messages=messages,
            model=route.model,
            temperature=route.temperature,
            system=system,
            max_tokens=route.max_tokens,
        )
    else:  # openai (fallback)
        return get_openai().complete(
            messages=messages,
            model=route.model,
            temperature=route.temperature,
            response_format=response_format,
            max_tokens=route.max_tokens,
        )
