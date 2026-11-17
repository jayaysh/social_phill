"""OpenAI 구현. agent.llm.LLM 인터페이스(parse / research)를 Responses API 로 제공한다.

- 구조화 출력: `client.responses.parse(text_format=<Pydantic>)` (strict JSON schema)
- 웹 리서치: Responses API 의 `web_search` 도구. 출처는 url_citation 주석에서 뽑는다.
- reasoning 모델(gpt-5·o 시리즈)에만 `reasoning.effort` 를 보낸다. gpt-4.1·gpt-4o 에 보내면 400 이다.
"""
from __future__ import annotations

from typing import Callable, TypeVar

import openai
from pydantic import BaseModel, ValidationError

from .llm import MAX_TOKENS, LLMError, WebSource

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")

# SDK 의 모델 타입 정의에 있는 이름들. 계정에서 실제로 쓸 수 있는지는 키에 따라 다르므로 '직접 입력'도 허용한다.
OPENAI_DEFAULT_MODEL = "gpt-5.5"
OPENAI_MODEL_CHOICES = {
    "gpt-6.1-sol": "GPT-6.1 sol",
    "gpt-5.5": "GPT-5.5 (기본)",
    "gpt-5.4": "GPT-5.4",
    "gpt-5.4-mini": "GPT-5.4 mini · 빠르고 저렴",
    "gpt-5": "GPT-5",
    "gpt-5-mini": "GPT-5 mini",
    "gpt-4.1": "GPT-4.1 (reasoning 없음)",
}
_REASONING_PREFIXES = ("gpt-6", "gpt-5", "o1", "o3", "o4")
_FATAL = (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError)


def _is_reasoning(model: str) -> bool:
    return model.startswith(_REASONING_PREFIXES)


def _max_output(model: str, wanted: int) -> int:
    """gpt-4o 계열은 출력 상한이 16,384 라 그보다 크면 400 이 난다."""
    return min(wanted, 16000) if model.startswith("gpt-4o") else wanted


def _detail(e: openai.APIStatusError) -> str:
    """e.message 는 'Error code: 400 - ...' 형태라, 본문의 message 만 꺼낸다."""
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        inner = body.get("message") or (body.get("error") or {}).get("message")
        if inner:
            return str(inner)
    return e.message


def friendly_error(e: Exception) -> str:
    if isinstance(e, openai.AuthenticationError):
        return "OpenAI API 키가 올바르지 않습니다. 사이드바에서 키를 확인해 주세요."
    if isinstance(e, openai.PermissionDeniedError):
        return "이 OpenAI 키에는 해당 모델 또는 기능을 쓸 권한이 없습니다(지역·조직 설정을 확인하세요)."
    if isinstance(e, openai.NotFoundError):
        return "요청한 모델을 찾을 수 없습니다. 이 계정에서 쓸 수 있는 다른 모델을 고르거나 직접 입력해 보세요."
    if isinstance(e, openai.RateLimitError):
        if getattr(e, "code", None) == "insufficient_quota":
            return "OpenAI 계정의 크레딧(할당량)이 부족합니다. 결제·한도 설정을 확인해 주세요."
        return "요청이 몰렸습니다. 잠시 뒤에 다시 시도해 주세요."
    if isinstance(e, openai.APITimeoutError):
        return "OpenAI 응답이 너무 오래 걸려 중단했습니다. '분석 깊이'를 낮추거나 다시 시도해 주세요."
    if isinstance(e, openai.BadRequestError):
        return f"요청 형식이 거절되었습니다: {_detail(e)}"
    if isinstance(e, openai.APIStatusError):
        if e.status_code >= 500:
            return "OpenAI 서버가 일시적으로 불안정합니다. 잠시 뒤 다시 시도해 주세요."
        return f"API 오류({e.status_code}): {_detail(e)}"
    if isinstance(e, openai.APIConnectionError):
        return "네트워크에 연결할 수 없습니다. 인터넷 연결을 확인해 주세요."
    return f"알 수 없는 오류: {e}"


def _wrap(e: openai.APIError) -> LLMError:
    fatal = isinstance(e, _FATAL) or getattr(e, "code", None) == "insufficient_quota"
    return LLMError(friendly_error(e), fatal=fatal)


