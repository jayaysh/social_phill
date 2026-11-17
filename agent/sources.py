"""외부 데이터 수집: 뉴스 기사 본문, 학술 논문(Semantic Scholar · OpenAlex · arXiv).

- 학술 검색은 모두 키 없이 쓸 수 있는 공개 API 이며, 한 곳이 실패해도 나머지로 계속 진행한다.
- KCI·RISS 는 공개 검색 API 가 없어 직접 연동하지 않았다. OpenAlex 가 국내 학술지 일부를 색인한다.
"""
from __future__ import annotations

import ipaddress
import os
import re
import socket
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "gyeoldeung-bunsoegi/0.1 (educational research agent)"
TIMEOUT = 8
_ALLOWED_PORTS = {None, 80, 443}  # 내부 서비스가 흔히 쓰는 임의 포트는 막는다
MAX_ARTICLE_CHARS = 40_000
MAX_DOWNLOAD_BYTES = 3_000_000


# ───────────────────────── 기사 URL → 본문 ─────────────────────────
@dataclass
class Article:
    url: str
    title: str
    text: str
    truncated: bool = False


class FetchError(Exception):
    pass


def is_url(text: str) -> bool:
    return bool(re.match(r"^https?://\S+$", text.strip()))


def _is_blocked(ip: ipaddress._BaseAddress) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:  # ::ffff:127.0.0.1 같은 우회 표기
        ip = ip.ipv4_mapped
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified


