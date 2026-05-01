"""Indian Penal Code 1860 scraper for the §8 cross-jurisdiction
comparative-encoding paper claim.

Two source backends, both server-rendered HTML (no Playwright needed):

* **indiacode**  — https://www.indiacode.nic.in (National Informatics
  Centre, the official portal).
* **advocatekhoj** — https://www.advocatekhoj.com/library/bareacts/indianpenalcode/
  (community mirror, often easier to parse).

The scraper uses ``urllib.request`` from stdlib so it adds no new
install deps beyond ``beautifulsoup4 + lxml`` (already required by
``scrape_sso.py``). Output JSON matches the shape of the SSO
scraper's ``Act`` / ``Section`` / ``SubItem`` records, so the
agent-dispatched encoder pipeline (``apply_flag_fix.py``,
``l3_audit.py``) can iterate the IPC corpus the same way it
iterates the SG PC corpus.

Respects the same 6-second crawl-delay convention as the SSO
scraper (India Code's robots.txt does not specify a delay; we
err on the conservative side).

Usage::

    python scripts/scrape_indiacode.py index \\
        --out library/indian_penal_code/_raw/index.json

    python scripts/scrape_indiacode.py section \\
        --section 302 \\
        --out library/indian_penal_code/_raw/sections/s302.json

    python scripts/scrape_indiacode.py act \\
        --out library/indian_penal_code/_raw/act.json

    # Pluggable backend:
    python scripts/scrape_indiacode.py act --source advocatekhoj \\
        --out library/indian_penal_code/_raw/act-advocatekhoj.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    sys.exit(
        "missing beautifulsoup4: pip install beautifulsoup4 lxml"
    )

CRAWL_DELAY = 6.0
UA = (
    "Mozilla/5.0 (compatible; YuhoScraper/0.1; "
    "+https://github.com/gongahkia/yuho)"
)

# -- schema (mirrors scrape_sso.py for downstream tool reuse) ------------

@dataclass
class Amendment:
    marker: str
    note: Optional[str] = None


@dataclass
class SubItem:
    """kind: illustration / explanation / exception / proviso /
    subsection / heading / item / raw."""
    kind: str
    label: str
    text: str


@dataclass
class Section:
    number: str
    marginal_note: str
    text: str
    sub_items: List[SubItem] = field(default_factory=list)
    amendments: List[Amendment] = field(default_factory=list)
    anchor_id: Optional[str] = None


@dataclass
class Act:
    act_code: str
    title: str
    url: str
    scraped_at: str
    source: str
    sections: List[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# -- HTTP client ---------------------------------------------------------


class HttpClient:
    """Stdlib urllib client with crawl-delay throttling and a Chrome-
    flavoured UA so the upstream sites don't reject us as a bot."""

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
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")


# -- parsers --------------------------------------------------------------


_LEAD_NUM_RE = re.compile(r"^\s*(\d+[A-Z]*)\.\s*")
_AMEND_RE = re.compile(r"\[[^\]]*(?:Act|Ord)\s+\d+[^\]]*\]")
_SUB_RE = re.compile(r"^\s*\((\d+[A-Z]?)\)\s*")
_ALPHA_RE = re.compile(r"^\s*\(\s*([a-z]+|[ivxlcdm]+|\d+)\s*\)\s*", re.I)


