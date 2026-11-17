"""에이전트 각 단계의 입출력 스키마 (Pydantic).

Claude 의 structured output(`output_format`)에 그대로 사용되므로
필드 설명(description)이 곧 모델에게 주는 작성 지침이다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ───────────────────────── 1단계: 현안 구조화 ─────────────────────────
class Stakeholder(BaseModel):
    layer: str = Field(description="연루된 사회 계층·집단의 이름 (예: '청년층(20~30대)', '자영업자')")
    role: str = Field(description="이 현안에서 이 집단이 놓인 위치와 역할 한두 문장")
    interests: list[str] = Field(description="이 집단이 지키거나 얻으려는 이익·가치 2~3개")
    fears: list[str] = Field(description="이 집단이 잃을까 두려워하는 것 2~3개")


ConflictKind = Literal["이익 갈등", "가치 갈등", "정체성 갈등", "사실·정보 갈등", "구조적 갈등"]


class Conflict(BaseModel):
    parties: list[str] = Field(description="충돌하는 두 집단의 이름. stakeholders 의 layer 와 똑같은 표기를 사용")
    kind: ConflictKind = Field(description="충돌의 성격")
    description: str = Field(description="무엇을 두고 어떻게 부딪히는지 두 문장 이내")


class IssueStructure(BaseModel):
    title: str = Field(description="현안을 한 줄로 요약한 제목 (25자 안팎)")
    summary: str = Field(description="현안 개요 3~4문장. 중립적 어조")
    surface_phenomenon: str = Field(description="뉴스·여론에서 보이는 표면적 현상 2문장")
    root_cause: str = Field(description="표면 현상 아래에 있는 근본 원인 가설 2~3문장. 구조·제도·가치·신뢰 관점에서 진단")
    core_questions: list[str] = Field(description="핵심 쟁점을 질문 형태로 3~4개")
    stakeholders: list[Stakeholder] = Field(description="연루된 사회 계층 3~5개")
    conflicts: list[Conflict] = Field(description="주요 이해관계 충돌 양상 3~4개")
    public_perception: str = Field(description="대중이 이 현안을 바라보는 시각과 온라인 담론의 결. 제공된 웹 리서치 자료가 없으면 일반적 추정임을 밝힌다")
    scholar_keywords_en: list[str] = Field(description="학술 데이터베이스 검색용 영어 키워드 3개")
    scholar_keywords_ko: list[str] = Field(description="RISS·KCI 검색용 한국어 키워드 3개")


# ───────────────────────── 2단계: 관점 큐레이션 ─────────────────────────
class HistoricalCase(BaseModel):
    id: str = Field(description="'A', 'B', 'C' 중 하나")
    title: str = Field(description="사례 이름 (예: '솔론의 부채 탕감 개혁')")
    era_place: str = Field(description="시기와 장소 (예: '기원전 594년경, 아테네')")
    summary: str = Field(description="사례의 전개를 3~4문장으로. 실제 역사적 사실만")
    parallels: list[str] = Field(description="현안과 구조적으로 닮은 점 2~3개")
    differences: str = Field(description="현안과 다른 점, 비유의 한계 한 문장")
    outcome: str = Field(description="그 갈등이 어떻게 수습되었는지 혹은 실패했는지 한두 문장")
    philosopher: str = Field(description="이 사례를 분석한 철학자·이론가의 한국어 이름")
    philosopher_latin: str = Field(description="그 철학자의 로마자 이름 (예: 'Aristotle')")
    work: str = Field(description="핵심 이론이 담긴 대표 저작 (실제 존재하는 저작만)")
    theory: str = Field(description="핵심 이론·개념 이름 (예: '중용과 혼합정체')")
    lens: str = Field(description="이 이론으로 현안을 보면 무엇이 보이는지 3문장")
    key_question: str = Field(description="이 관점이 우리에게 던지는 핵심 질문 하나")
    queries_en: list[str] = Field(description="이 사례·이론의 학술 근거를 찾기 위한 영어 검색어 2개")
    queries_ko: list[str] = Field(description="같은 목적의 한국어 검색어 1~2개")


class CaseSet(BaseModel):
    cases: list[HistoricalCase] = Field(description="서로 다른 시대·사상 전통에서 고른 사례 3개")


# ───────────────────────── 3단계: 솔루션 ─────────────────────────
class LayerAction(BaseModel):
    layer: str = Field(description="1단계 stakeholders 의 layer 와 똑같은 표기")
    actions: list[str] = Field(description="그 계층이 자기 위치에서 실제로 할 수 있는 구체적 실천 3개. 누가·무엇을·어떻게가 드러나게")
    first_step: str = Field(description="내일 시작할 수 있는 가장 작은 첫걸음 한 문장")


Horizon = Literal["단기 (3개월 이내)", "중기 (1년 이내)", "장기 (1년 이후)"]


class Phase(BaseModel):
    horizon: Horizon
    goals: list[str] = Field(description="해당 시기의 목표와 실행 항목 2~3개")


class Limitation(BaseModel):
    point: str = Field(description="이 해법의 한계나 부작용 한 문장")
    mitigation: str = Field(description="그 한계를 줄일 방법 한 문장")


class Resource(BaseModel):
    kind: str = Field(description="자원 유형 (예: 제도, 예산, 인력, 신뢰, 데이터, 시간)")
    detail: str = Field(description="무엇이 얼마나 필요한지 한 문장")


class SolutionReport(BaseModel):
    headline: str = Field(description="해법의 핵심을 담은 한 문장 (40자 안팎)")
    logic: str = Field(description="선택한 철학적 관점이 이 현안에 어떻게 적용되는지 논리 전개 4~6문장")
    principles: list[str] = Field(description="해법을 관통하는 원칙 3개")
    layer_actions: list[LayerAction] = Field(description="1단계에서 식별한 계층 각각에 대한 실천안")
    roadmap: list[Phase] = Field(description="단기·중기·장기 순서의 로드맵 3단계")
    limitations: list[Limitation] = Field(description="한계점 2~3개")
    resources: list[Resource] = Field(description="필요 자원 3~4개")
    indicators: list[str] = Field(description="해법이 작동하는지 확인할 관찰 가능한 지표 2~3개")
    evidence_note: str = Field(description="제공된 참고 문헌 후보 중 실제로 근거로 삼은 것이 있다면 [번호]와 함께 한 문장. 없으면 빈 문자열")


# ───────────────────────── 4단계: 확산 콘텐츠 ─────────────────────────
class XThread(BaseModel):
    hook: str = Field(description="스레드 첫 글. 공백 포함 120자 이내, 스크롤을 멈추게 하는 질문이나 장면")
    posts: list[str] = Field(description="이어지는 글 5~7개. 각 글은 공백 포함 130자 이내")
    hashtags: list[str] = Field(description="해시태그 3개 ('#' 포함)")


class BlogSection(BaseModel):
    heading: str
    body: str = Field(description="2~3개 문단. 문단 사이는 빈 줄로 구분")


class Blog(BaseModel):
    title: str
    subtitle: str
    intro: str = Field(description="도입 문단")
    sections: list[BlogSection] = Field(description="본문 3~4개 섹션")
    closing: str = Field(description="맺음 문단. 독자가 오늘 할 수 있는 행동 하나로 끝낸다")


class Card(BaseModel):
    headline: str = Field(description="카드 한 장의 핵심 문구 20자 이내")
    body: str = Field(description="보조 설명 60자 이내")
    visual_idea: str = Field(description="이 카드에 들어갈 이미지·도형·레이아웃 아이디어 한 문장")


class CardNews(BaseModel):
    cards: list[Card] = Field(description="표지 포함 6~8장")
    caption: str = Field(description="인스타그램 등에 올릴 캡션 2~3문장")


class ContentPack(BaseModel):
    x_thread: XThread | None = None
    blog: Blog | None = None
    card_news: CardNews | None = None
    errors: dict[str, str] = Field(default_factory=dict)  # 포맷 키 → 실패 사유 (일부만 실패했을 때)
