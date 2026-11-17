"""'아테네 학당'(라파엘로, 1511) 원작 이미지를 적극 활용한 테마.

원작은 퍼블릭 도메인이며 static/school_of_athens.jpg (1920x1490) 로 함께 배포한다.
- 머리글: 금박 액자에 담은 프레스코 + 비문 명판
- 단계 배너: 프레스코의 부분 확대(헤라클레이토스, 플라톤·아리스토텔레스 …)
- 벽감 카드: 실제 그림 속 철학자·아폴론/아테나 석상을 크롭해 넣는다
- 배경: 프레스코를 아주 옅게 깔고, 그리스 메안더 문양과 금색 장식으로 마감한다
- 계층 구분색은 그림 속 인물의 옷 색(장미·군청·황토·세이지·보라·청록)에서 가져왔다
"""
from __future__ import annotations

import base64
from pathlib import Path

IMG_W, IMG_H = 1920, 1490
_IMG_PATH = Path(__file__).resolve().parent.parent / "static" / "school_of_athens.jpg"


def _image_url() -> str:
    """원작 이미지를 CSS 에 직접 내장한다.

    정적 파일 서빙(/app/static/…)은 배포 환경(Streamlit Community Cloud 등)이 앱을 하위 경로 아래에서
    서빙하면 절대 경로가 404 가 된다. 내장하면 경로·서버 설정에 의존하지 않는다. 파일을 읽지 못하면
    접두사 문제를 피하려고 슬래시 없는 상대 경로로 폴백한다. 큰 메시지는 Streamlit 이 클라이언트에 캐시하므로
    매 실행마다 다시 전송되지는 않는다.
    """
    try:
        data = _IMG_PATH.read_bytes()
    except OSError:
        return "app/static/school_of_athens.jpg"
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")


IMG_URL = _image_url()  # 모듈 로드 시 한 번만 계산

# 계층 구분용 '옷 색' — 흰 글자와 대비 4.5:1 이상
ROBES = ["#A8475E", "#2F5DA8", "#8A5D0C", "#4F7355", "#7A5A8C", "#2F6F77"]

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Cinzel:wght@500;700;900&family=Noto+Serif+KR:wght@400;500;700;800;900&display=swap');"
)

# ───────────────────────── 원작 이미지 크롭 ─────────────────────────
# 인물 크롭: (중심 x, 중심 y, 한 변) — 원본 픽셀 좌표, 정사각형
FIGURES: dict[str, tuple[int, int, int]] = {
    "plato": (935, 770, 240),
    "aristotle": (1035, 770, 240),
    "socrates": (705, 740, 270),
    "pythagoras": (500, 1010, 310),
    "heraclitus": (850, 1030, 310),
    "euclid": (1480, 1030, 330),
    "diogenes": (1130, 930, 310),
    "epicurus": (320, 840, 230),
    "zoroaster": (1640, 840, 270),
    "apollo": (450, 400, 350),
    "athena": (1510, 420, 350),
}
# 철학자 이름(한글/영문 일부) → 크롭 키
FIGURE_NAMES: dict[str, str] = {
    "플라톤": "plato", "plato": "plato",
    "아리스토텔레스": "aristotle", "aristotle": "aristotle",
    "소크라테스": "socrates", "socrates": "socrates",
    "피타고라스": "pythagoras", "pythagoras": "pythagoras",
    "헤라클레이토스": "heraclitus", "heraclitus": "heraclitus",
    "디오게네스": "diogenes", "diogenes": "diogenes",
    "에우클레이데스": "euclid", "유클리드": "euclid", "euclid": "euclid",
    "에피쿠로스": "epicurus", "epicurus": "epicurus",
    "조로아스터": "zoroaster", "프톨레마이오스": "zoroaster",
}
# 띠 모양 배너: (x, y, 너비, 높이)
BANNERS: dict[str, tuple[int, int, int, int]] = {
    "hero": (160, 100, 1600, 860),
    "issue": (380, 860, 960, 380),
    "cases": (505, 590, 960, 380),
    "solution": (820, 850, 960, 380),
    "content": (960, 590, 960, 380),
}
BANNER_CAPTIONS: dict[str, tuple[str, str]] = {
    "issue": ("헤라클레이토스와 피타고라스", "「투쟁은 만물의 아버지」 — 갈등을 외면하지 않고 그 구조를 읽는 데서 출발합니다."),
    "cases": ("플라톤과 아리스토텔레스", "플라톤은 하늘(이상)을, 아리스토텔레스는 땅(경험)을 가리킵니다. 같은 현안에도 여러 관점이 있습니다."),
    "solution": ("에우클레이데스(혹은 아르키메데스)", "컴퍼스로 도형을 그리듯, 선택한 관점을 구체적인 해법으로 작도합니다."),
    "content": ("아테네 학당의 사람들", "배움은 대화로 퍼집니다. 분석을 각자의 채널로 옮겨 봅시다."),
}