def _txt(el) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def parse_advocatekhoj_section(html: str, section_num: str) -> Optional[Section]:
    """Parse one section page from AdvocateKhoj.

    AdvocateKhoj's IPC pages (verified 2026-04-30) render as a single
    ``<div id="content_container" class="bareacts_contentarea">`` body
    with no ``<h*>`` headings — the section number + marginal note
    appear as the first non-empty text block (e.g. ``"1. Title and
    extent of operation of the Code"``), followed by the section body
    and trailing ``Back / Index / Next`` navigation strings.

    The original parser hunted for ``<h1>/<h2>/<h3>`` headings and a
    ``<div class="content">`` body; both selectors are stale. We now
    pull the content area by id+class, drop the navigation tail, and
    split the marginal note off the leading ``"<num>. <title>"``
    prefix line.
    """
    soup = BeautifulSoup(html, "lxml")

    # Legacy-fixture path: when an explicit `<h1>/<h2>/<h3>` heading
    # carries "Section N. <marginal>", honour it. The 2026-04-30
    # AdvocateKhoj live site has dropped these headings (folding the
    # marginal into the first `<p>` instead), but the bundled
    # `tests/fixtures/indiacode_advocatekhoj_s302.html` fixture
    # preserves the old shape — so the parser must accept both.
    legacy_heading = soup.find("h1") or soup.find("h2") or soup.find("h3")
    legacy_marginal: Optional[str] = None
    if legacy_heading is not None:
        h = _txt(legacy_heading)
        m = re.search(
            rf"Section\s+{re.escape(section_num)}[A-Z]*\.?\s*(.+)",
            h, flags=re.IGNORECASE,
        )
        if m:
            legacy_marginal = m.group(1).strip()

    body = (soup.find("div", id="content_container")
            or soup.find("div", class_="bareacts_contentarea")
            or soup.find("div", class_="content")
            or soup.find("div", id="content")
            or soup.find("div", class_="bareact")
            or soup.find("article")
            or soup.find("main")
            or soup.body)
    if body is None:
        return None

    paragraphs_raw: List[str] = []
    p_tags = body.find_all("p", recursive=True)
    if p_tags:
        for p in p_tags:
            t = " ".join(_txt(p).split())
            if t:
                paragraphs_raw.append(t)
    else:
        raw_text = body.get_text(separator="\n", strip=True)
        paragraphs_raw = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]

    if paragraphs_raw and paragraphs_raw[0].lower().startswith("indian penal code"):
        paragraphs_raw = paragraphs_raw[1:]
    while paragraphs_raw and paragraphs_raw[-1].lower() in {"back", "index", "next"}:
        paragraphs_raw.pop()

    if not paragraphs_raw and legacy_marginal is None:
        return None

    if legacy_marginal is not None:
        # Legacy shape: heading-tag carries the marginal; all `<p>`s
        # are body content.
        marginal = legacy_marginal
        rest = paragraphs_raw
    else:
        # Live-site shape: first `<p>` carries "<num>. <marginal>".
        head = paragraphs_raw[0]
        rest = paragraphs_raw[1:]
        head_stripped = re.sub(r"^\[+\s*", "", head).rstrip("]").strip()
        m = re.match(
            rf"^{re.escape(section_num)}[A-Z]*\s*\.?\s*(.*)$", head_stripped
        )
        if m and m.group(1):
            marginal = m.group(1).strip()
        else:
            marginal = head_stripped

    sub_items: List[SubItem] = []
    amendments: List[Amendment] = []
    paragraphs: List[str] = []

    for para in rest:
        for am in _AMEND_RE.finditer(para):
            amendments.append(Amendment(marker=am.group(0)))
        t_clean = _AMEND_RE.sub("", para).strip()
        if not t_clean:
            continue
        kind = "raw"
        label = ""
        low = t_clean.lower()
        if low.startswith("illustration"):
            kind = "illustration"
        elif low.startswith("explanation"):
            kind = "explanation"
        elif low.startswith("exception"):
            kind = "exception"
        elif low.startswith("proviso"):
            kind = "proviso"
        elif _SUB_RE.match(t_clean):
            kind = "subsection"
            sm = _SUB_RE.match(t_clean)
            label = sm.group(1) if sm else ""
            t_clean = _SUB_RE.sub("", t_clean, count=1).strip()
        elif _ALPHA_RE.match(t_clean):
            kind = "item"
            am2 = _ALPHA_RE.match(t_clean)
            label = am2.group(1) if am2 else ""
            t_clean = _ALPHA_RE.sub("", t_clean, count=1).strip()
        if kind != "raw":
            sub_items.append(SubItem(kind=kind, label=label, text=t_clean))
        else:
            paragraphs.append(t_clean)

    text = "\n\n".join(paragraphs).strip()
    return Section(
        number=str(section_num),
        marginal_note=marginal,
        text=text,
        sub_items=sub_items,
        amendments=amendments,
    )


