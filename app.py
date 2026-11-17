"""갈등분쇄기 — 역사·철학 기반 사회갈등 해결 에이전트 (Streamlit).

실행:  streamlit run app.py
"""
from __future__ import annotations

import os
import re

import streamlit as st

from agent import demo_data, pipeline
from agent.llm import DEFAULT_MODEL, LLM, LLMError
from agent.providers import KEY_ENV, PROVIDERS, default_model, make_llm as build_llm, model_choices
from ui import components as C
from ui import export
from ui.theme import CSS, banner_html, hero_html

st.set_page_config(page_title="갈등분쇄기 · 아테네 학당", page_icon="🏛️", layout="wide")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

STEPS = ["현안 구조화", "관점 큐레이션", "솔루션 도출", "확산 콘텐츠"]
NUMERALS = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ"]
VIEW_STEP = {"input": 0, "issue": 0, "cases": 1, "solution": 2, "content": 3}
EXAMPLES = ["국민연금 개혁 세대 갈등", "의대 정원 확대 의정 갈등", "플랫폼 노동자 보호 논쟁", "지역 대형마트 의무휴업"]
FORMATS = {"x_thread": "X 스레드", "blog": "블로그 글", "card_news": "카드뉴스 기획안"}
DEPTHS = {"빠르게": "low", "보통": "medium", "깊게": "high"}


def H(markup: str) -> None:
    """HTML 조각을 그린다. st.html 은 이미지·SVG 를 제거하므로 st.markdown 을 쓴다.
    빈 줄은 마크다운의 HTML 블록을 끊으므로 공백으로 접는다."""
    st.markdown(re.sub(r"\s*\n\s*", " ", markup), unsafe_allow_html=True)


# ───────────────────────── 설정·상태 ─────────────────────────
def _secret(name: str) -> str | None:
    try:
        return st.secrets.get(name)
    except Exception:  # secrets.toml 이 없으면 예외가 난다
        return None


# 제공자별로 서버에 저장된 키(secrets 또는 환경변수)를 찾는다
SERVER_KEYS = {prov: (_secret(env) or os.environ.get(env)) for prov, env in KEY_ENV.items()}
if _secret("S2_API_KEY"):
    os.environ.setdefault("S2_API_KEY", _secret("S2_API_KEY"))  # type: ignore[arg-type]

_defaults = {
    "view": "input", "saved_query": "", "issue_res": None, "cases_res": None, "chosen_id": None,
    "solution": None, "content": None, "demo": not any(SERVER_KEYS.values()),
}
for k, v in _defaults.items():
    st.session_state.setdefault(k, v)
# 'query' 는 입력 위젯의 키라서 기본값 목록에 두지 않는다. 입력 화면이 아닐 때 위젯과 함께 사라지는데,
# 매 실행마다 ""로 되살리면 '입력 수정'으로 돌아왔을 때 입력창이 비어 버린다. 대신 saved_query 에 보관한다.


def reset_all() -> None:
    for k, v in _defaults.items():
        if k != "demo":
            st.session_state[k] = v
    st.session_state["query"] = ""


def go(view: str) -> None:
    st.session_state.view = view


def set_query(text: str) -> None:
    st.session_state.query = text


def _default_provider() -> str:
    """서버에 OpenAI 키만 있으면 OpenAI 를, 그 밖에는 Anthropic 을 기본으로 한다."""
    return "openai" if SERVER_KEYS["openai"] and not SERVER_KEYS["anthropic"] else "anthropic"