def _bg(x: float, y: float, w: float, h: float) -> str:
    size = IMG_W / w * 100
    px = x / (IMG_W - w) * 100 if IMG_W != w else 0
    py = y / (IMG_H - h) * 100 if IMG_H != h else 0
    return f"background-size:{size:.3f}% auto;background-position:{px:.3f}% {py:.3f}%;"


def _crop_css() -> str:
    rules = [f".crop{{background-image:var(--fresco);background-repeat:no-repeat;background-color:#CDBF9B;}}"]
    for key, (cx, cy, cw) in FIGURES.items():
        rules.append(f".crop-{key}{{aspect-ratio:1/1;{_bg(cx - cw / 2, cy - cw / 2, cw, cw)}}}")
    for key, (x, y, w, h) in BANNERS.items():
        rules.append(f".crop-{key}{{aspect-ratio:{w}/{h};{_bg(x, y, w, h)}}}")
    return "\n".join(rules)


def figure_key(philosopher: str, philosopher_latin: str, index: int) -> str:
    """철학자가 원작에 그려져 있으면 그 인물을, 아니면 벽감 속 아폴론/아테나 석상을 쓴다."""
    text = f"{philosopher} {philosopher_latin}".lower()
    for name, key in FIGURE_NAMES.items():
        if name in text:
            return key
    return ("apollo", "athena")[index % 2]


def is_in_fresco(key: str) -> bool:
    return key not in ("apollo", "athena")


# ───────────────────────── 그리스 메안더 문양 ─────────────────────────
def _meander_uri(color: str, bg: str | None = None) -> str:
    rect = f'<rect width="28" height="20" fill="{bg}"/>' if bg else ""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="20" viewBox="0 0 28 20">'
        f"{rect}"
        f'<path d="M0 17H28M3 17V3H25V13H10V8H18" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="square"/>'
        "</svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


