"""에이전트의 4단계 추론 파이프라인.

1. analyze_issue  : 입력(키워드/URL) → 현안 구조화
2. match_cases    : 유사 과거 사례 3개 + 철학자·이론 매칭 + 학술 문헌 검색
3. derive_solution: 선택된 관점 → 계층별 해법·한계·자원
4. make_content   : 해법 → X 스레드 / 블로그 / 카드뉴스
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from . import prompts
from .llm import LLM, LLMError
from .schemas import (
    Blog,
    CardNews,
    CaseSet,
    ContentPack,
    HistoricalCase,
    IssueStructure,
    SolutionReport,
    XThread,
)
from .sources import FetchError, Paper, fetch_article, is_url, search_papers


@dataclass
class IssueResult:
    issue: IssueStructure
    web_sources: list[dict] = field(default_factory=list)  # [{"title","url"}]
    article_url: str | None = None
    notices: list[str] = field(default_factory=list)  # 화면에 알릴 안내 (잘림, 웹 검색 실패 등)


def _dump(model) -> str:
    return json.dumps(model.model_dump(), ensure_ascii=False, indent=1)


# ───────────────────────── 1단계 ─────────────────────────
def analyze_issue(llm: LLM, user_input: str, use_web: bool = True) -> IssueResult:
    user_input = user_input.strip()
    article_text = article_title = article_url = None
    notices: list[str] = []

    if is_url(user_input):
        try:
            art = fetch_article(user_input)
        except FetchError as e:
            raise LLMError(str(e)) from e
        article_text, article_title, article_url = art.text, art.title, art.url
        if art.truncated:
            notices.append("기사가 길어 앞부분 약 4만 자만 분석에 사용했습니다.")

    digest, web_sources = None, []
    if use_web:
        try:
            digest, web_sources = llm.research(prompts.research_prompt(article_title or user_input, article_title))
            if not digest:
                notices.append("웹 검색 결과가 비어 있어 일반적 추정으로 대중 시각을 정리했습니다.")
        except LLMError as e:
            if e.fatal:  # 키·권한·모델 문제는 웹 검색을 건너뛰어도 분석 호출에서 똑같이 실패한다
                raise
            notices.append(f"웹 검색을 건너뛰었습니다: {e}")

    issue = llm.parse(
        IssueStructure,
        prompts.SYSTEM,
        prompts.issue_prompt(article_title or user_input, article_text, digest),
    )
    return IssueResult(
        issue=issue,
        web_sources=[{"title": s.title, "url": s.url} for s in web_sources],
        article_url=article_url,
        notices=notices,
    )


# ───────────────────────── 2단계 ─────────────────────────
@dataclass
class CasesResult:
    cases: list[HistoricalCase]
    papers: dict[str, list[Paper]]  # case.id → 검색된 문헌


def match_cases(llm: LLM, issue: IssueStructure, search_academic: bool = True) -> CasesResult:
    case_set = llm.parse(CaseSet, prompts.SYSTEM, prompts.cases_prompt(_dump(issue)))
    cases = case_set.cases[:3]
    papers: dict[str, list[Paper]] = {c.id: [] for c in cases}
    if search_academic:
        def lookup(c: HistoricalCase) -> list[Paper]:
            return search_papers(c.queries_en + c.queries_ko, max_total=5)

        with ThreadPoolExecutor(max_workers=3) as pool:
            for c, found in zip(cases, pool.map(lookup, cases)):
                papers[c.id] = found
    return CasesResult(cases=cases, papers=papers)


# ───────────────────────── 3단계 ─────────────────────────
def _papers_text(papers: list[Paper]) -> str:
    lines = []
    for i, p in enumerate(papers[:5], 1):
        who = ", ".join(p.authors[:3])
        lines.append(f"[{i}] {p.title} ({who}, {p.year or 'n.d.'}) — {p.abstract}")
    return "\n".join(lines)


def derive_solution(
    llm: LLM, issue: IssueStructure, case: HistoricalCase, papers: list[Paper]
) -> SolutionReport:
    return llm.parse(
        SolutionReport,
        prompts.SYSTEM,
        prompts.solution_prompt(_dump(issue), _dump(case), _papers_text(papers)),
    )


# ───────────────────────── 4단계 ─────────────────────────
_FORMATS = {"x_thread": XThread, "blog": Blog, "card_news": CardNews}


def make_content(
    llm: LLM,
    issue: IssueStructure,
    case: HistoricalCase,
    report: SolutionReport,
    formats: list[str],
) -> ContentPack:
    """선택된 포맷만 병렬로 생성한다.

    일부 포맷만 실패하면 성공한 결과는 살려서 돌려주고 실패 사유는 pack.errors 에 담는다.
    전부 실패하면 첫 번째 오류를 그대로 던진다.
    """
    formats = [f for f in formats if f in _FORMATS]
    issue_j, case_j, report_j = _dump(issue), _dump(case), _dump(report)

    def one(fmt: str):
        try:
            return llm.parse(_FORMATS[fmt], prompts.SYSTEM, prompts.content_prompt(fmt, issue_j, case_j, report_j))
        except LLMError as e:
            return e

    pack = ContentPack()
    first_error: LLMError | None = None
    with ThreadPoolExecutor(max_workers=3) as pool:
        for fmt, result in zip(formats, pool.map(one, formats)):
            if isinstance(result, LLMError):
                pack.errors[fmt] = str(result)
                first_error = first_error or result
            else:
                setattr(pack, fmt, result)
    if first_error and len(pack.errors) == len(formats):
        raise first_error
    return pack
