"""Claude API 호출 래퍼.

- 구조화 출력: `client.beta.messages.parse(output_format=<Pydantic>)`
- 웹 리서치: 서버 도구 `web_search_20260209` (Anthropic 서버에서 실행됨)
- 모델이 안전 분류기로 거절할 때를 대비해 지원 모델에는 서버 측 fallbacks 를 켠다.
  서버가 이 베타를 받아주지 않으면(400) 한 번만 fallbacks 없이 다시 보낸다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")

DEFAULT_MODEL = "claude-opus-5-5"
MODEL_CHOICES = {
    "claude-opus-5-5": "Opus 5.5 · 가장 깊은 분석 (기본)",
    "claude-sonnet-5-5": "Sonnet 5.5 · 빠르고 저렴",
    "claude-haiku-5-5": "Haiku 5.5 · 가장 빠름 (품질 낮음)",
}
# 서버 측 fallbacks 를 지원하는 모델
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

# 비스트리밍 요청에서 SDK 가 허용하는 max_tokens 상한(약 21,333) 아래. 사고 토큰도 여기에 포함된다.
MAX_TOKENS = 20000


class LLMError(Exception):
    """화면에 그대로 보여줘도 되는 한국어 오류 메시지를 담는다.

    fatal=True 이면 같은 자격 증명으로 다시 호출해도 소용없는 오류(키·권한·모델 없음)다.
    """

    def __init__(self, message: str, fatal: bool = False):
        super().__init__(message)
        self.fatal = fatal


_FATAL = (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError)


def _wrap(e: anthropic.APIError) -> LLMError:
    return LLMError(friendly_error(e), fatal=isinstance(e, _FATAL))


@dataclass
class WebSource:
    title: str
    url: str


class LLM(Protocol):
    """파이프라인이 기대하는 모델 인터페이스. Claude 와 OpenAI 구현이 모두 이를 만족한다."""

    def parse(self, schema: type[T], system: str, user: str, max_tokens: int = MAX_TOKENS) -> T: ...

    def research(self, prompt: str, max_uses: int = 4) -> tuple[str, list[WebSource]]: ...


class Claude:
    def __init__(self, api_key: str | None, model: str = DEFAULT_MODEL, effort: str = "medium"):
        self.model = model
        self.effort = effort
        self._fallbacks = model in _FALLBACK_MODELS
        # api_key 가 None 이면 SDK 가 환경 변수/`ant auth login` 프로필에서 자격 증명을 찾는다.
        self.client = anthropic.Anthropic(api_key=api_key or None, max_retries=3, timeout=300.0)

    # ── 공통 요청 옵션 ───────────────────────────────────────────
    def _common(self, effort: str | None = None) -> dict:
        kwargs: dict = {"model": self.model, "output_config": {"effort": effort or self.effort}}
        if self._fallbacks:
            kwargs["betas"] = [_FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        return kwargs

    def _guarded(self, call: Callable[[], R]) -> R:
        """서버가 fallbacks 베타를 거절(400)하면 그 기능을 끄고 한 번만 다시 보낸다."""
        try:
            return call()
        except anthropic.BadRequestError as e:
            text = str(e).lower()
            if self._fallbacks and ("fallback" in text or "beta" in text):
                self._fallbacks = False
                return call()
            raise

    # ── 구조화 출력 ──────────────────────────────────────────────
    def parse(self, schema: type[T], system: str, user: str, max_tokens: int = MAX_TOKENS) -> T:
        """구조화된 응답을 받는다.

        응답이 max_tokens 에서 잘리면 SDK 가 parse 도중 pydantic ValidationError 를 던진다
        (사고 토큰이 max_tokens 를 먼저 소모하는 높은 effort 에서 흔하다). 이때는 effort 를
        'low' 로 낮춰 한 번만 다시 시도하고, 그래도 안 되면 안내 메시지를 낸다.
        """
        efforts = [self.effort] if self.effort == "low" else [self.effort, "low"]
        for effort in efforts:
            try:
                resp = self._guarded(
                    lambda: self.client.beta.messages.parse(
                        max_tokens=max_tokens,
                        system=system,
                        messages=[{"role": "user", "content": user}],
                        output_format=schema,
                        **self._common(effort),
                    )
                )
            except anthropic.APIError as e:
                raise _wrap(e) from e
            except ValidationError:
                continue  # 잘린 응답 또는 깨진 JSON → 더 낮은 effort 로 재시도

            if resp.stop_reason == "refusal":
                raise LLMError("모델이 이 요청에 답하지 않았습니다. 입력 표현을 바꿔 다시 시도해 주세요.")
            if resp.parsed_output is None or resp.stop_reason == "max_tokens":
                continue
            return resp.parsed_output

        raise LLMError(
            "모델 응답이 중간에 끊겼거나 형식이 올바르지 않았습니다. "
            "사이드바에서 '분석 깊이'를 낮추거나 입력을 줄여 다시 시도해 주세요."
        )

    # ── 웹 리서치 (서버 도구) ────────────────────────────────────
    def research(self, prompt: str, max_uses: int = 4) -> tuple[str, list[WebSource]]:
        """웹 검색으로 최신 보도·YouTube 해설·블로그 담론을 조사해 요약문과 출처를 돌려준다."""
        messages: list[dict] = [{"role": "user", "content": prompt}]
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": max_uses}]
        texts: list[str] = []
        sources: dict[str, WebSource] = {}

        try:
            for _ in range(5):  # pause_turn 이어받기 상한
                resp = self._guarded(
                    lambda: self.client.beta.messages.create(
                        max_tokens=8000, messages=messages, tools=tools, **self._common()
                    )
                )
                for block in resp.content:
                    if block.type == "text":
                        texts.append(block.text)
                    elif block.type == "web_search_tool_result" and isinstance(block.content, list):
                        # 오류일 때 content 는 리스트가 아니라 오류 객체다 (위 isinstance 로 걸러짐)
                        for item in block.content:
                            url = getattr(item, "url", None)
                            if url and url not in sources:
                                sources[url] = WebSource(getattr(item, "title", "") or url, url)
                if resp.stop_reason == "pause_turn":
                    messages.append({"role": "assistant", "content": resp.content})
                    texts.clear()  # 이어받은 최종 턴의 텍스트만 사용
                    continue
                break
        except anthropic.APIError as e:
            raise _wrap(e) from e

        return "".join(texts).strip(), list(sources.values())[:10]


def _detail(e: anthropic.APIStatusError) -> str:
    """e.message 는 'Error code: 400 - {...}' 형태의 원시 JSON 이라, 본문의 error.message 만 꺼낸다."""
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        inner = body.get("error")
        if isinstance(inner, dict) and inner.get("message"):
            return str(inner["message"])
    return e.message


def friendly_error(e: Exception) -> str:
    if isinstance(e, anthropic.AuthenticationError):
        return "API 키가 올바르지 않습니다. 사이드바에서 키를 확인해 주세요."
    if isinstance(e, anthropic.PermissionDeniedError):
        return "이 API 키에는 해당 모델 또는 기능을 쓸 권한이 없습니다."
    if isinstance(e, anthropic.NotFoundError):
        return "요청한 모델을 찾을 수 없습니다. 사이드바에서 다른 모델을 선택해 보세요."
    if isinstance(e, anthropic.RateLimitError):
        retry = e.response.headers.get("retry-after", "60")
        return f"요청이 몰렸습니다. 약 {retry}초 뒤에 다시 시도해 주세요."
    if isinstance(e, anthropic.BadRequestError):
        return f"요청 형식이 거절되었습니다: {_detail(e)}"
    if isinstance(e, anthropic.APIStatusError):
        if e.status_code >= 500:
            return "Anthropic 서버가 일시적으로 불안정합니다. 잠시 뒤 다시 시도해 주세요."
        return f"API 오류({e.status_code}): {_detail(e)}"
    if isinstance(e, anthropic.APIConnectionError):
        return "네트워크에 연결할 수 없습니다. 인터넷 연결을 확인해 주세요."
    return f"알 수 없는 오류: {e}"