class OpenAIModel:
    def __init__(self, api_key: str | None, model: str = OPENAI_DEFAULT_MODEL, effort: str = "medium"):
        self.model = model.strip() or OPENAI_DEFAULT_MODEL
        self.effort = effort
        self._api_key = api_key
        self._client: openai.OpenAI | None = None
        self._send_reasoning = _is_reasoning(self.model)

    @property
    def client(self) -> openai.OpenAI:
        """키가 없으면 OpenAI SDK 는 생성자에서 바로 예외를 던진다. 화면 흐름(run_step) 안에서 안내하도록 지연 생성한다."""
        if self._client is None:
            try:
                self._client = openai.OpenAI(api_key=self._api_key or None, max_retries=3, timeout=300.0)
            except openai.OpenAIError as e:
                raise LLMError("OpenAI API 키가 설정되지 않았습니다. 사이드바에 키를 입력하거나 데모 모드를 켜 주세요.", fatal=True) from e
        return self._client

    def _reasoning(self, effort: str) -> dict:
        return {"reasoning": {"effort": effort}} if self._send_reasoning else {}

    def _guarded(self, call: Callable[[], R]) -> R:
        """모델이 reasoning 파라미터를 받지 않아 400 을 내면, 그 파라미터만 빼고 한 번 다시 보낸다.

        새 모델 계열(gpt-6 등)이 reasoning.effort 를 받는지는 이름만으로 알 수 없어서 둔 안전장치다.
        """
        try:
            return call()
        except openai.BadRequestError as e:
            if self._send_reasoning and "reasoning" in str(e).lower():
                self._send_reasoning = False
                return call()
            raise

    # ── 구조화 출력 ──────────────────────────────────────────────
    def parse(self, schema: type[T], system: str, user: str, max_tokens: int = MAX_TOKENS) -> T:
        """응답이 max_output_tokens 에서 잘리면(추론 토큰 포함) effort 를 'low' 로 낮춰 한 번만 다시 시도한다."""
        efforts = [self.effort] if self.effort == "low" else [self.effort, "low"]
        for effort in efforts:
            try:
                resp = self._guarded(
                    lambda: self.client.responses.parse(
                        model=self.model,
                        instructions=system,
                        input=user,
                        text_format=schema,
                        max_output_tokens=_max_output(self.model, max_tokens),
                        **self._reasoning(effort),
                    )
                )
            except openai.APIError as e:
                raise _wrap(e) from e
            except (ValidationError, openai.LengthFinishReasonError):
                continue  # 잘린 응답 또는 깨진 JSON → 더 낮은 effort 로 재시도

            for item in resp.output:
                if item.type == "message" and any(c.type == "refusal" for c in item.content):
                    raise LLMError("모델이 이 요청에 답하지 않았습니다. 입력 표현을 바꿔 다시 시도해 주세요.")
            if resp.status == "incomplete" or resp.output_parsed is None:
                continue
            return resp.output_parsed

        raise LLMError(
            "모델 응답이 중간에 끊겼거나 형식이 올바르지 않았습니다. "
            "사이드바에서 '분석 깊이'를 낮추거나 입력을 줄여 다시 시도해 주세요."
        )

    # ── 웹 리서치 ───────────────────────────────────────────────
    def research(self, prompt: str, max_uses: int = 4) -> tuple[str, list[WebSource]]:
        try:
            resp = self._guarded(
                lambda: self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    tools=[{"type": "web_search"}],
                    max_tool_calls=max_uses,
                    max_output_tokens=_max_output(self.model, 8000),
                    **self._reasoning("low"),  # 조사 요약에는 깊은 추론이 필요 없다
                )
            )
        except openai.APIError as e:
            raise _wrap(e) from e

        sources: dict[str, WebSource] = {}
        for item in resp.output:
            if item.type != "message":
                continue
            for content in item.content:
                for ann in getattr(content, "annotations", None) or []:
                    if ann.type == "url_citation" and ann.url and ann.url not in sources:
                        sources[ann.url] = WebSource(ann.title or ann.url, ann.url)
        return (resp.output_text or "").strip(), list(sources.values())[:10]
