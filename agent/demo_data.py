"""데모 모드용 예시 데이터.

API 키 없이 화면 전체 흐름을 체험하고 UI 를 검증하기 위한 고정 결과다.
'국민연금 개혁과 세대 갈등'을 주제로 한 한 가지 시나리오만 담고 있으며, 입력과 무관하게 같은 결과가 나온다.
참고 문헌은 실제 존재하는 고전 저작만 넣었고, 최신 논문 검색 결과는 포함하지 않는다.
"""
from __future__ import annotations

from .pipeline import CasesResult, IssueResult
from .schemas import (
    Blog,
    BlogSection,
    Card,
    CardNews,
    Conflict,
    ContentPack,
    HistoricalCase,
    IssueStructure,
    LayerAction,
    Limitation,
    Phase,
    Resource,
    SolutionReport,
    Stakeholder,
    XThread,
)
from .sources import Paper

DEMO_QUERY = "국민연금 개혁 세대 갈등"

_L_YOUNG = "청년층(20~30대)"
_L_MID = "중장년층(40~50대)"
_L_OLD = "은퇴·고령층"
_L_SELF = "자영업자·플랫폼 노동자"
_L_GOV = "정부·정치권"


def demo_issue() -> IssueResult:
    issue = IssueStructure(
        title="국민연금 개혁을 둘러싼 세대 갈등",
        summary=(
            "저출생과 고령화로 국민연금의 장기 재정 전망이 나빠지면서 보험료율, 소득대체율, 수급 개시 연령을 어떻게 조정할지가 쟁점이 되었다. "
            "세대마다 내는 시점과 받는 시점이 달라 같은 제도를 두고 서로 다른 손익을 계산한다. "
            "개혁안이 나올 때마다 '누가 더 내고 누가 덜 받는가'가 논쟁의 중심이 되고, 제도 자체에 대한 신뢰는 더 낮아진다."
        ),
        surface_phenomenon=(
            "온라인에서는 '내는 돈만 늘고 나는 못 받는다'는 청년의 불만과 '평생 낸 돈을 깎지 말라'는 고령층의 반발이 맞선다. "
            "개혁안은 숫자 싸움으로 소비되고 세대 간 비난으로 번진다."
        ),
        root_cause=(
            "갈등의 뿌리는 숫자보다 신뢰와 설계에 있다. 제도가 '세대 간 약속'이라는 점이 설명되지 않은 채 손익 계산만 남았고, "
            "부담 조정을 결정하는 자리에 가장 오래 부담할 청년이 거의 없다. 그 결과 개혁은 한 세대의 양보로 읽히고, 양보는 곧 불신이 된다."
        ),
        core_questions=[
            "세대 간 약속은 어디까지 지켜져야 하며, 누가 그 조정을 결정할 자격이 있는가?",
            "부담의 형평은 '낸 만큼 받는 것'인가, '버틸 수 있는 만큼 내는 것'인가?",
            "지금 세대가 합의해도 아직 태어나지 않은 세대의 몫은 누가 대변하는가?",
        ],
        stakeholders=[
            Stakeholder(
                layer=_L_YOUNG,
                role="앞으로 가장 오래 보험료를 내지만 개혁 논의에서 발언권은 가장 약한 세대.",
                interests=["내는 만큼 받을 수 있다는 예측 가능성", "개혁 결정 과정에서의 대표성"],
                fears=["보험료만 오르고 수급은 불확실해지는 것", "기금 고갈의 책임을 떠안는 것"],
            ),
            Stakeholder(
                layer=_L_MID,
                role="부모 부양과 자녀 양육, 자신의 노후 준비를 동시에 지는 세대.",
                interests=["노후 소득의 안정", "보험료 인상 속도의 완급"],
                fears=["수급 직전에 규칙이 바뀌는 것", "부모와 자녀 양쪽의 부담이 겹치는 것"],
            ),
            Stakeholder(
                layer=_L_OLD,
                role="이미 낸 보험료를 근거로 연금을 받고 있거나 곧 받을 세대. 소득의 상당 부분을 연금에 의존한다.",
                interests=["약속된 급여의 보장", "물가를 따라가는 급여 수준"],
                fears=["급여 삭감", "'부담스러운 세대'로 낙인찍히는 것"],
            ),
            Stakeholder(
                layer=_L_SELF,
                role="소득이 불규칙해 보험료 부담과 가입 이력의 단절을 함께 겪는 비정규·독립 노동자.",
                interests=["소득 변동을 반영한 보험료 체계", "가입 공백이 노후 빈곤으로 이어지지 않는 장치"],
                fears=["보험료를 내고도 최소 수급 기간을 못 채우는 것", "지역가입자 부담 가중"],
            ),
            Stakeholder(
                layer=_L_GOV,
                role="제도 설계와 입법의 책임자이면서 선거 주기에 묶인 행위자.",
                interests=["재정 지속 가능성", "사회적 합의의 정당성"],
                fears=["개혁안이 곧 표 잃는 일이 되는 것", "어느 세대에게든 '배신자'로 찍히는 것"],
            ),
        ],
        conflicts=[
            Conflict(parties=[_L_YOUNG, _L_OLD], kind="이익 갈등", description="보험료 인상과 급여 조정의 몫을 서로 상대에게 돌리려 한다."),
            Conflict(parties=[_L_YOUNG, _L_GOV], kind="사실·정보 갈등", description="재정 전망과 개혁안의 효과를 두고 믿을 수 있는 수치가 없다고 느낀다."),
            Conflict(parties=[_L_MID, _L_YOUNG], kind="구조적 갈등", description="낀 세대가 위아래 요구를 동시에 받으며 개혁 속도를 두고 부딪힌다."),
            Conflict(parties=[_L_SELF, _L_GOV], kind="구조적 갈등", description="소득 파악과 보험료 부과 방식이 불규칙 노동의 현실과 맞지 않는다."),
        ],
        public_perception=(
            "(데모 데이터) 온라인 담론에서는 '세대 전쟁' 프레임이 가장 자주 쓰이지만, 설명 영상과 칼럼에는 '세대가 아니라 설계의 문제'라는 목소리도 늘고 있다. "
            "정서의 결은 청년층의 불안과 냉소, 고령층의 억울함과 방어감으로 나뉜다."
        ),
        scholar_keywords_en=["intergenerational justice pension reform", "social contract generations welfare state", "deliberative democracy pension"],
        scholar_keywords_ko=["국민연금 세대 간 형평성", "연금개혁 사회적 합의", "세대 간 정의"],
    )
    return IssueResult(
        issue=issue,
        notices=["데모 모드입니다. 입력과 상관없이 예시 시나리오가 표시되며 실제 웹 검색은 하지 않았습니다."],
    )