def sidebar() -> dict:
    sb = st.sidebar
    sb.markdown("### 설정")
    demo = sb.toggle(
        "데모 모드", key="demo",
        help="API 호출 없이 '국민연금 개혁' 예시 결과로 전체 흐름을 체험합니다. 입력과 무관하게 같은 결과가 나옵니다.",
    )
    cfg = {"demo": demo, "provider": "anthropic", "key": None, "model": DEFAULT_MODEL, "effort": "medium", "web": True, "academic": True}
    if not demo:
        # segmented_control 은 선택된 항목을 다시 누르면 선택이 해제돼(None) 혼란스러우므로 라디오를 쓴다
        providers = list(PROVIDERS)
        provider = sb.radio(
            "AI 제공자", providers, format_func=PROVIDERS.get, horizontal=True,
            index=providers.index(_default_provider()), key="provider_radio",
            help="분석에 쓸 모델의 제공자입니다. 선택한 제공자의 API 키가 필요합니다.",
        )
        cfg["provider"] = provider
        label = PROVIDERS[provider]
        if SERVER_KEYS[provider]:
            sb.success(f"서버에 저장된 {label} 키를 사용합니다.")
            cfg["key"] = SERVER_KEYS[provider]
        else:
            cfg["key"] = sb.text_input(
                f"{label} API 키", type="password", key=f"user_key_{provider}",
                placeholder="sk-..." if provider == "openai" else "sk-ant-...",
                help="이 세션에서만 쓰이며 저장되지 않습니다. 선택한 제공자에게만 전송됩니다.",
            ) or None
        choices = model_choices(provider)
        if provider == "openai":
            custom = "직접 입력"
            options = [*choices, custom]
            picked = sb.selectbox(
                "모델", options, format_func=lambda m: choices.get(m, "직접 입력…"), key="model_openai",
                index=options.index(default_model("openai")),  # 목록 순서와 무관하게 (기본) 표시와 같은 모델로 시작
            )
            if picked == custom:
                picked = sb.text_input("모델 이름", key="model_openai_custom", placeholder="예: gpt-5.5") or next(iter(choices))
            cfg["model"] = picked
            sb.caption("모델 목록은 OpenAI SDK에 정의된 이름이며, 이 키로 실제 사용 가능한지는 계정에 따라 다릅니다.")
        else:
            cfg["model"] = sb.selectbox("모델", list(choices), format_func=choices.get, key="model_anthropic")
        depth = sb.select_slider("분석 깊이", options=list(DEPTHS), value="보통", key="depth", help="깊을수록 정확하지만 오래 걸리고 비용이 늘어납니다.")
        cfg["effort"] = DEPTHS[depth]
        cfg["web"] = sb.toggle(
            "웹 검색으로 최신 여론 반영", value=True, key="web",
            help="뉴스·YouTube 해설·블로그를 검색해 대중의 시각을 정리합니다. 제공자의 웹 검색 도구를 쓰므로 호출당 추가 요금이 붙을 수 있습니다.",
        )
        cfg["academic"] = sb.toggle("학술 문헌 검색", value=True, key="academic", help="Semantic Scholar · OpenAlex · arXiv 에서 근거 문헌 후보를 찾습니다.")
    sb.divider()
    sb.button("처음부터 다시", on_click=reset_all, width="stretch")
    sb.caption("분석 결과는 AI가 생성한 것으로, 역사적 사실과 문헌은 직접 확인해 주세요.")
    return cfg


def run_step(label: str, steps: list[str], fn, *args):
    """st.status 로 진행 상황을 보여 주며 fn 을 실행한다. 실패하면 None."""
    with st.status(label, expanded=True) as status:
        progress = st.empty()  # 실패하면 지운다: 하지 않은 단계를 한 것처럼 보이지 않게
        progress.markdown("\n".join(f"- {s}" for s in steps))
        try:
            result = fn(*args)
        except LLMError as ex:
            progress.empty()
            # expanded=True 를 다시 주지 않으면 실패 상태에서 위젯이 접혀 오류 메시지가 가려진다
            status.update(label="실패했습니다", state="error", expanded=True)
            st.error(str(ex))
            return None
        except Exception as ex:  # 키 미설정 등 SDK 의 인증 구성 오류 포함
            progress.empty()
            status.update(label="실패했습니다", state="error", expanded=True)
            msg = str(ex)
            if "authentication" in msg.lower() or "api_key" in msg.lower() or "credential" in msg.lower():
                msg = "API 키가 설정되지 않았습니다. 사이드바에 키를 입력하거나 데모 모드를 켜 주세요."
            st.error(f"처리 중 오류가 발생했습니다: {msg}")
            return None
        progress.empty()
        status.update(label="완료", state="complete")
        return result


def make_llm(cfg: dict) -> LLM:
    return build_llm(cfg["provider"], cfg["key"], cfg["model"], cfg["effort"])