def parse_indiacode_section(html: str, section_num: str) -> Optional[Section]:
    """Parse one section from the official India Code portal.

    India Code typically serves IPC sections under the
    ``/handle/123456789/<id>`` path with a `<div class="ds-static-div">`
    or similar container. The HTML is more complex than AdvocateKhoj's
    but more authoritative.
    """
    soup = BeautifulSoup(html, "lxml")
    # India Code wraps section text in a `<table>` or `<div>` near the
    # title. Try a few selectors and pick the longest match.
    candidates = [
        soup.find("div", class_="ds-static-div"),
        soup.find("div", class_="item-page"),
        soup.find("article"),
        soup.find("main"),
    ]
    body = max(
        (c for c in candidates if c is not None),
        key=lambda c: len(_txt(c)),
        default=None,
    )
    if body is None:
        return None

    # Marginal note: heuristically the first heading inside body.
    heading = body.find(["h1", "h2", "h3", "h4"])
    marginal = ""
    if heading is not None:
        raw = _txt(heading)
        marginal = re.sub(r"^\d+[A-Z]*\.?\s*", "", raw).strip()

    paragraphs: List[str] = []
    sub_items: List[SubItem] = []
    amendments: List[Amendment] = []
    for p in body.find_all(["p", "div"], recursive=True):
        t = _txt(p)
        if not t or len(t) < 5:
            continue
        for m in _AMEND_RE.finditer(t):
            amendments.append(Amendment(marker=m.group(0)))
        t_clean = _AMEND_RE.sub("", t).strip()
        if not t_clean or t_clean == marginal:
            continue
        # Same classification as AdvocateKhoj parser.
        kind = "raw"
        label = ""
        lc = t_clean.lower()
        if lc.startswith("illustration"):
            kind = "illustration"
        elif lc.startswith("explanation"):
            kind = "explanation"
        elif lc.startswith("exception"):
            kind = "exception"
        elif lc.startswith("proviso"):
            kind = "proviso"
        elif _SUB_RE.match(t_clean):
            kind = "subsection"
            m = _SUB_RE.match(t_clean)
            label = m.group(1) if m else ""
            t_clean = _SUB_RE.sub("", t_clean, count=1).strip()
        if kind != "raw":
            sub_items.append(SubItem(kind=kind, label=label, text=t_clean))
        else:
            paragraphs.append(t_clean)

    return Section(
        number=str(section_num),
        marginal_note=marginal,
        text="\n".join(paragraphs).strip(),
        sub_items=sub_items,
        amendments=amendments,
    )


def parse_advocatekhoj_index(html: str) -> List[Dict[str, str]]:
    """Extract the list of section links from AdvocateKhoj's IPC ToC.

    AdvocateKhoj's current ToC (verified 2026-04-30) uses *relative*
    section hrefs of the form ``<num>.php?Title=…&STitle=…``, not the
    fully-qualified ``indianpenalcode/<num>.php`` shape this parser
    originally assumed. We match either form so the scraper survives
    URL-shape drift in either direction; the downstream
    ``advocatekhoj.section_url`` lambda always reconstructs the
    canonical absolute URL anyway."""
    soup = BeautifulSoup(html, "lxml")
    out: List[Dict[str, str]] = []
    seen: set[str] = set()
    abs_pattern = re.compile(r"indianpenalcode/(\d+[A-Z]*)\.php")
    rel_pattern = re.compile(r"^(\d+[A-Z]*)\.php(?:\?.*)?$")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        section_num: Optional[str] = None
        m = abs_pattern.search(href)
        if m:
            section_num = m.group(1)
        else:
            m = rel_pattern.match(href)
            if m:
                section_num = m.group(1)
        if section_num is None or section_num in seen:
            continue
        seen.add(section_num)
        out.append({
            "section_number": section_num,
            "title": _txt(a),
            "href": href,
        })
    return out


# -- backend dispatch -----------------------------------------------------


_BACKENDS: Dict[str, Dict[str, Callable]] = {
    "advocatekhoj": {
        "base_url": "https://www.advocatekhoj.com",
        "index_url": "https://www.advocatekhoj.com/library/bareacts/indianpenalcode/",
        "section_url": (
            lambda num: f"https://www.advocatekhoj.com/library/bareacts/"
                        f"indianpenalcode/{num}.php"
        ),
        "parse_index": parse_advocatekhoj_index,
        "parse_section": parse_advocatekhoj_section,
    },
    "indiacode": {
        "base_url": "https://www.indiacode.nic.in",
        # The IPC's India Code identifier is volatile; expose as override.
        "index_url": (
            "https://www.indiacode.nic.in/handle/123456789/2263/"
            "browse?type=title"
        ),
        "section_url": (
            lambda num: f"https://www.indiacode.nic.in/show-data?"
                        f"actid=AC_CEN_5_23_00037_186045_1523266765688&"
                        f"sectionId={num}"
        ),
        # India Code's index page shape is irregular; reuse the
        # AdvocateKhoj index parser as a fallback when the official
        # index page has no scrapable structure.
        "parse_index": parse_advocatekhoj_index,
        "parse_section": parse_indiacode_section,
    },
}