CSS = (
    FONT_IMPORT
    + ":root{--fresco:url('"
    + IMG_URL
    + "');}"  # 원작 이미지는 여기에 한 번만 담고 .crop / .stApp 이 var(--fresco)로 참조한다
    + """
:root{
  --parch:#EDE6D3; --parch-hi:#FBF7EA; --stone:#DDD2B4; --stone-dk:#B09A62;
  --lapis:#23407A; --lapis-deep:#14264B; --sky-pale:#DCE8EE;
  --gold:#C79A2E; --gold-lt:#F3DA8F; --gold-dk:#8A6418; --ink:#241F17; --muted:#5E5646;
  --gilt:linear-gradient(135deg,#E8C766 0%,#B38A2E 30%,#F3DA8F 50%,#9C7424 72%,#E2BC5A 100%);
}
"""
    + _crop_css()
    + """
.stApp{
  background-color:var(--parch);
  background-image:linear-gradient(rgba(237,230,211,.935),rgba(237,230,211,.935)),var(--fresco);
  background-size:cover; background-position:center top; background-attachment:fixed;
}
.stApp, .stMarkdown, .stMarkdown p, .stMarkdown li, label, [data-testid="stWidgetLabel"] p,
.stTextArea textarea, .stTextInput input, .stButton button, [data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"], .stDownloadButton button, [data-baseweb="tab"]{
  font-family:'Noto Serif KR','Source Serif 4',serif;
}
.block-container{max-width:1080px; padding-top:1.2rem; padding-bottom:5rem;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer, .stAppDeployButton{visibility:hidden;}
.stMarkdown p, .stMarkdown li{line-height:1.85; color:var(--ink);}
[data-testid="stSidebar"]{border-right:3px solid var(--gold);}
[data-testid="stSidebar"] .stButton button{border:1px solid var(--gold) !important; color:var(--gold-lt) !important; background:transparent !important;}
[data-testid="stSidebar"] .stButton button:hover{background:rgba(243,218,143,.12) !important;}
:focus-visible{outline:2px solid var(--gold-dk); outline-offset:2px;}

/* ── 문양 ─────────────────────────────────── */
.meander{height:20px; background:var(--lapis-deep) url('"""
    + _meander_uri("#E2BC5A")
    + """') repeat-x center; border-top:2px solid var(--gold); border-bottom:2px solid var(--gold);}
.meander.light{background:transparent url('"""
    + _meander_uri("#B38A2E")
    + """') repeat-x center; border:none; height:20px; margin:.4rem 0 .2rem; opacity:.9;}

/* ── 금박 액자 ───────────────────────────── */
.frame{position:relative; padding:13px; background:var(--gilt); border-radius:3px;
  box-shadow:0 14px 34px rgba(50,35,10,.38), 0 0 0 1px #6F5316;}
.frame::before{content:""; position:absolute; inset:6px; border:1px solid rgba(70,48,8,.7); pointer-events:none; z-index:3;}
.frame::after{content:""; position:absolute; inset:-1px; pointer-events:none; z-index:4;
  background:
   radial-gradient(circle,#7A2433 0 4px,#F6E3A1 4.5px 7px,#8A6418 7.5px 9px,transparent 9.5px) 0 0/28px 28px no-repeat,
   radial-gradient(circle,#7A2433 0 4px,#F6E3A1 4.5px 7px,#8A6418 7.5px 9px,transparent 9.5px) 100% 0/28px 28px no-repeat,
   radial-gradient(circle,#7A2433 0 4px,#F6E3A1 4.5px 7px,#8A6418 7.5px 9px,transparent 9.5px) 0 100%/28px 28px no-repeat,
   radial-gradient(circle,#7A2433 0 4px,#F6E3A1 4.5px 7px,#8A6418 7.5px 9px,transparent 9.5px) 100% 100%/28px 28px no-repeat;}
.frame .crop{width:100%; position:relative; box-shadow:inset 0 0 0 2px rgba(60,40,5,.75), inset 0 -60px 60px -40px rgba(20,38,75,.35);}
.frame .cap{position:absolute; left:13px; right:13px; bottom:13px; z-index:2; padding:1.6rem 1.2rem .8rem;
  background:linear-gradient(0deg,rgba(20,38,75,.94) 0%,rgba(20,38,75,.78) 55%,rgba(20,38,75,0) 100%); color:#F7EFD6; line-height:1.6;}
.frame .cap b{color:var(--gold-lt); font-size:1.05rem; margin-right:.6rem;}
.frame .cap span{font-size:.92rem;}

/* ── 머리글 명판 ───────────────────────────── */
.hero{margin:0;}
.plaque{position:relative; z-index:5; margin:-46px auto 0; width:min(680px,88%); text-align:center; padding:1.1rem 1.5rem 1.2rem;
  background:linear-gradient(180deg,#1D3768,#102044); border:3px solid var(--gold); border-radius:4px;
  outline:1px solid var(--gold-lt); outline-offset:4px; box-shadow:0 12px 28px rgba(20,15,5,.45);}
.plaque .latin{font-family:'Cinzel',serif; font-weight:700; letter-spacing:.42em; font-size:.78rem; color:var(--gold-lt); padding-left:.42em;}
.plaque .ptitle{display:block; margin:.25rem 0 0; padding:0; font-weight:900; font-size:3.1rem; letter-spacing:-.02em; line-height:1.2;
  background:var(--gilt); -webkit-background-clip:text; background-clip:text; color:transparent;}
.plaque p{margin:.5rem 0 0; color:#E8E2CC; font-size:1rem; line-height:1.7;}
.plaque.slim{margin-top:-34px; padding:.6rem 1.4rem .8rem; width:min(760px,92%);}
.plaque.slim p{font-size:.92rem; margin:.35rem 0 0; line-height:1.65;}
.plaque.slim p b{color:var(--gold-lt);}
.plaque.slim .ptitle{font-size:1.65rem; margin:0;}
.plaque.slim .latin{font-size:.66rem;}

/* ── 계단형 진행 표시 (버튼) ───────────────────────── */
.st-key-stairs{margin-top:1.4rem;}
.st-key-stairs [data-testid="stHorizontalBlock"]{align-items:flex-end; gap:.35rem;}
[class*="st-key-stair_"] button{width:100%; justify-content:flex-start; align-items:flex-start; text-align:left;
  border-radius:3px 3px 0 0; padding:.7rem .9rem; font-weight:700; font-size:.98rem; transition:none;}
[class*="st-key-stair_0_"] button{height:58px;}
[class*="st-key-stair_1_"] button{height:78px;}
[class*="st-key-stair_2_"] button{height:98px;}
[class*="st-key-stair_3_"] button{height:118px;}
[class*="_done"] button{background:linear-gradient(180deg,#E8DDBE,#D6C9A2); border:1px solid var(--stone-dk); color:var(--lapis-deep);
  box-shadow:inset 0 3px 0 var(--gold);}
[class*="_active"] button{background:linear-gradient(180deg,#2B4D90,#1B3463); border:1px solid var(--lapis-deep); color:#F7E7B0;
  box-shadow:inset 0 4px 0 var(--gold-lt), 0 6px 14px rgba(20,38,75,.35);}
[class*="_locked"] button{background:rgba(255,250,235,.45); border:1px dashed var(--stone-dk); color:#6F6652; opacity:1;}
[class*="_done"] button:hover{background:#DFD1A8; border-color:var(--lapis); color:var(--lapis-deep);}
[class*="stair_"] button p{font-size:.98rem; line-height:1.3; margin:0; text-align:left;}
@media (max-width:760px){
  [class*="st-key-stair_"] button{height:46px !important;}
  .plaque .ptitle{font-size:2.2rem;}
  .plaque, .plaque.slim{margin-top:-16px; width:94%;}
  .frame .cap{position:relative; left:auto; right:auto; bottom:auto; padding:.7rem 1rem; background:var(--lapis-deep);}
}

/* ── 일반 컨트롤 ─────────────────────────────── */
.stTextArea textarea, .stTextInput input{background:var(--parch-hi); border:1.5px solid var(--stone-dk);
  border-radius:3px; font-size:1.05rem; line-height:1.7; color:var(--ink);}
.stTextArea textarea:focus, .stTextInput input:focus{border-color:var(--lapis); box-shadow:0 0 0 1px var(--gold);}
[data-testid="stBaseButton-primary"]{background:linear-gradient(180deg,#2B4D90,#1B3463); border:1px solid var(--lapis-deep); color:#F7E7B0;
  border-radius:3px; font-weight:700; box-shadow:inset 0 3px 0 var(--gold);}
[data-testid="stBaseButton-primary"]:hover{background:var(--lapis-deep); color:#fff; border-color:var(--lapis-deep);}
[data-testid="stBaseButton-primary"] p{color:#F7E7B0 !important;}
[data-testid="stBaseButton-primary"]:hover p{color:#fff !important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#D9CFAE !important;}
[data-testid="stSidebar"] .stButton button p{color:var(--gold-lt) !important;}
.stDownloadButton button{border:1px solid var(--lapis); color:var(--lapis); background:transparent; border-radius:3px;}
[data-testid="stBaseButton-secondary"]:not([class*="stair"] *){border:1px solid var(--stone-dk); color:var(--lapis-deep);
  background:rgba(255,250,235,.7); border-radius:3px;}

/* ── 본문 요소 ─────────────────────────────── */
.blog .view-title{margin-top:0; font-size:1.5rem;}
.blog .h3{font-size:1.1rem; margin-top:1.4rem;}
.view-title{font-weight:900; font-size:1.9rem; color:var(--lapis-deep); margin:1.8rem 0 .2rem; letter-spacing:-.02em; line-height:1.35;}
.view-lead{color:var(--muted); margin:0 0 .6rem; line-height:1.8;}
.h3{font-weight:800; font-size:1.25rem; color:var(--lapis-deep); margin:2.4rem 0 .2rem; letter-spacing:-.01em;}
.h3 + .meander{margin-bottom:.8rem; width:150px;}
.card{background:linear-gradient(180deg,var(--parch-hi),#F3ECD6); border:1px solid #B89440;
  outline:1px solid rgba(184,148,64,.5); outline-offset:-6px; border-radius:3px; padding:1.2rem 1.4rem; height:100%;
  box-shadow:0 2px 8px rgba(70,50,10,.12);}
.card p{margin:.3rem 0; line-height:1.8;}
.notice{background:#F3E6BC; border-left:4px solid var(--gold); padding:.7rem 1rem; margin:.5rem 0; color:#4A3F1C;
  border-radius:0 3px 3px 0; line-height:1.7; font-size:.95rem;}

.layers{display:grid; grid-template-columns:1fr 1fr; gap:0; margin:.8rem 0 0; border-radius:3px; overflow:hidden;
  border:2px solid var(--gold); box-shadow:0 8px 22px rgba(50,35,10,.25);}
.layer-surface{background:linear-gradient(180deg,#E3EDF1,#F4EFDC); padding:1.3rem 1.5rem;}
.layer-root{background:linear-gradient(180deg,#1B3463,#102044); color:#E9ECF3; padding:1.3rem 1.5rem;}
.layer-surface b, .layer-root b{display:block; margin-bottom:.4rem; font-size:.98rem;}
.layer-root b{color:var(--gold-lt);} .layer-surface b{color:var(--lapis);}
.layer-surface p, .layer-root p{margin:0; line-height:1.85;}
.layer-root p{color:#E9ECF3;}
@media (max-width:760px){.layers{grid-template-columns:1fr;}}

.qlist{margin:.2rem 0; padding-left:1.1rem;} .qlist li{margin:.35rem 0; line-height:1.75;}
.grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:1.1rem;}
.robe{border-left:7px solid var(--c); outline:none; }
.robe h4{margin:0 0 .35rem; font-size:1.1rem; font-weight:800; color:var(--c);}
.robe .sub{font-size:.85rem; font-weight:700; color:var(--muted); margin:.7rem 0 .1rem;}
.robe ul{margin:0; padding-left:1.1rem;} .robe li{line-height:1.7; margin:.15rem 0;}
.chip{display:inline-block; background:var(--c); color:#fff; border-radius:999px; padding:.12rem .8rem;
  font-weight:700; font-size:.88rem; line-height:1.6; box-shadow:0 0 0 2px rgba(243,218,143,.7);}
.conflict{display:grid; grid-template-columns:auto 1fr; gap:.4rem 1rem; align-items:center;
  padding:.85rem 0; border-bottom:1px solid var(--stone);}
.conflict:last-child{border-bottom:none;}
.vs{color:var(--gold-dk); font-size:.95rem; margin:0 .35rem; font-weight:900;}
.kind{font-size:.82rem; color:var(--lapis); font-weight:700; border:1px solid var(--lapis); border-radius:3px; padding:0 .45rem; margin-left:.5rem;}
.srclist{font-size:.92rem; line-height:1.8; margin:.3rem 0; padding-left:1.1rem;}
.srclist a{color:var(--lapis);}

/* ── 벽감(사례 카드) ───────────────────────────── */
.niche{background:linear-gradient(180deg,var(--parch-hi),#F1E9D2); border:3px solid #B89440;
  border-radius:999px 999px 4px 4px; overflow:hidden; box-shadow:0 12px 26px rgba(50,35,10,.3), 0 0 0 1px #6F5316;}
.niche-arch{border-bottom:6px solid var(--gold); box-shadow:inset 0 0 0 3px rgba(60,40,5,.55), inset 0 -40px 40px -30px rgba(20,38,75,.4);}
.niche-name{background:linear-gradient(180deg,#1D3768,#102044); color:var(--gold-lt); text-align:center; padding:.45rem .5rem;
  font-family:'Cinzel',serif; font-weight:700; letter-spacing:.14em; font-size:.8rem; border-bottom:2px solid var(--gold);}
.niche-body{padding:1rem 1.2rem 1.3rem;}
.niche-era{font-size:.85rem; color:var(--muted); margin:0;}
.niche-body h3{font-size:1.2rem; font-weight:800; color:var(--lapis-deep); margin:.15rem 0 .5rem; line-height:1.4;}
.niche-body p{font-size:.96rem; margin:.4rem 0; line-height:1.75;}
.phil{background:linear-gradient(180deg,var(--sky-pale),#E9EEEB); border-left:4px solid var(--lapis); padding:.6rem .8rem; margin:.8rem 0; border-radius:0 3px 3px 0;}
.phil .name{font-weight:800; color:var(--lapis-deep); font-size:1.05rem;}
.phil .latin{font-family:'Cinzel',serif; font-size:.78rem; letter-spacing:.06em; color:var(--muted); margin-left:.4rem;}
.phil .theory{font-size:.92rem; color:var(--ink); margin-top:.15rem; line-height:1.6;}
.keyq{font-weight:700; color:var(--lapis); border-top:1px solid var(--stone-dk); padding-top:.7rem; margin-top:.8rem; line-height:1.65;}
.paper{padding:.55rem 0; border-bottom:1px solid var(--stone); font-size:.92rem; line-height:1.6;}
.paper:last-child{border-bottom:none;}
.paper a{color:var(--lapis); font-weight:700; text-decoration:none;} .paper a:hover{text-decoration:underline;}
.paper .meta{color:var(--muted); font-size:.85rem;}
.paper .abs{color:#3A3326; font-size:.88rem; margin-top:.15rem;}
.badge{font-size:.75rem; background:var(--stone); color:var(--lapis-deep); padding:0 .4rem; border-radius:2px; margin-left:.35rem;}

/* ── 솔루션 ───────────────────────────────── */
.verdict{position:relative; background:linear-gradient(180deg,#1D3768,#102044); color:#F5F3ED; padding:1.9rem 2rem 1.7rem; border-radius:3px;
  border:3px solid var(--gold); outline:1px solid var(--gold-lt); outline-offset:4px; margin:1.4rem 0 1rem;
  box-shadow:0 12px 28px rgba(20,15,5,.4);}
.verdict .by{color:var(--gold-lt); font-size:.92rem; margin:0 0 .5rem; font-weight:700;}
.verdict h2{font-size:1.75rem; font-weight:900; margin:0; padding:0; line-height:1.5; letter-spacing:-.02em;
  background:linear-gradient(180deg,#FFF4CC,#F3DA8F); -webkit-background-clip:text; background-clip:text; color:transparent;}
.principles{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem; margin:.8rem 0;}
.principle{border-top:4px solid var(--gold); background:linear-gradient(180deg,var(--parch-hi),#F3ECD6); padding:.9rem 1.1rem; line-height:1.7; font-weight:700;
  box-shadow:0 2px 8px rgba(70,50,10,.12); outline:1px solid rgba(184,148,64,.45); outline-offset:-5px;}
.action-first{margin-top:.8rem; padding:.55rem .75rem; background:#fff; border-left:4px solid var(--c); font-weight:600; line-height:1.65; font-size:.94rem;}
.action-first span{color:var(--c); font-weight:800; margin-right:.4rem;}
.steps{display:grid; grid-template-columns:repeat(3,1fr); gap:.6rem; align-items:end;}
.step{background:linear-gradient(180deg,var(--parch-hi),#F3ECD6); border:1px solid #B89440; border-top:6px solid var(--lapis); padding:.9rem 1rem;}
.step:nth-child(1){margin-bottom:0;} .step:nth-child(2){margin-bottom:1.2rem; border-top-color:#3B5FA0;} .step:nth-child(3){margin-bottom:2.4rem; border-top-color:var(--gold);}
.step b{display:block; color:var(--lapis-deep); margin-bottom:.35rem;}
.step ul{margin:0; padding-left:1.05rem;} .step li{line-height:1.7; margin:.2rem 0;}
@media (max-width:760px){.steps{grid-template-columns:1fr;} .step{margin-bottom:0 !important;}}
.pair{display:grid; grid-template-columns:1fr 1fr; gap:1.4rem; padding:.8rem 0; border-bottom:1px solid var(--stone);}
.pair:last-child{border-bottom:none;} .pair small{display:block; color:var(--muted); font-weight:700; margin-bottom:.15rem;}
@media (max-width:760px){.pair{grid-template-columns:1fr; gap:.4rem;}}
.res{display:flex; gap:.8rem; padding:.55rem 0; border-bottom:1px solid var(--stone); line-height:1.7;}
.res:last-child{border-bottom:none;} .res b{min-width:3.4rem; color:var(--lapis);}

/* ── 확산 콘텐츠 ──────────────────────────── */
.tweet{background:linear-gradient(180deg,var(--parch-hi),#F3ECD6); border:1px solid #B89440; border-radius:10px; padding:.8rem 1rem; margin:.5rem 0 .5rem 1rem;
  position:relative; line-height:1.75;}
.tweet::before{content:""; position:absolute; left:-.6rem; top:-.5rem; bottom:-.5rem; width:2px; background:var(--gold);}
.tweet .cnt{display:block; text-align:right; font-size:.8rem; color:var(--muted); margin-top:.25rem;}
.tweet .cnt.over{color:#A8475E; font-weight:700;}
.cards{display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:.9rem;}
.cardnews{aspect-ratio:1/1; background:linear-gradient(180deg,#1D3768,#102044); color:#F5F3ED; padding:1.1rem; display:flex; flex-direction:column;
  justify-content:space-between; border:2px solid var(--gold); outline:1px solid var(--gold-lt); outline-offset:-7px;}
.cardnews:nth-child(even){background:linear-gradient(180deg,var(--parch-hi),#F1E9D2); color:var(--ink); border:2px solid #B89440; outline-color:rgba(184,148,64,.6);}
.cardnews h5{font-size:1.15rem; font-weight:800; margin:0; line-height:1.4;}
.cardnews p{margin:.3rem 0 0; font-size:.88rem; line-height:1.6;}
.cardnews .vis{font-size:.78rem; opacity:.85; border-top:1px dashed currentColor; padding-top:.45rem; line-height:1.5;}
"""
)


