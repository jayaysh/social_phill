"""분석 결과를 HTML 조각으로 바꾸는 함수들. 모든 동적 텍스트는 escape 한다."""
from __future__ import annotations

import re
from html import escape as _esc

from agent.schemas import (
    Blog,
    CardNews,
    HistoricalCase,
    IssueStructure,
    SolutionReport,
    XThread,
)
from agent.sources import Paper

from .theme import ROBES, figure_key, is_in_fresco, niche_art_html


def e(text: object) -> str:
    """HTML escape. '$' 는 st.markdown 이 수식으로 해석하지 못하게 엔티티로 바꾼다."""
    return _esc(str(text)).replace("$", "&#36;")


def safe_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else ""


def paras(text: str) -> str:
    return "".join(f"<p>{e(p.strip())}</p>" for p in text.split("\n\n") if p.strip())


def color_map(issue: IssueStructure) -> dict[str, str]:
    """계층 이름 → 옷 색. 분석·충돌·실천안이 같은 색을 공유한다."""
    return {s.layer: ROBES[i % len(ROBES)] for i, s in enumerate(issue.stakeholders)}


def _color(cmap: dict[str, str], name: str) -> str:
    if name in cmap:
        return cmap[name]
    # 표기가 조금 다른 경우(공백 등)를 느슨하게 맞춘다
    norm = name.replace(" ", "")
    for k, v in cmap.items():
        if k.replace(" ", "") == norm or k.replace(" ", "") in norm or norm in k.replace(" ", ""):
            return v
    return "#5A6070"


# ───────────────────────── 1단계 ─────────────────────────
def layers_html(issue: IssueStructure) -> str:
    return (
        '<div class="layers">'
        f'<div class="layer-surface"><b>표면에 보이는 것</b><p>{e(issue.surface_phenomenon)}</p></div>'
        f'<div class="layer-root"><b>그 아래의 뿌리</b><p>{e(issue.root_cause)}</p></div>'
        "</div>"
    )


def questions_html(issue: IssueStructure) -> str:
    items = "".join(f"<li>{e(q)}</li>" for q in issue.core_questions)
    return f'<div class="card"><ul class="qlist">{items}</ul></div>'


def stakeholders_html(issue: IssueStructure, cmap: dict[str, str]) -> str:
    cards = []
    for s in issue.stakeholders:
        c = _color(cmap, s.layer)
        li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)  # noqa: E731
        cards.append(
            f'<div class="card robe" style="--c:{c}"><h4>{e(s.layer)}</h4><p>{e(s.role)}</p>'
            f'<div class="sub">지키려는 것</div><ul>{li(s.interests)}</ul>'
            f'<div class="sub">두려워하는 것</div><ul>{li(s.fears)}</ul></div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>'


def conflicts_html(issue: IssueStructure, cmap: dict[str, str]) -> str:
    rows = []
    for c in issue.conflicts:
        a, b = (c.parties + ["", ""])[:2]
        chips = (
            f'<span class="chip" style="--c:{_color(cmap, a)}">{e(a)}</span>'
            f'<span class="vs">↔</span>'
            f'<span class="chip" style="--c:{_color(cmap, b)}">{e(b)}</span>'
        )
        rows.append(
            f'<div class="conflict"><div>{chips}</div>'
            f'<div><span class="kind">{e(c.kind)}</span> {e(c.description)}</div></div>'
        )
    return f'<div class="card">{"".join(rows)}</div>'


def sources_html(web_sources: list[dict], article_url: str | None) -> str:
    items = []
    if article_url and safe_url(article_url):
        items.append(f'<li>분석한 기사: <a href="{e(article_url)}" target="_blank" rel="noopener noreferrer">{e(article_url)}</a></li>')
    for s in web_sources:
        if safe_url(s["url"]):
            items.append(f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["title"])}</a></li>')
    return f'<ul class="srclist">{"".join(items)}</ul>' if items else ""


# ───────────────────────── 2단계 ─────────────────────────
def _niche_art(c: HistoricalCase, index: int) -> str:
    key = figure_key(c.philosopher, c.philosopher_latin, index)
    # 원작에 그려진 철학자면 그 사람의 이름을, 아니면 벽감의 석상임을 밝힌다
    label = c.philosopher_latin if is_in_fresco(key) else ("아폴론 석상" if key == "apollo" else "아테나 석상")
    return niche_art_html(key, e(label))


def niche_html(c: HistoricalCase, index: int = 0) -> str:
    parallels = "".join(f"<li>{e(p)}</li>" for p in c.parallels)
    return (
        '<div class="niche">'
        f"{_niche_art(c, index)}"
        '<div class="niche-body">'
        f'<p class="niche-era">{e(c.era_place)}</p>'
        f"<h3>{e(c.title)}</h3>"
        f"<p>{e(c.summary)}</p>"
        f'<ul class="qlist">{parallels}</ul>'
        f"<p><b>다른 점.</b> {e(c.differences)}</p>"
        '<div class="phil">'
        f'<span class="name">{e(c.philosopher)}</span><span class="latin">{e(c.philosopher_latin)}</span>'
        f'<div class="theory">{e(c.work)} · {e(c.theory)}</div></div>'
        f"<p>{e(c.lens)}</p>"
        f'<div class="keyq">{e(c.key_question)}</div>'
        "</div></div>"
    )