def _backend(name: str) -> Dict[str, Callable]:
    if name not in _BACKENDS:
        raise SystemExit(
            f"unknown source backend: {name!r} "
            f"(known: {sorted(_BACKENDS)})"
        )
    return _BACKENDS[name]


# -- CLI ------------------------------------------------------------------


def cmd_index(args) -> None:
    backend = _backend(args.source)
    client = HttpClient(delay=args.delay)
    html = client.fetch(backend["index_url"])
    items = backend["parse_index"](html)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(items, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {len(items)} sections → {out_path}", file=sys.stderr)


def cmd_section(args) -> None:
    backend = _backend(args.source)
    client = HttpClient(delay=args.delay)
    url = backend["section_url"](args.section)
    try:
        html = client.fetch(url)
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} from {url}", file=sys.stderr)
        sys.exit(2)
    section = backend["parse_section"](html, args.section)
    if section is None:
        print(f"error: parser produced no Section for {args.section}",
              file=sys.stderr)
        sys.exit(3)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(asdict(section), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if args.dump_html:
        Path(args.dump_html).write_text(html, encoding="utf-8")
    print(f"wrote s{section.number} → {out_path}", file=sys.stderr)


def cmd_act(args) -> None:
    """Scrape every section listed in the index and persist as one Act."""
    backend = _backend(args.source)
    client = HttpClient(delay=args.delay)
    index_html = client.fetch(backend["index_url"])
    items = backend["parse_index"](index_html)
    if args.limit:
        items = items[: args.limit]
    print(f"will scrape {len(items)} sections "
          f"(throttled at {args.delay}s/request)…",
          file=sys.stderr)

    sections: List[Section] = []
    n_ok = n_fail = 0
    for i, item in enumerate(items, 1):
        num = item["section_number"]
        url = backend["section_url"](num)
        try:
            html = client.fetch(url)
            sec = backend["parse_section"](html, num)
        except Exception as exc:  # noqa: BLE001 — keep run resilient
            print(f"  ✗ s{num}: {type(exc).__name__}: {exc}", file=sys.stderr)
            n_fail += 1
            continue
        if sec is None:
            print(f"  ✗ s{num}: parser returned None", file=sys.stderr)
            n_fail += 1
            continue
        sections.append(sec)
        n_ok += 1
        if i % 25 == 0 or i == len(items):
            print(f"  [{i}/{len(items)}] ok={n_ok} fail={n_fail}",
                  file=sys.stderr)

    act = Act(
        act_code=args.act_code,
        title=args.title or args.act_code,
        url=backend["index_url"],
        scraped_at=_dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        source=args.source,
        sections=sections,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(act.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"done: {n_ok}/{len(items)} sections, {n_fail} failures → {out_path}",
          file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(prog="scrape_indiacode",
                                description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--source",
                   choices=sorted(_BACKENDS),
                   default="advocatekhoj",
                   help="HTML backend (default: advocatekhoj — easier to parse "
                        "than the official India Code portal)")
    p.add_argument("--delay", type=float, default=CRAWL_DELAY,
                   help=f"crawl delay seconds (default: {CRAWL_DELAY})")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="enumerate IPC sections")
    pi.add_argument("--out", required=True, help="output JSON path")

    ps = sub.add_parser("section", help="scrape one IPC section")
    ps.add_argument("--section", required=True,
                    help="section number, e.g. 302 or 376A")
    ps.add_argument("--out", required=True, help="output JSON path")
    ps.add_argument("--dump-html",
                    help="optional: also save raw rendered HTML")

    pa = sub.add_parser("act", help="scrape every section into one act file")
    pa.add_argument("--act-code", default="IPC1860")
    pa.add_argument("--title", help="display title (default: act_code)")
    pa.add_argument("--out", required=True)
    pa.add_argument("--limit", type=int, default=0,
                    help="cap section count (0 = no cap)")

    args = p.parse_args()
    {
        "index": cmd_index,
        "section": cmd_section,
        "act": cmd_act,
    }[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
