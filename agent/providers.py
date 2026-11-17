"""AI 제공자 선택. 앱은 이 모듈의 make_llm 만 알면 된다."""
from __future__ import annotations

from .llm import DEFAULT_MODEL, LLM, MODEL_CHOICES, Claude

PROVIDERS = {"anthropic": "Anthropic (Claude)", "openai": "OpenAI"}
KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}


def make_llm(provider: str, api_key: str | None, model: str, effort: str) -> LLM:
    if provider == "openai":
        from .openai_llm import OpenAIModel  # openai 패키지는 이 제공자를 고를 때만 불러온다

        return OpenAIModel(api_key, model, effort)
    return Claude(api_key, model or DEFAULT_MODEL, effort)


def model_choices(provider: str) -> dict[str, str]:
    if provider == "openai":
        from .openai_llm import OPENAI_MODEL_CHOICES

        return OPENAI_MODEL_CHOICES
    return MODEL_CHOICES


def default_model(provider: str) -> str:
    if provider == "openai":
        from .openai_llm import OPENAI_DEFAULT_MODEL

        return OPENAI_DEFAULT_MODEL
    return DEFAULT_MODEL