def demo_cases() -> CasesResult:
    cases = [
        HistoricalCase(
            id="A",
            title="솔론의 부채 탕감 개혁",
            era_place="기원전 594년경, 아테네",
            summary=(
                "소수 지주에게 빚진 농민이 노예로 팔려 나가며 아테네 내부의 긴장이 한계에 이르렀다. "
                "조정자로 선출된 솔론은 부채를 탕감하고 채무 노예를 금지하는 한편 시민을 재산 등급으로 나누어 정치 참여의 길을 열었다. "
                "그는 부자와 빈자 어느 쪽의 전면 승리도 허락하지 않는 균형을 설계했다."
            ),
            parallels=[
                "세대 간 부담이 한쪽으로 쌓여 공동체의 신뢰가 흔들렸다는 점",
                "한 집단의 승리가 아니라 모두가 받아들일 규칙을 새로 짜야 했다는 점",
            ],
            differences="솔론의 개혁은 채무 탕감이라는 일회성 조치였지만 연금은 수십 년에 걸친 지속적 약속이다.",
            outcome="두 진영 모두에게 불만을 샀지만 당장의 내전을 막았다. 다만 장기적 안정은 이후 개혁이 이어받아야 했다.",
            philosopher="아리스토텔레스",
            philosopher_latin="Aristotle",
            work="『정치학』",
            theory="중용과 혼합정체",
            lens=(
                "아리스토텔레스는 극단적인 부자와 극단적인 빈자 사이에서 중간 계층이 두터울 때 국가가 안정된다고 보았다. "
                "연금 갈등에서는 어느 세대의 이익도 극단으로 가지 않도록 부담과 보장의 균형점을 설계하는 일이 핵심이 된다. "
                "솔론의 사례는 그 균형이 한 번에 만족을 주지 못해도 갈등의 폭발을 막는다는 점을 보여 준다."
            ),
            key_question="어느 세대도 '전부 잃거나 전부 얻지' 않는 균형점은 어디인가?",
            queries_en=["Aristotle Politics middle class stability", "Solon reforms debt Athens"],
            queries_ko=["솔론 개혁 아리스토텔레스 정치학"],
        ),
        HistoricalCase(
            id="B",
            title="1983년 미국 사회보장 개혁과 그린스펀 위원회",
            era_place="1983년, 미국",
            summary=(
                "사회보장 기금이 급여 지급에 차질을 빚을 위기에 놓이자 양당과 이해단체의 인사가 참여하는 초당적 위원회가 꾸려졌다. "
                "위원회는 비공개 협상으로 급여세율 인상, 수급 연령의 단계적 상향, 급여 인상 시기 조정을 한 묶음으로 합의했고 의회가 이를 통과시켰다. "
                "고통을 나누는 방식을 한꺼번에 협상한 점이 특징이다."
            ),
            parallels=[
                "제도의 지속 가능성을 두고 세대·계층별 손익이 정면으로 부딪혔다는 점",
                "어느 정당도 혼자서는 감당하기 어려운 부담 조정을 공동 책임으로 풀었다는 점",
            ],
            differences="당시 미국은 급여와 부담을 소규모로 조정할 여지가 컸고, 한국의 저출생 구조는 훨씬 가파르다.",
            outcome="단기 재정 위기를 넘겼고 '초당적 합의'의 모델로 자주 인용된다. 장기 쟁점은 이후로 미뤄졌다.",
            philosopher="존 롤스",
            philosopher_latin="John Rawls",
            work="『정의론』(1971)",
            theory="무지의 베일과 세대 간 정의(정당한 저축 원칙)",
            lens=(
                "롤스는 자신이 어느 세대에 속할지 모르는 상태에서 합의할 수 있는 원칙이 정의롭다고 보았다. "
                "연금 규칙을 '내가 몇 년생인지 모른다'는 가정 아래 다시 세우면 어느 세대에게도 일방적이지 않은 설계가 드러난다. "
                "또한 세대 간 정의는 지금 세대가 다음 세대에게 공정한 몫을 남길 의무를 포함한다고 본다."
            ),
            key_question="내가 몇 년생으로 태어날지 모른다면 어떤 연금 규칙에 동의하겠는가?",
            queries_en=["Rawls justice between generations just savings", "1983 Social Security reform Greenspan Commission"],
            queries_ko=["롤스 세대 간 정의 연금"],
        ),
        HistoricalCase(
            id="C",
            title="로마 평민의 성산 철수와 호민관 제도",
            era_place="기원전 494년경, 로마",
            summary=(
                "채무와 병역의 부담이 평민에게 집중되자 평민들이 도시를 떠나 성산에 집결하는 집단 철수를 감행했다. "
                "원로원은 평민이 직접 선출하는 호민관을 두는 데 합의했고 평민은 돌아왔다. "
                "갈등은 사라지지 않았지만 요구를 제도 안으로 들이는 통로가 생겼다."
            ),
            parallels=[
                "의사결정에서 배제된 집단이 부담만 지고 있다고 느꼈다는 점",
                "갈등의 해소가 아니라 갈등을 표현할 제도적 통로가 해법이 되었다는 점",
            ],
            differences="로마의 평민은 하나의 신분 집단이었지만, 세대는 모두가 거쳐 가는 시기이고 이해관계가 겹친다.",
            outcome="호민관 제도가 이후 수백 년간 갈등을 폭력이 아니라 제도 안의 협상으로 끌어들이는 장치가 되었다.",
            philosopher="니콜로 마키아벨리",
            philosopher_latin="Niccolò Machiavelli",
            work="『로마사 논고』",
            theory="생산적 갈등론",
            lens=(
                "마키아벨리는 로마의 자유가 귀족과 평민의 갈등 덕분에 유지되었다고 보았다. "
                "갈등을 없애려 하기보다 갈등이 폭력이 되지 않도록 제도화하는 것이 핵심이다. "
                "연금 논쟁에서는 청년의 목소리가 협상 테이블에 상시로 올라오는 제도적 자리를 만드는 일이 해법이 된다."
            ),
            key_question="배제된 세대의 요구를 제도 안으로 들일 통로는 무엇인가?",
            queries_en=["Machiavelli Discourses conflict liberty Rome", "Roman plebeian secession tribunes"],
            queries_ko=["마키아벨리 로마사 논고 갈등"],
        ),
    ]
    classics = {
        "A": Paper(
            title="Politics (『정치학』) — 중산층과 혼합정체를 다룬 4권, 솔론의 개혁을 언급한 2권",
            authors=["Aristotle"], year=None, venue="기원전 4세기 저작", url="",
            abstract="국가의 안정이 극단적 부와 가난의 사이에서 두터운 중간 계층에 달려 있다고 논한다.",
            source="고전 문헌",
        ),
        "B": Paper(
            title="A Theory of Justice (『정의론』) — 44절 '세대 간 정의의 문제'",
            authors=["John Rawls"], year=1971, venue="Harvard University Press", url="",
            abstract="무지의 베일 아래의 합의로 정의의 원칙을 도출하고, 세대 사이의 정당한 저축 원칙을 논한다.",
            source="고전 문헌",
        ),
        "C": Paper(
            title="Discorsi sopra la prima Deca di Tito Livio (『로마사 논고』) — 1권 4장",
            authors=["Niccolò Machiavelli"], year=1531, venue="최초 출간", url="",
            abstract="귀족과 평민의 불화가 로마의 자유를 키운 원인이었다는 논지를 편다.",
            source="고전 문헌",
        ),
    }
    return CasesResult(cases=cases, papers={k: [v] for k, v in classics.items()})