# ───────────────────────── 계단형 진행 표시 ─────────────────────────
def render_stairs() -> None:
    s = st.session_state
    active = VIEW_STEP[s.view]
    reachable = [True, s.cases_res is not None, s.solution is not None, s.content is not None]
    targets = ["issue" if s.issue_res else "input", "cases", "solution", "content"]
    with st.container(key="stairs"):
        cols = st.columns(4)
        for i, col in enumerate(cols):
            status = "active" if i == active else ("done" if reachable[i] else "locked")
            with col:
                st.button(
                    f"{NUMERALS[i]}  {STEPS[i]}", key=f"stair_{i}_{status}", width="stretch",
                    disabled=(status == "locked"), on_click=go, args=(targets[i],),
                )


# ───────────────────────── 화면: 입력 ─────────────────────────
def view_input(cfg: dict) -> None:
    H(
        '<div class="view-title" role="heading" aria-level="2">어떤 갈등을 풀어볼까요?</div>'
        '<p class="view-lead">사회문제 키워드나 뉴스 기사 주소를 넣어 주세요. 갈등의 구조를 진단하고, '
        "닮은 역사 사례와 철학자를 찾아 해법까지 이어 갑니다.</p>"
    )
    st.session_state.setdefault("query", st.session_state.saved_query)
    st.text_area(
        "현안 입력", key="query", height=110, label_visibility="collapsed",
        placeholder="예) 국민연금 개혁 세대 갈등     또는     https://news.example.com/article/123",
    )
    cols = st.columns(len(EXAMPLES))
    for i, (col, ex) in enumerate(zip(cols, EXAMPLES)):
        col.button(ex, key=f"ex_{i}", on_click=set_query, args=(ex,), width="stretch")

    if cfg["demo"]:
        H('<div class="notice">데모 모드가 켜져 있습니다. 입력과 관계없이 예시 시나리오(국민연금 개혁)가 표시됩니다.</div>')

    q = st.session_state.query.strip()
    if st.button("현안 분석하기", type="primary", disabled=not q):
        if cfg["demo"]:
            res = run_step("현안을 구조화하는 중", ["예시 데이터를 불러옵니다."], demo_data.demo_issue)
        else:
            steps = ["기사 본문을 읽습니다." if pipeline.is_url(q) else "키워드를 해석합니다."]
            if cfg["web"]:
                steps.append("웹에서 최근 보도와 대중 담론을 조사합니다.")
            steps.append("쟁점·계층·충돌 양상을 구조화합니다. (1~2분 걸릴 수 있습니다)")
            res = run_step("현안을 구조화하는 중", steps, pipeline.analyze_issue, make_llm(cfg), q, cfg["web"])
        if res:
            st.session_state.update(
                issue_res=res, cases_res=None, chosen_id=None, solution=None, content=None,
                saved_query=q, view="issue",
            )
            st.rerun()


# ───────────────────────── 화면: 현안 구조 ─────────────────────────
def view_issue(cfg: dict) -> None:
    res = st.session_state.issue_res
    issue = res.issue
    cmap = C.color_map(issue)
    for n in res.notices:
        H(f'<div class="notice">{C.e(n)}</div>')
    H(f'<div class="view-title" role="heading" aria-level="2">{C.e(issue.title)}</div><p class="view-lead">{C.e(issue.summary)}</p>')
    H(C.layers_html(issue))
    H('<div class="h3" role="heading" aria-level="3">핵심 쟁점</div><div class="meander light"></div>' + C.questions_html(issue))
    H('<div class="h3" role="heading" aria-level="3">연루된 사회 계층</div><div class="meander light"></div>' + C.stakeholders_html(issue, cmap))
    H('<div class="h3" role="heading" aria-level="3">이해관계가 부딪히는 지점</div><div class="meander light"></div>' + C.conflicts_html(issue, cmap))
    H(
        '<div class="h3" role="heading" aria-level="3">대중이 보는 방식</div><div class="meander light"></div>'
        f'<div class="card">{C.paras(issue.public_perception)}{C.sources_html(res.web_sources, res.article_url)}</div>'
    )
    st.write("")
    left, right = st.columns([1, 3])
    left.button("← 입력 수정", on_click=go, args=("input",), width="stretch")
    if right.button("다음 · 닮은 역사 사례와 철학자 찾기", type="primary", width="stretch"):
        if cfg["demo"]:
            out = run_step("유사 사례를 찾는 중", ["예시 데이터를 불러옵니다."], demo_data.demo_cases)
        else:
            steps = ["현안과 구조가 닮은 과거 갈등 3건을 고릅니다.", "각 사례를 분석한 철학자와 핵심 이론을 짝짓습니다."]
            if cfg["academic"]:
                steps.append("Semantic Scholar · OpenAlex · arXiv 에서 근거 문헌을 검색합니다.")
            out = run_step("유사 사례를 찾는 중", steps, pipeline.match_cases, make_llm(cfg), issue, cfg["academic"])
        if out:
            st.session_state.update(cases_res=out, chosen_id=None, solution=None, content=None, view="cases")
            st.rerun()


