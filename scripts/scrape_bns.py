"""Bharatiya Nyaya Sanhita 2023 scraper for India Code.

Source: official India Code handle for Act 45 of 2023. The section pages
lazy-load body text from ``/SectionPageContent``; this script scrapes the
index once, then calls that JSON endpoint per section. Output mirrors the
``Act`` / ``Section`` / ``SubItem`` shape used by ``scrape_sso.py``.

Usage::

    python scripts/scrape_bns.py index \\
        --out library/bharatiya_nyaya_sanhita/_raw/index.json

    python scripts/scrape_bns.py section --section 100 \\
        --out library/bharatiya_nyaya_sanhita/_raw/sections/s100.json

    python scripts/scrape_bns.py act \\
        --out library/bharatiya_nyaya_sanhita/_raw/act.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("missing beautifulsoup4: pip install beautifulsoup4 lxml")

BASE = "https://www.indiacode.nic.in"
ACT_ID = "AC_CEN_5_23_00048_2023-45_1719292564123"
HANDLE = "123456789/20062"
STATE_HANDLE = "123456789/1362"
INDEX_URL = f"{BASE}/handle/{HANDLE}"
CONTENT_URL = f"{BASE}/SectionPageContent"
CRAWL_DELAY = 0.25
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class Amendment:
    marker: str
    note: Optional[str] = None


@dataclass
class SubItem:
    kind: str
    label: str
    text: str


@dataclass
class Section:
    number: str
    marginal_note: str
    text: str
    sub_items: list[SubItem] = field(default_factory=list)
    amendments: list[Amendment] = field(default_factory=list)
    anchor_id: Optional[str] = None


@dataclass
class Act:
    act_code: str
    title: str
    url: str
    scraped_at: str
    source: str
    act_id: str
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class HttpClient:
    def __init__(self, delay: float = CRAWL_DELAY):
        self.delay = delay
        self._last = 0.0

    def _throttle(self) -> None:
        gap = time.monotonic() - self._last
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self._last = time.monotonic()

    def fetch(self, url: str, *, timeout: float = 30.0) -> str:
        self._throttle()
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")


_SECTION_RE = re.compile(r"^\s*Section\s+(\d+[A-Z]*)\.\s*(.+)$", re.I)
_SUB_RE = re.compile(r"^\s*\((\d+[A-Z]?)\)\s*")
_ALPHA_RE = re.compile(r"^\s*\(\s*([a-z]+|[ivxlcdm]+|\d+)\s*\)\s*", re.I)
_EXPL_RE = re.compile(r"^\s*Explanation\s*(\d*)\s*\.?\s*[-—]*\s*", re.I)
_EXCEPT_RE = re.compile(r"^\s*Exception\s*(\d*)\s*\.?\s*[-—]*\s*", re.I)
_NOTE_SPLIT_RE = re.compile(r"(?=(?:\d+\.\s+))")


def _txt(el) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _section_url(href: str) -> str:
    return urllib.parse.urljoin(BASE, href)


def parse_index(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "show-data" not in href:
            continue
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        section_no = (qs.get("sectionno") or [""])[0]
        section_id = (qs.get("sectionId") or [""])[0]
        if not section_no or not section_id or section_no in seen:
            continue
        title_text = _txt(a)
        match = _SECTION_RE.match(title_text)
        title = match.group(2).strip() if match else title_text
        seen.add(section_no)
        out.append({
            "section_number": section_no,
            "title": title,
            "section_id": section_id,
            "href": _section_url(href),
        })
    return out


def _split_html_lines(html: str) -> list[str]:
    html = re.sub(r"</br\s*>", "<br/>", html or "", flags=re.I)
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["br", "hr"]):
        tag.replace_with("\n")
    text = soup.get_text("\n", strip=True)
    out: list[str] = []
    for raw in text.splitlines():
        line = _clean_text(raw)
        if not line:
            continue
        if out and line.startswith(("--", "—", "-")):
            out[-1] = f"{out[-1]}{line}"
        else:
            out.append(line)
    return out


def _classify_line(line: str) -> tuple[str, str, str]:
    expl = _EXPL_RE.match(line)
    if expl:
        return "explanation", expl.group(1), line
    exc = _EXCEPT_RE.match(line)
    if exc:
        return "exception", exc.group(1), line
    if line.lower().startswith("illustration"):
        return "illustration", "", line
    if line.lower().startswith("provided that"):
        return "proviso", "", line
    sub = _SUB_RE.match(line)
    if sub:
        return "subsection", sub.group(1), _SUB_RE.sub("", line, count=1).strip()
    item = _ALPHA_RE.match(line)
    if item:
        return "item", item.group(1), _ALPHA_RE.sub("", line, count=1).strip()
    return "raw", "", line


def _parse_footnotes(html: str) -> list[Amendment]:
    out: list[Amendment] = []
    for line in _split_html_lines(html):
        for part in _NOTE_SPLIT_RE.split(line):
            part = _clean_text(part)
            if part:
                out.append(Amendment(marker=part))
    return out


def parse_section_payload(
    *,
    section_number: str,
    marginal_note: str,
    section_id: str,
    payload: dict,
) -> Section:
    sub_items: list[SubItem] = []
    body_lines: list[str] = []
    for line in _split_html_lines(str(payload.get("content", ""))):
        kind, label, text = _classify_line(line)
        if kind == "raw":
            body_lines.append(text)
        else:
            sub_items.append(SubItem(kind=kind, label=label, text=text))
    return Section(
        number=section_number,
        marginal_note=marginal_note,
        text="\n\n".join(body_lines).strip(),
        sub_items=sub_items,
        amendments=_parse_footnotes(str(payload.get("footnote", ""))),
        anchor_id=section_id,
    )


def fetch_index(client: HttpClient) -> list[dict[str, str]]:
    return parse_index(client.fetch(INDEX_URL))


def fetch_section_payload(client: HttpClient, section_id: str) -> dict:
    query = urllib.parse.urlencode({"actid": ACT_ID, "sectionID": section_id})
    raw = client.fetch(f"{CONTENT_URL}?{query}")
    return json.loads(raw)


def _find_section(index: list[dict[str, str]], section: str) -> dict[str, str]:
    for item in index:
        if item["section_number"] == section:
            return item
    raise SystemExit(f"section not found in BNS index: {section}")


def cmd_index(args) -> None:
    client = HttpClient(delay=args.delay)
    items = fetch_index(client)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(items)} sections -> {out_path}", file=sys.stderr)


def cmd_section(args) -> None:
    client = HttpClient(delay=args.delay)
    index = fetch_index(client)
    item = _find_section(index, args.section)
    try:
        payload = fetch_section_payload(client, item["section_id"])
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} for section {args.section}", file=sys.stderr)
        sys.exit(2)
    section = parse_section_payload(
        section_number=item["section_number"],
        marginal_note=item["title"],
        section_id=item["section_id"],
        payload=payload,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(asdict(section), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote s{section.number} -> {out_path}", file=sys.stderr)


def cmd_act(args) -> None:
    client = HttpClient(delay=args.delay)
    index = fetch_index(client)
    if args.limit:
        index = index[: args.limit]
    sections: list[Section] = []
    n_fail = 0
    print(f"will scrape {len(index)} BNS sections", file=sys.stderr)
    for i, item in enumerate(index, 1):
        try:
            payload = fetch_section_payload(client, item["section_id"])
            sections.append(parse_section_payload(
                section_number=item["section_number"],
                marginal_note=item["title"],
                section_id=item["section_id"],
                payload=payload,
            ))
        except Exception as exc:  # noqa: BLE001
            n_fail += 1
            print(f"  ! s{item['section_number']}: {type(exc).__name__}: {exc}", file=sys.stderr)
        if i % 50 == 0 or i == len(index):
            print(f"  [{i}/{len(index)}] ok={len(sections)} fail={n_fail}", file=sys.stderr)
    act = Act(
        act_code=args.act_code,
        title=args.title,
        url=INDEX_URL,
        scraped_at=_dt.datetime.now(_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        source="indiacode",
        act_id=ACT_ID,
        sections=sections,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(act.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"done: {len(sections)}/{len(index)} sections, {n_fail} failures -> {out_path}", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="scrape_bns",
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--delay", type=float, default=CRAWL_DELAY,
                   help=f"crawl delay seconds (default: {CRAWL_DELAY})")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="enumerate BNS sections")
    pi.add_argument("--out", required=True)

    ps = sub.add_parser("section", help="scrape one BNS section")
    ps.add_argument("--section", required=True)
    ps.add_argument("--out", required=True)

    pa = sub.add_parser("act", help="scrape every BNS section into one raw act file")
    pa.add_argument("--act-code", default="BNS2023")
    pa.add_argument("--title", default="The Bharatiya Nyaya Sanhita, 2023")
    pa.add_argument("--out", required=True)
    pa.add_argument("--limit", type=int, default=0, help="cap section count (0 = no cap)")

    args = p.parse_args()
    {"index": cmd_index, "section": cmd_section, "act": cmd_act}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