def _acts(young, mid, old, selfemp, gov) -> list[LayerAction]:
    names = [_L_YOUNG, _L_MID, _L_OLD, _L_SELF, _L_GOV]
    return [LayerAction(layer=n, actions=list(a[0]), first_step=a[1]) for n, a in zip(names, [young, mid, old, selfemp, gov])]


def demo_solution(case_id: str) -> SolutionReport:
    if case_id == "A":
        return SolutionReport(
            headline="어느 세대도 전부 잃지 않는 균형점을 함께 설계한다",
            logic=(
                "아리스토텔레스의 중용은 두 극단의 산술적 평균이 아니라 공동체가 오래 버틸 수 있는 지점을 찾는 일이다. "
                "연금에서 한쪽 세대의 희생만 요구하면 제도 전체가 불신으로 무너진다. "
                "그래서 보험료, 급여, 수급 개시 연령을 따로 다루지 않고 한 묶음의 균형으로 설계하고, 그 속도를 세대별로 달리해 충격을 나눈다. "
                "솔론이 그러했듯 이 설계는 모두에게 불만을 남기겠지만, 불만의 크기가 서로 비슷하다는 사실이 정당성의 근거가 된다."
            ),
            principles=["부담과 보장은 한 묶음으로 설계한다", "충격은 세대에 걸쳐 완만하게 나눈다", "누가 얼마를 양보했는지 숫자로 공개한다"],
            layer_actions=_acts(
                (["보험료율 인상 속도를 단계화하는 안에 찬성하는 대신 소득대체율 하한의 명문화를 요구한다", "또래 모임·학교에서 연금 구조를 설명하는 스터디를 연다"], "내 연금 예상 수령액을 국민연금 공단 조회 서비스로 확인한다."),
                (["부모 부양 부담을 연금 설계 논의의 의제로 올리는 의견서를 낸다", "수급 시점이 가까운 세대로서 단계적 조정안의 속도에 의견을 낸다"], "가족과 노후 소득 계획을 함께 점검하는 대화를 한 번 한다."),
                (["현재 수급자의 급여는 보장하되 물가 연동 방식 조정에는 열린 태도를 갖는다", "경험 많은 은퇴자가 청년 설명회에 참여해 제도의 역사를 증언한다"], "지역 노인정이나 모임에서 '세대 간 약속'을 주제로 대화를 연다."),
                (["소득 변동에 연동되는 보험료 체계를 협동조합·노조 단위로 정리해 제안한다", "가입 공백 기간의 보완 방안을 공동으로 요구한다"], "자신의 가입 이력과 공백 기간을 확인한다."),
                (["개혁안을 하나의 묶음으로 제시하되 세대별 손익표를 공개한다", "개혁 후 5년마다 자동 재점검하는 규정을 법에 넣는다"], "개혁안의 세대별 손익 계산 방법을 먼저 공개한다."),
            ),
            roadmap=[
                Phase(horizon="단기 (3개월 이내)", goals=["세대별 손익표 공개 형식 합의", "쟁점별 대표 의견 수렴 창구 개설"]),
                Phase(horizon="중기 (1년 이내)", goals=["보험료·급여·연령 조정을 묶음으로 담은 개혁안 확정", "불규칙 노동자 가입 공백 보완책 시범 실시"]),
                Phase(horizon="장기 (1년 이후)", goals=["5년 단위 자동 재점검 체계 가동", "세대별 부담 지표의 정례 공개"]),
            ],
            limitations=[
                Limitation(point="균형점이 어디인지는 숫자로 쉽게 합의되지 않고, 세대마다 균형을 다르게 정의한다.", mitigation="균형의 정의를 먼저 합의하고 계산은 독립 기관이 맡는다."),
                Limitation(point="모두에게 불만을 남기는 설계는 정치적으로 선택되기 어렵다.", mitigation="불만의 크기를 비교한 표를 공개해 설계의 정당성을 보여 준다."),
            ],
            resources=[
                Resource(kind="제도", detail="자동 재점검 조항과 세대별 손익 공개를 규정할 법적 근거"),
                Resource(kind="데이터", detail="세대별 납부·수급 전망을 계산하는 독립 추계 기구"),
                Resource(kind="신뢰", detail="정치권이 개혁안을 정쟁에 쓰지 않겠다는 사전 약속"),
            ],
            indicators=["개혁안에 대한 세대별 찬성도의 격차가 줄어드는가", "제도 신뢰도 조사에서 청년층 수치가 상승하는가"],
            evidence_note="",
        )
    if case_id == "B":
        return SolutionReport(
            headline="내가 몇 년생인지 모른다는 가정에서 규칙을 다시 쓴다",
            logic=(
                "롤스의 무지의 베일은 자신의 출생 연도를 모르는 상태에서 연금 규칙을 정하게 만든다. "
                "이 가정에서는 누구도 자기 세대에게만 유리한 규칙을 고집할 이유가 없다. "
                "1983년 미국의 개혁은 당파를 넘어 공동 책임으로 합의했다는 점에서 이 정신과 닿아 있다. "
                "따라서 해법의 핵심은 숫자보다 절차이며, 세대 대표를 포함한 공개 숙의 절차에서 나온 규칙이야말로 정당하다고 본다."
            ),
            principles=["규칙은 출생 연도를 가린 상태에서 정당화된다", "합의 절차는 공개되고 모든 세대가 대표된다", "다음 세대에 남길 몫을 먼저 정한다"],
            layer_actions=_acts(
                (["시민 숙의단의 청년 몫 참여에 지원한다", "세대별 손익 분석을 또래와 함께 읽고 의견서를 만든다"], "공론화 위원회 참여 신청 공고를 확인한다."),
                (["가족 안에서 '무지의 베일' 대화를 해 본다: 내가 다른 연도에 태어났다면 어떤 규칙이 공정한가", "직장·지역 숙의 토론회에 참여한다"], "가족 식사 자리에서 위 질문을 던진다."),
                (["숙의 과정에서 수급자의 정당한 기대 보호 범위를 스스로 정리해 공유한다", "세대 대표 패널의 자문 역할을 맡는다"], "수급권 보호 원칙에 대한 본인의 입장을 글로 정리한다."),
                (["불규칙 노동자 몫의 대표를 숙의단에 포함하도록 요구한다", "소득 파악 개선안에 대한 실무 의견을 제출한다"], "노동자 단체의 의견서 작성에 참여한다."),
                (["초당적 연금 숙의 기구를 구성하고 협상 시한을 정한다", "숙의 자료와 회의록을 공개한다"], "숙의 기구의 구성 원칙을 먼저 공표한다."),
            ),
            roadmap=[
                Phase(horizon="단기 (3개월 이내)", goals=["세대 대표를 포함한 숙의 기구 구성", "논의 자료의 중립성 검증 절차 마련"]),
                Phase(horizon="중기 (1년 이내)", goals=["숙의 기구의 권고안 공표", "권고안에 대한 국회 심의 일정 확정"]),
                Phase(horizon="장기 (1년 이후)", goals=["권고안 이행 점검 보고", "다음 세대 몫을 정기 평가하는 제도화"]),
            ],
            limitations=[
                Limitation(point="무지의 베일은 사고 실험이어서 현실의 이익 갈등을 직접 해소하지 못한다.", mitigation="숙의 절차에서 사고 실험을 실제 질문지로 바꿔 쓴다."),
                Limitation(point="숙의 기구의 권고는 법적 구속력이 없으면 정치적 반대에 부딪힌다.", mitigation="권고안에 대한 국회 심의를 법에 명시한다."),
            ],
            resources=[
                Resource(kind="시간", detail="숙의에 필요한 충분한 기간과 협상 시한"),
                Resource(kind="인력", detail="중립적인 진행자와 자료 검증 전문가"),
                Resource(kind="신뢰", detail="초당적 참여와 결과 수용에 대한 사전 약속"),
            ],
            indicators=["숙의 참여자의 세대·계층 분포가 모집단을 반영하는가", "권고안이 입법 절차로 이어지는가"],
            evidence_note="",
        )
    return SolutionReport(
        headline="청년의 요구가 상시로 협상 테이블에 오르는 통로를 만든다",
        logic=(
            "마키아벨리는 갈등 자체가 아니라 갈등이 표현될 제도가 없다는 사실이 공동체를 위협한다고 보았다. "
            "로마 평민의 철수는 요구가 제도 밖으로 밀려났을 때 나타나는 극단적 형태였고, 호민관은 그 요구를 제도 안으로 불러들인 장치였다. "
            "연금 갈등에서도 세대의 요구를 정례적으로 반영하는 대표 구조가 있다면 개혁안이 나올 때마다 터지는 폭발은 줄어든다. "
            "그러므로 해법은 한 번의 개혁안이 아니라 갈등을 다루는 상시 구조의 설계가 된다."
        ),
        principles=["갈등을 없애지 않고 제도 안으로 들인다", "배제된 이들에게 상시 대표 자리를 준다", "대표의 의견은 기록되고 답변되어야 한다"],
        layer_actions=_acts(
            (["미래세대 대표 위원 선출·추천 절차에 참여한다", "연금 쟁점에 대한 청년 의견을 정기적으로 모으는 모임을 연다"], "미래세대 대표 후보 추천 공고를 확인한다."),
            (["낀 세대로서의 경험을 정기 의견 수렴에 내어 가교 역할을 한다", "직장 내 연금 학습 모임을 연다"], "직장 동료 두 명과 연금 이야기를 나눈다."),
            (["대표 위원의 질의에 성실히 답하는 자문 모임에 참여한다", "경험담을 기록으로 남겨 청년과 공유한다"], "청년 모임의 질문 하나에 서면으로 답한다."),
            (["불규칙 노동자 대표 몫을 요구하고 의견서를 제출한다", "소득 신고 방식의 개선 아이디어를 모아 전달한다"], "자신의 사례를 익명으로 정리해 대표 위원에게 전달한다."),
            (["미래세대 대표 위원회를 법으로 설치하고 연금 개정안에 의견 제출을 의무화한다", "대표의 의견에 서면으로 답변하는 규정을 만든다"], "위원회 설치 조항을 담은 법안 초안을 공개한다."),
        ),
        roadmap=[
            Phase(horizon="단기 (3개월 이내)", goals=["대표 위원 선출 절차 확정", "의견 제출·답변 규칙 마련"]),
            Phase(horizon="중기 (1년 이내)", goals=["위원회 첫 연례 보고서 발간", "연금 개정안 심의 시 의견 반영 사례 축적"]),
            Phase(horizon="장기 (1년 이후)", goals=["다른 세대 쟁점(주거·기후)으로 모델 확장", "대표성 평가의 정례화"]),
        ],
        limitations=[
            Limitation(point="대표 기구가 형식적인 자문기구로 전락할 위험이 있다.", mitigation="의견 제출과 서면 답변을 법적 의무로 못박는다."),
            Limitation(point="대표 몇 명이 한 세대 전체를 대변할 수는 없다.", mitigation="공개 의견 수렴과 순환 임기로 대표성을 보완한다."),
        ],
        resources=[
            Resource(kind="제도", detail="위원회 설치와 의견 제출·답변 의무를 규정한 법률"),
            Resource(kind="예산", detail="위원회 운영과 독립 사무국을 위한 안정적 재원"),
            Resource(kind="신뢰", detail="의견이 정책에 반영된 사례의 공개적 축적"),
        ],
        indicators=["위원회 의견이 실제 법안 수정으로 이어진 건수", "청년층의 제도 참여 의향이 높아지는가"],
        evidence_note="",
    )