def _assert_public(url: str) -> None:
    """서버가 내부망을 대신 호출하지 않도록 사설·루프백 주소를 거부한다 (SSRF 방지)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("http(s) 주소만 읽을 수 있습니다.")
    try:
        port = parsed.port
    except ValueError as e:
        raise FetchError("주소의 포트가 올바르지 않습니다.") from e
    if port not in _ALLOWED_PORTS:
        raise FetchError("80·443 이외의 포트는 읽을 수 없습니다.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, port or 443)
    except socket.gaierror as e:
        raise FetchError("주소를 찾을 수 없습니다.") from e
    for info in infos:
        if _is_blocked(ipaddress.ip_address(info[4][0])):
            raise FetchError("내부망 주소는 읽을 수 없습니다.")


def _assert_peer_public(resp: requests.Response) -> None:
    """실제로 연결된 서버 주소를 다시 검사한다.

    _assert_public 과 요청 사이에 DNS 가 내부 주소로 바뀌는 재바인딩 공격을 막는다.
    urllib3 내부 속성에 기대므로 읽지 못하면 검사를 건너뛴다(앞선 검사는 이미 통과한 상태).
    """
    try:
        peer = ipaddress.ip_address(resp.raw._connection.sock.getpeername()[0])  # type: ignore[union-attr]
    except Exception:
        return
    if _is_blocked(peer):
        resp.close()
        raise FetchError("내부망 주소는 읽을 수 없습니다.")


def fetch_article(url: str) -> Article:
    url = url.strip()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; " + UA + ")", "Accept-Language": "ko,en;q=0.8"}
    resp = None
    try:
        for _ in range(4):  # 리다이렉트는 직접 따라가며 매번 검사
            _assert_public(url)
            resp = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=False)
            _assert_peer_public(resp)
            if resp.is_redirect and resp.headers.get("location"):
                url = urljoin(url, resp.headers["location"])
                continue
            break
        else:
            raise FetchError("리다이렉트가 너무 많습니다.")
        resp.raise_for_status()
        raw = resp.raw.read(MAX_DOWNLOAD_BYTES, decode_content=True)
    except requests.RequestException as e:
        raise FetchError(f"기사를 불러오지 못했습니다 ({e.__class__.__name__}).") from e

    encoding = resp.encoding if resp.encoding and resp.encoding.lower() != "iso-8859-1" else None
    soup = BeautifulSoup(raw, "lxml", from_encoding=encoding)

    title = ""
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = og["content"].strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()

    for tag in soup(["script", "style", "nav", "footer", "aside", "header", "form", "noscript", "iframe"]):
        tag.decompose()
    root = soup.find("article") or soup.find(attrs={"id": re.compile(r"(article|content|news)", re.I)}) or soup.body or soup
    paragraphs = [p.get_text(" ", strip=True) for p in root.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) > 30]
    if not paragraphs:  # <p> 를 쓰지 않는 사이트 대비
        paragraphs = [t for t in root.get_text("\n", strip=True).split("\n") if len(t) > 30]
    text = "\n\n".join(paragraphs).strip()
    if len(text) < 200:
        raise FetchError("기사 본문을 추출하지 못했습니다. 본문을 직접 붙여넣어 주세요.")

    truncated = len(text) > MAX_ARTICLE_CHARS
    return Article(url=url, title=title, text=text[:MAX_ARTICLE_CHARS], truncated=truncated)


# ───────────────────────── 학술 논문 검색 ─────────────────────────
@dataclass
class Paper:
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    url: str = ""
    abstract: str = ""
    source: str = ""
    citations: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _clip(text: str | None, n: int = 600) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


_s2_blocked_until = 0.0  # 키 없이 429 를 받으면 몇 분간 호출하지 않는다(매 검색어마다 429 를 맞는 낭비 방지)


def search_semantic_scholar(query: str, limit: int = 4) -> list[Paper]:
    global _s2_blocked_until
    headers = {"User-Agent": UA}
    has_key = bool(os.environ.get("S2_API_KEY"))
    if has_key:
        headers["x-api-key"] = os.environ["S2_API_KEY"]
    elif time.time() < _s2_blocked_until:
        return []
    r = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "limit": limit,
            "fields": "title,year,authors,venue,abstract,url,citationCount",
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    if r.status_code == 429 and not has_key:
        _s2_blocked_until = time.time() + 600
    r.raise_for_status()  # 429 는 호출부(_safe)에서 조용히 건너뜀
    out = []
    for p in r.json().get("data", []):
        out.append(
            Paper(
                title=p.get("title") or "",
                authors=[a.get("name", "") for a in p.get("authors", [])][:4],
                year=p.get("year"),
                venue=p.get("venue") or "",
                url=p.get("url") or "",
                abstract=_clip(p.get("abstract")),
                source="Semantic Scholar",
                citations=p.get("citationCount"),
            )
        )
    return out


def _openalex_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos: dict[int, str] = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def search_openalex(query: str, limit: int = 4) -> list[Paper]:
    r = requests.get(
        "https://api.openalex.org/works",
        params={
            "search": query,
            "per-page": limit,
            "select": "id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,cited_by_count",
        },
        headers={"User-Agent": UA},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        loc = w.get("primary_location") or {}
        src = (loc.get("source") or {}).get("display_name") or ""
        out.append(
            Paper(
                title=w.get("title") or "",
                authors=[(a.get("author") or {}).get("display_name", "") for a in w.get("authorships", [])][:4],
                year=w.get("publication_year"),
                venue=src,
                url=w.get("doi") or w.get("id") or "",
                abstract=_clip(_openalex_abstract(w.get("abstract_inverted_index"))),
                source="OpenAlex",
                citations=w.get("cited_by_count"),
            )
        )
    return out


def search_arxiv(query: str, limit: int = 3) -> list[Paper]:
    r = requests.get(
        "https://export.arxiv.org/api/query",
        params={"search_query": f'all:"{query}"', "start": 0, "max_results": limit},
        headers={"User-Agent": UA},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in ET.fromstring(r.text).findall("a:entry", ns):
        published = (e.findtext("a:published", default="", namespaces=ns) or "")[:4]
        out.append(
            Paper(
                title=_clip(e.findtext("a:title", default="", namespaces=ns), 300),
                authors=[a.findtext("a:name", default="", namespaces=ns) for a in e.findall("a:author", ns)][:4],
                year=int(published) if published.isdigit() else None,
                venue="arXiv",
                url=e.findtext("a:id", default="", namespaces=ns) or "",
                abstract=_clip(e.findtext("a:summary", default="", namespaces=ns)),
                source="arXiv",
            )
        )
    return out


_BACKENDS = (search_semantic_scholar, search_openalex, search_arxiv)


def _safe(fn, query: str) -> list[Paper]:
    try:
        return fn(query)
    except Exception:  # 네트워크·한도 오류는 해당 소스만 건너뛴다
        return []


def search_papers(queries: list[str], max_total: int = 6) -> list[Paper]:
    """여러 검색어 × 여러 DB 를 병렬 조회하고, 중복을 제거해 소스가 고루 섞이게 돌려준다."""
    queries = [q.strip() for q in queries if q and q.strip()][:4]
    if not queries:
        return []
    jobs = [(fn, q) for q in queries for fn in _BACKENDS]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda j: _safe(*j), jobs))

    # 소스별로 묶은 뒤 라운드로빈으로 섞는다
    by_source: dict[str, list[Paper]] = {}
    for papers in results:
        for p in papers:
            by_source.setdefault(p.source, []).append(p)

    seen: set[str] = set()
    merged: list[Paper] = []
    queues = [list(v) for v in by_source.values()]
    while queues and len(merged) < max_total:
        for q in list(queues):
            if not q:
                queues.remove(q)
                continue
            p = q.pop(0)
            key = re.sub(r"\W+", "", p.title.lower())
            if not p.title or key in seen or not p.abstract:
                continue
            seen.add(key)
            merged.append(p)
            if len(merged) >= max_total:
                break
    return merged