# ───────────────────────── 머리글·배너 HTML ─────────────────────────
def hero_html() -> str:
    """첫 화면: 금박 액자에 담은 프레스코 전경 + 비문 명판."""
    return (
        '<div class="hero"><div class="meander"></div>'
        '<div class="frame"><div class="crop crop-hero" role="img" '
        'aria-label="라파엘로의 아테네 학당. 아치 회랑 한가운데에서 플라톤은 하늘을, 아리스토텔레스는 땅을 가리킨다"></div></div>'
        '<div class="plaque"><div class="latin">CAUSARUM COGNITIO</div><div class="ptitle" role="heading" aria-level="1">갈등분쇄기</div>'
        "<p>역사와 철학의 눈으로 갈등의 뿌리를 묻고,<br/>각자의 자리에서 할 수 있는 해법을 찾습니다.</p></div></div>"
    )


def banner_html(view: str) -> str:
    """다음 화면들: 그림의 부분 확대 배너 + 인물 설명이 담긴 명판."""
    key = view if view in BANNER_CAPTIONS else "issue"
    who, line = BANNER_CAPTIONS[key]
    return (
        '<div class="hero"><div class="meander"></div>'
        f'<div class="frame"><div class="crop crop-{key}" role="img" aria-label="{who}"></div></div>'
        '<div class="plaque slim"><div class="latin">CAUSARUM COGNITIO</div><div class="ptitle" role="heading" aria-level="1">갈등분쇄기</div>'
        f'<p><b>{who}</b> · {line}</p></div></div>'
    )


def niche_art_html(key: str, label: str) -> str:
    """벽감의 윗부분: 원작에서 오려 낸 인물(또는 석상)과 이름 띠."""
    return (
        f'<div class="crop crop-{key} niche-arch" role="img" aria-label="{label}"></div>'
        f'<div class="niche-name">{label}</div>'
    )