def papers_html(papers: list[Paper]) -> str:
    if not papers:
        return '<p class="niche-era">검색된 문헌이 없습니다. 네트워크 상태나 검색 한도 때문일 수 있습니다.</p>'
    rows = []
    for p in papers:
        url = safe_url(p.url)
        title = f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(p.title)}</a>' if url else f"<b>{e(p.title)}</b>"
        who = ", ".join(p.authors[:3])
        meta = " · ".join(x for x in [who, str(p.year) if p.year else "", p.venue] if x)
        rows.append(
            f'<div class="paper">{title}<span class="badge">{e(p.source)}</span>'
            f'<div class="meta">{e(meta)}</div><div class="abs">{e(p.abstract)}</div></div>'
        )
    return "".join(rows)


# ───────────────────────── 3단계 ─────────────────────────
def verdict_html(report: SolutionReport, case: HistoricalCase) -> str:
    return (
        f'<div class="verdict"><p class="by">{e(case.philosopher)} · {e(case.theory)}</p>'
        f"<h2>{e(report.headline)}</h2></div>"
    )


def principles_html(report: SolutionReport) -> str:
    return '<div class="principles">' + "".join(f'<div class="principle">{e(p)}</div>' for p in report.principles) + "</div>"


def layer_actions_html(report: SolutionReport, cmap: dict[str, str]) -> str:
    cards = []
    for la in report.layer_actions:
        c = _color(cmap, la.layer)
        acts = "".join(f"<li>{e(a)}</li>" for a in la.actions)
        cards.append(
            f'<div class="card robe" style="--c:{c}"><h4>{e(la.layer)}</h4><ul>{acts}</ul>'
            f'<div class="action-first"><span>첫걸음</span>{e(la.first_step)}</div></div>'
        )
    return f'<div class="grid">{"".join(cards)}</div>'


def roadmap_html(report: SolutionReport) -> str:
    steps = []
    for ph in report.roadmap:
        goals = "".join(f"<li>{e(g)}</li>" for g in ph.goals)
        steps.append(f'<div class="step"><b>{e(ph.horizon)}</b><ul>{goals}</ul></div>')
    return f'<div class="steps">{"".join(steps)}</div>'


def limitations_html(report: SolutionReport) -> str:
    rows = "".join(
        f'<div class="pair"><div><small>한계</small>{e(l.point)}</div><div><small>줄이는 방법</small>{e(l.mitigation)}</div></div>'
        for l in report.limitations
    )
    return f'<div class="card">{rows}</div>'


def resources_html(report: SolutionReport) -> str:
    rows = "".join(f'<div class="res"><b>{e(r.kind)}</b><span>{e(r.detail)}</span></div>' for r in report.resources)
    return f'<div class="card">{rows}</div>'


def indicators_html(report: SolutionReport) -> str:
    return '<div class="card"><ul class="qlist">' + "".join(f"<li>{e(i)}</li>" for i in report.indicators) + "</ul></div>"


# ───────────────────────── 4단계 ─────────────────────────
_X_URL = re.compile(r"https?://\S+")


def x_weight(text: str) -> int:
    """X 의 가중 글자 수. URL 은 길이와 무관하게 23, 유니코드 0~0x10FF·일부 일반 문장부호(0x2000~0x200D,
    0x2010~0x201F, 0x2032~0x2037)는 1, 그 밖의 한글·CJK·이모지는 2 로 센다."""
    text = _X_URL.sub("x" * 23, text)
    total = 0
    for ch in text:
        o = ord(ch)
        total += 1 if (o <= 0x10FF or 0x2000 <= o <= 0x200D or 0x2010 <= o <= 0x201F or 0x2032 <= o <= 0x2037) else 2
    return total


def thread_texts(t: XThread) -> list[str]:
    return [t.hook, *t.posts, " ".join(t.hashtags)]


def tweets_html(t: XThread) -> str:
    out = []
    for text in thread_texts(t):
        w = x_weight(text)
        cls = "cnt over" if w > 280 else "cnt"
        out.append(f'<div class="tweet">{e(text)}<span class="{cls}">{w}/280</span></div>')
    return "".join(out)


def blog_html(b: Blog) -> str:
    """블로그 글을 이스케이프한 HTML 로 보여 준다.

    모델이 만든 텍스트를 st.markdown 에 그대로 넘기면 마크다운 이미지(외부 주소 로드)·링크·수식이
    살아나므로, 화면 표시는 이 함수로 하고 마크다운 원문은 복사·다운로드용으로만 쓴다.
    """
    sections = "".join(
        f'<div class="h3" role="heading" aria-level="3">{e(s.heading)}</div>{paras(s.body)}' for s in b.sections
    )
    return (
        '<div class="card blog">'
        f'<div class="view-title" role="heading" aria-level="2">{e(b.title)}</div>'
        f'<p class="view-lead">{e(b.subtitle)}</p>{paras(b.intro)}{sections}{paras(b.closing)}</div>'
    )


def cards_html(cn: CardNews) -> str:
    out = []
    for c in cn.cards:
        out.append(
            f'<div class="cardnews"><div><h5>{e(c.headline)}</h5><p>{e(c.body)}</p></div>'
            f'<div class="vis">{e(c.visual_idea)}</div></div>'
        )
    return f'<div class="cards">{"".join(out)}</div>'