# ───────────────────────── 화면: 관점 선택 ─────────────────────────
def view_cases(cfg: dict) -> None:
    res = st.session_state.cases_res
    H(
        '<div class="view-title" role="heading" aria-level="2">닮은 갈등, 서로 다른 지혜</div>'
        '<p class="view-lead">비슷한 구조로 갈등을 겪은 세 사례와, 이를 분석한 철학자입니다. '
        "하나를 고르면 그 관점의 논리로 구체적인 해법을 도출합니다.</p>"
    )
    cols = st.columns(len(res.cases), gap="medium")
    picked = None
    for i, (col, c) in enumerate(zip(cols, res.cases)):
        with col:
            H(C.niche_html(c, i))
            papers = res.papers.get(c.id, [])
            label = f"근거 문헌 후보 ({len(papers)})" if papers else "근거 문헌 후보"
            with st.expander(label):
                H(C.papers_html(papers))
            if st.button("이 관점으로 해법 도출", key=f"pick_{c.id}", type="primary", width="stretch"):
                picked = c
    st.caption("문헌은 검색으로 찾은 후보이며 내용을 직접 확인해야 합니다." if not cfg["demo"] else "데모 모드에서는 검색 대신 해당 이론의 고전 저작을 보여 줍니다.")
    st.button("← 현안 구조로 돌아가기", on_click=go, args=("issue",))

    if picked:
        issue = st.session_state.issue_res.issue
        papers = res.papers.get(picked.id, [])
        if cfg["demo"]:
            sol = run_step("해법을 도출하는 중", ["예시 데이터를 불러옵니다."], demo_data.demo_solution, picked.id)
        else:
            steps = [f"{picked.philosopher}의 '{picked.theory}'로 현안을 다시 읽습니다.", "계층별 실천안·한계·필요 자원을 도출합니다."]
            sol = run_step("해법을 도출하는 중", steps, pipeline.derive_solution, make_llm(cfg), issue, picked, papers)
        if sol:
            st.session_state.update(chosen_id=picked.id, solution=sol, content=None, view="solution")
            st.rerun()


# ───────────────────────── 화면: 솔루션 ─────────────────────────
def _chosen():
    s = st.session_state
    case = next(c for c in s.cases_res.cases if c.id == s.chosen_id)
    return case, s.cases_res.papers.get(case.id, [])