def demo_content(issue: IssueStructure, case: HistoricalCase, report: SolutionReport, formats: list[str]) -> ContentPack:
    """데모 모드: 분석 결과를 템플릿으로 조립한 예시 콘텐츠."""
    pack = ContentPack()
    first_steps = [la.first_step for la in report.layer_actions]
    if "x_thread" in formats:
        pack.x_thread = XThread(
            hook=f"{case.title}에서 {issue.title}의 힌트를 찾아보면 어떨까?",
            posts=[
                f"{issue.surface_phenomenon[:110]}",
                f"{case.era_place}. {case.summary.split('. ')[0][:100]}.",
                f"{case.philosopher}({case.work})의 관점: {case.theory}.",
                f"핵심 질문 하나. {case.key_question}",
                f"해법의 방향: {report.headline}",
                f"청년이라면: {first_steps[0][:100]}",
                f"당신의 자리에서 오늘 할 수 있는 일부터 시작해 보자.",
            ],
            hashtags=["#연금개혁", "#세대갈등", "#인문학"],
        )
    if "blog" in formats:
        pack.blog = Blog(
            title=f"{issue.title}, {case.title}에서 길을 묻다",
            subtitle=f"{case.philosopher}의 '{case.theory}'로 읽는 오늘의 갈등",
            intro=issue.summary,
            sections=[
                BlogSection(heading="뉴스가 보여 주지 않는 뿌리", body=f"{issue.surface_phenomenon}\n\n{issue.root_cause}"),
                BlogSection(heading=f"{case.era_place}의 거울", body=f"{case.summary}\n\n{case.outcome}"),
                BlogSection(heading=f"{case.philosopher}라면 이렇게 묻는다", body=case.lens),
                BlogSection(heading="그래서, 각자의 자리에서", body="\n\n".join(f"{la.layer}: {la.first_step}" for la in report.layer_actions)),
            ],
            closing=f"{report.headline}. 오늘은 위의 첫걸음 중 내 자리에 맞는 하나만 골라 보자.",
        )
    if "card_news" in formats:
        pack.card_news = CardNews(
            cards=[
                Card(headline=issue.title[:20], body="역사와 철학으로 읽는 갈등의 뿌리", visual_idea="아치 안에 제목을 넣은 표지, 하늘색 배경"),
                Card(headline="표면 현상", body=issue.surface_phenomenon[:58], visual_idea="좌우로 대립하는 두 말풍선"),
                Card(headline=case.title[:20], body=case.era_place, visual_idea="고대 석조 아치 일러스트"),
                Card(headline=f"{case.philosopher}의 관점", body=case.theory, visual_idea="흉상 실루엣과 핵심 개념 한 줄"),
                Card(headline="핵심 질문", body=case.key_question[:58], visual_idea="큰 물음표와 짧은 문장"),
                Card(headline="계층별 첫걸음", body=first_steps[0][:58], visual_idea="계층별 아이콘 4개와 한 줄 행동"),
                Card(headline="한계도 있습니다", body=report.limitations[0].point[:58], visual_idea="균열이 간 기둥 일러스트"),
            ],
            caption=f"{report.headline}. 오늘 내 자리에서 할 수 있는 한 걸음은 무엇일까요?",
        )
    return pack
