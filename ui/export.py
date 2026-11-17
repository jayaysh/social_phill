"""분석 결과·콘텐츠를 다운로드용 Markdown 으로 변환한다."""
from __future__ import annotations

from agent.pipeline import IssueResult
from agent.schemas import Blog, CardNews, HistoricalCase, SolutionReport, XThread
from agent.sources import Paper


def report_markdown(res: IssueResult, case: HistoricalCase, report: SolutionReport, papers: list[Paper]) -> str:
    i = res.issue
    L: list[str] = [f"# {i.title}", "", f"> {report.headline}", ""]
    L += ["## 1. 현안 구조화", "", i.summary, "", f"**표면 현상.** {i.surface_phenomenon}", "", f"**근본 원인.** {i.root_cause}", ""]
    L += ["### 핵심 쟁점", *[f"- {q}" for q in i.core_questions], ""]
    L += ["### 연루된 계층"]
    for s in i.stakeholders:
        L += [f"- **{s.layer}** — {s.role}", f"  - 지키려는 것: {', '.join(s.interests)}", f"  - 두려워하는 것: {', '.join(s.fears)}"]
    L += ["", "### 이해관계 충돌"]
    L += [f"- {' ↔ '.join(c.parties)} ({c.kind}): {c.description}" for c in i.conflicts]
    L += ["", f"**대중의 시각.** {i.public_perception}", ""]
    L += ["## 2. 선택한 관점", "", f"### {case.title} ({case.era_place})", case.summary, "",
          f"**{case.philosopher} ({case.philosopher_latin})** — {case.work} · {case.theory}", "", case.lens, "",
          f"> {case.key_question}", ""]
    L += ["## 3. 해법", "", report.logic, "", "### 원칙", *[f"- {p}" for p in report.principles], "", "### 계층별 실천안"]
    for la in report.layer_actions:
        L += [f"#### {la.layer}", *[f"- {a}" for a in la.actions], f"- **첫걸음:** {la.first_step}", ""]
    L += ["### 로드맵"]
    for ph in report.roadmap:
        L += [f"**{ph.horizon}**", *[f"- {g}" for g in ph.goals], ""]
    L += ["### 한계점"]
    L += [f"- {l.point} → {l.mitigation}" for l in report.limitations]
    L += ["", "### 필요 자원"] + [f"- **{r.kind}:** {r.detail}" for r in report.resources]
    L += ["", "### 확인할 지표"] + [f"- {x}" for x in report.indicators]
    if report.evidence_note:
        L += ["", f"> {report.evidence_note}"]
    if papers:
        L += ["", "## 참고 문헌 후보 (검색 결과, 직접 확인 필요)"]
        for n, p in enumerate(papers[:5], 1):
            L.append(f"{n}. {p.title} — {', '.join(p.authors[:3])} ({p.year or 'n.d.'}) {p.url}".rstrip())
    if res.web_sources:
        L += ["", "## 웹 리서치 출처"] + [f"- [{s['title']}]({s['url']})" for s in res.web_sources]
    return "\n".join(L) + "\n"


def thread_text(t: XThread) -> str:
    posts = [t.hook, *t.posts, " ".join(t.hashtags)]
    return "\n\n".join(f"({n}/{len(posts)}) {p}" for n, p in enumerate(posts, 1))


def blog_markdown(b: Blog) -> str:
    body = "\n\n".join(f"## {s.heading}\n\n{s.body}" for s in b.sections)
    return f"# {b.title}\n\n_{b.subtitle}_\n\n{b.intro}\n\n{body}\n\n{b.closing}\n"


def cardnews_markdown(cn: CardNews) -> str:
    cards = "\n\n".join(
        f"### 카드 {n}. {c.headline}\n\n{c.body}\n\n- 시각 아이디어: {c.visual_idea}" for n, c in enumerate(cn.cards, 1)
    )
    return f"{cards}\n\n---\n\n**캡션**\n\n{cn.caption}\n"