def view_solution(cfg: dict) -> None:
    s = st.session_state
    issue = s.issue_res.issue
    cmap = C.color_map(issue)
    case, papers = _chosen()
    rep = s.solution

    H(C.verdict_html(rep, case))
    H(f'<div class="h3" role="heading" aria-level="3">논리 전개</div><div class="meander light"></div><div class="card">{C.paras(rep.logic)}</div>')
    H('<div class="h3" role="heading" aria-level="3">해법을 관통하는 원칙</div><div class="meander light"></div>' + C.principles_html(rep))
    H('<div class="h3" role="heading" aria-level="3">각자의 자리에서 할 수 있는 일</div><div class="meander light"></div>' + C.layer_actions_html(rep, cmap))
    H('<div class="h3" role="heading" aria-level="3">로드맵</div><div class="meander light"></div>' + C.roadmap_html(rep))
    H('<div class="h3" role="heading" aria-level="3">이 해법의 한계</div><div class="meander light"></div>' + C.limitations_html(rep))
    H('<div class="h3" role="heading" aria-level="3">필요한 자원</div><div class="meander light"></div>' + C.resources_html(rep))
    H('<div class="h3" role="heading" aria-level="3">작동하는지 확인하는 법</div><div class="meander light"></div>' + C.indicators_html(rep))
    if rep.evidence_note:
        H(f'<div class="notice">{C.e(rep.evidence_note)}</div>')
    if papers:
        with st.expander("참고한 문헌 후보"):
            H(C.papers_html(papers[:5]))

    H('<div class="h3" role="heading" aria-level="3">확산 콘텐츠로 바꾸기</div><div class="meander light"></div><p class="view-lead">이 분석을 원하는 채널의 글감으로 변환합니다.</p>')
    chosen = st.pills(
        "만들 포맷", list(FORMATS), format_func=FORMATS.get, selection_mode="multi",
        default=list(FORMATS), key="formats", label_visibility="collapsed",
    )
    a, b, c = st.columns([2, 2, 1.4])
    if a.button("콘텐츠 만들기", type="primary", width="stretch", disabled=not chosen):
        if cfg["demo"]:
            pack = run_step("콘텐츠를 만드는 중", ["예시 데이터를 조립합니다."], demo_data.demo_content, issue, case, rep, chosen)
        else:
            names = ", ".join(FORMATS[f] for f in chosen)
            pack = run_step("콘텐츠를 만드는 중", [f"{names}을(를) 동시에 작성합니다."], pipeline.make_content, make_llm(cfg), issue, case, rep, chosen)
        if pack:
            st.session_state.update(content=pack, view="content")
            st.rerun()
    b.download_button(
        "해법 리포트 내려받기 (.md)", export.report_markdown(s.issue_res, case, rep, papers),
        file_name="갈등해결_리포트.md", mime="text/markdown", width="stretch",
    )
    c.button("← 관점 다시 고르기", on_click=go, args=("cases",), width="stretch")


# ───────────────────────── 화면: 확산 콘텐츠 ─────────────────────────
def view_content(cfg: dict) -> None:
    pack = st.session_state.content
    H(
        '<div class="view-title" role="heading" aria-level="2">확산 콘텐츠</div>'
        '<p class="view-lead">그대로 올리기 전에 사실관계와 어조를 한 번 읽어 보세요. 복사 버튼은 코드 상자 오른쪽 위에 있습니다.</p>'
    )
    for fmt, reason in pack.errors.items():
        st.warning(f"{FORMATS[fmt]}은(는) 만들지 못했습니다. {reason}")
    present = [(k, FORMATS[k]) for k in FORMATS if getattr(pack, k)]
    tabs = st.tabs([name for _, name in present])
    for tab, (key, _) in zip(tabs, present):
        with tab:
            if key == "x_thread":
                t = pack.x_thread
                H(C.tweets_html(t))
                over = [i for i, x in enumerate(C.thread_texts(t), 1) if C.x_weight(x) > 280]
                if over:
                    st.warning(f"{', '.join(map(str, over))}번째 글이 280(한글 140자)을 넘습니다. 줄여서 올려 주세요.")
                text = export.thread_text(t)
                st.code(text, language=None, wrap_lines=True)
                st.download_button("스레드 내려받기 (.txt)", text, file_name="x_thread.txt", key="dl_x")
            elif key == "blog":
                md = export.blog_markdown(pack.blog)
                H(C.blog_html(pack.blog))
                with st.expander("복사용 원문 (Markdown)"):
                    st.code(md, language="markdown", wrap_lines=True)
                st.download_button("블로그 글 내려받기 (.md)", md, file_name="blog.md", key="dl_blog")
            else:
                cn = pack.card_news
                H(C.cards_html(cn))
                H(f'<p class="view-lead"><b>캡션</b> — {C.e(cn.caption)}</p>')
                md = export.cardnews_markdown(cn)
                with st.expander("기획안 원문"):
                    st.code(md, language="markdown", wrap_lines=True)
                st.download_button("기획안 내려받기 (.md)", md, file_name="card_news.md", key="dl_card")
    st.write("")
    a, b = st.columns(2)
    a.button("← 해법으로 돌아가기", on_click=go, args=("solution",), width="stretch")
    b.button("다른 관점으로 비교하기", on_click=go, args=("cases",), width="stretch")


# ───────────────────────── 메인 ─────────────────────────
def main() -> None:
    cfg = sidebar()
    H(hero_html() if st.session_state.view == "input" else banner_html(st.session_state.view))
    render_stairs()
    {"input": view_input, "issue": view_issue, "cases": view_cases, "solution": view_solution, "content": view_content}[
        st.session_state.view
    ](cfg)


main()
