"""sso scraper for singapore statutes online (sso.agc.gov.sg).

generic: works for any Act, not just penal code. uses headless Chromium via
Playwright because SSO lazy-loads provisions over XHR after JS runs.

usage:
    python -m playwright install chromium
    python scripts/scrape_sso.py index --out library/_index/sso_acts.json
    python scripts/scrape_sso.py act --act-code PC1871 --title "Penal Code 1871" \\
        --out library/penal_code/_raw/act.json

    # Phase 2a — diachronic snapshots:
    python scripts/scrape_sso.py historical-list --act-code PC1871 \\
        --out library/penal_code/_raw/historical_dates.json
    python scripts/scrape_sso.py historical --act-code PC1871 --date 19980101 \\
        --out library/penal_code/_raw/historical/19980101.json
    python scripts/scrape_sso.py historical-bulk --act-code PC1871 \\
        --out-dir library/penal_code/_raw/historical

respects robots.txt: 6s crawl-delay, skips /search.
"""
from __future__ import annotations
import argparse, asyncio, datetime as _dt, json, re, sys, time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    sys.exit("missing beautifulsoup4: pip install beautifulsoup4 lxml playwright")

try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    sys.exit("missing playwright: pip install playwright && python -m playwright install chromium")

BASE = "https://sso.agc.gov.sg"
CRAWL_DELAY = 6.0  # per SSO robots.txt
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "  # use Chrome UA
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# -- schema -------------------------------------------------------------------

@dataclass
class Amendment:
    marker: str                                           # e.g. "Act 15 of 2019"
    note: Optional[str] = None

@dataclass
class SubItem:
    # kind: illustration | explanation | exception | proviso | subsection | heading | item | raw
    kind: str
    label: str                                            # e.g. "(a)", "1", "2"; "" when absent
    text: str

@dataclass
class Section:
    number: str                                           # e.g. "415", "415A"
    marginal_note: str
    text: str
    sub_items: list[SubItem] = field(default_factory=list)
    amendments: list[Amendment] = field(default_factory=list)
    anchor_id: Optional[str] = None                       # SSO provision id e.g. "pr415-"

@dataclass
class Act:
    act_code: str                                         # e.g. "PC1871"
    title: str
    url: str
    scraped_at: str
    valid_date: Optional[str] = None                      # YYYYMMDD
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

# -- client -------------------------------------------------------------------

class SSOClient:
    def __init__(self, headless: bool = True, delay: float = CRAWL_DELAY):
        self.headless, self.delay = headless, delay
        self._last = 0.0
        self._pw = None
        self._browser: Browser | None = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, *exc):
        if self._browser: await self._browser.close()
        if self._pw: await self._pw.stop()

    async def _throttle(self):
        gap = time.monotonic() - self._last
        if gap < self.delay: await asyncio.sleep(self.delay - gap)
        self._last = time.monotonic()

    async def _new_page(self) -> tuple:
        ctx = await self._browser.new_context(user_agent=UA)
        page = await ctx.new_page()
        return ctx, page

    async def fetch(self, url: str, wait_selector: str | None = None, timeout_ms: int = 60000) -> str:
        await self._throttle()
        ctx, page = await self._new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if wait_selector:
                try: await page.wait_for_selector(wait_selector, timeout=timeout_ms)
                except Exception: pass                    # return whatever we got, parser reports coverage
            return await page.content()
        finally:
            await page.close(); await ctx.close()

    async def fetch_whole_doc(
        self,
        act_code: str,
        timeout_ms: int = 120000,
        valid_date: Optional[str] = None,
    ) -> str:
        """fetch the WholeDoc view and drive lazy-load until all provisions render.

        ``valid_date`` (YYYYMMDD) selects a historical snapshot via the
        SSO ``ValidDate`` query parameter; the parser extracts the
        same field from og:url so the round-trip is consistent.
        """
        if valid_date:
            url = f"{BASE}/Act/{act_code}?ValidDate={valid_date}&WholeDoc=1"
        else:
            url = f"{BASE}/Act/{act_code}?WholeDoc=1"
        await self._throttle()
        ctx, page = await self._new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # lazy-load driver: repeatedly scroll every scrollable element to bottom
            # until prov1 count is stable across N consecutive ticks
            stable, prev = 0, -1
            for tick in range(200):
                await page.evaluate(                      # scroll window + every inner scroller
                    "() => {"
                    "  window.scrollTo(0, document.body.scrollHeight);"
                    "  document.querySelectorAll('*').forEach(el => {"
                    "    if (el.scrollHeight > el.clientHeight + 4) el.scrollTop = el.scrollHeight;"
                    "  });"
                    "}"
                )
                await page.wait_for_timeout(1200)
                count = await page.evaluate("document.querySelectorAll('div.prov1').length")
                if count == prev and count > 0:
                    stable += 1
                    if stable >= 3: break                 # 3 consecutive identical counts = done
                else:
                    stable, prev = 0, count
            return await page.content()
        finally:
            await page.close(); await ctx.close()

# -- parser -------------------------------------------------------------------

_LEAD_NUM_RE = re.compile(r"^\s*(\d+[A-Z]*)\s*\.\s*")    # e.g. "415." or "304A."
_EXPL_RE = re.compile(r"^\s*Explanation\s*(\d*)\s*\.?\s*[—-]\s*", re.I)
_EXCEPT_RE = re.compile(r"^\s*Exception\s*(\d*)\s*\.?\s*[—-]\s*", re.I)
_SUB_RE = re.compile(r"^\s*\((\d+[A-Z]?)\)\s*")          # subsection: (1), (2A)
_ALPHA_RE = re.compile(r"^\s*\(\s*([a-z]+|[ivxlcdm]+|\d+)\s*\)\s*", re.I)
_AMEND_RE = re.compile(r"\[[^\]]*(?:Act|S)\s+\d+[^\]]*\]")

def parse_whole_doc(html: str, *, act_code: str, title: str, url: str, valid_date: str | None) -> Act:
    soup = BeautifulSoup(html, "lxml")
    valid = valid_date or _extract_valid_date(soup)
    sections = []
    for prov in soup.select("div.prov1"):
        s = _parse_section(prov)
        if s: sections.append(s)
    return Act(
        act_code=act_code, title=title, url=url, valid_date=valid,
        scraped_at=_dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        sections=sections,
    )

def _extract_valid_date(soup: BeautifulSoup) -> str | None:
    m = soup.find("meta", attrs={"name": "og:url"})
    if m and "ValidDate=" in m.get("content", ""):
        mm = re.search(r"ValidDate=(\d{8})", m["content"])
        if mm: return mm.group(1)
    return None

def _txt(el) -> str:
    if el is None: return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()

def _body_text(body_el: Tag) -> str:
    """extract prov1Txt / prov2Txt main-paragraph text, excluding nested tables
    (which carry (a)(b)(c) subitems captured separately) and the leading
    <strong>N.</strong> section marker. Also drops amendNote children so
    amendment markers stay in their own field."""
    clone = BeautifulSoup(str(body_el), "lxml")
    # nested tables hold (a)(b)(c) alternates + (i)(ii)(iii) deeper lists
    for t in clone.find_all("table"):
        if t.find_parent("table") is not None: t.decompose()
    for d in clone.find_all("div", class_="table-responsive"):
        d.decompose()
    for d in clone.find_all("div", class_="amendNote"):
        d.decompose()
    # drop a leading "N." section-number span
    lead = clone.find("strong")
    if lead and _LEAD_NUM_RE.match(_txt(lead)): lead.decompose()
    return _txt(clone)

def _walk_nested_items(container: Tag, parent_label: str = "") -> list[tuple[str, str, str]]:
    """Recursively extract (kind, label, text) tuples from nested SSO list
    tables (p1_1 holding p1No/pTxt pairs; p2_1 holding p2No/p2Txt; etc.).

    Returns a flat list with hierarchical labels like "(2)(a)", "(2)(a)(i)"
    so the canonical corpus is complete end-to-end.
    """
    out: list[tuple[str, str, str]] = []
    # direct-child tables only; deeper tables are reached via recursion on the
    # row's text cell. Walk the tbody non-recursively to avoid finding the
    # same <tr> twice when a row contains its own sub-table.
    for tbl in container.find_all("table", recursive=False):
        bodies = tbl.find_all("tbody", recursive=False) or [tbl]
        for tbody in bodies:
            for row in tbody.find_all("tr", recursive=False):
                label_cell = row.find(["td", "th"], class_=re.compile(r"^p\d*No$"),
                                      recursive=False)
                text_cell = row.find(["td", "th"],
                                     class_=re.compile(r"^p\d*Txt$|^pTxt$"),
                                     recursive=False)
                if not text_cell: continue
                raw_label = _txt(label_cell) if label_cell else ""
                # normalise "( a )" → "(a)", "(i)" stays "(i)"
                label_clean = re.sub(r"\s+", "", raw_label) if raw_label else ""
                combined_label = f"{parent_label}{label_clean}"
                # cell text minus its own nested tables (those surface via recursion)
                clone = BeautifulSoup(str(text_cell), "lxml")
                for t in clone.find_all("table"):
                    t.decompose()
                for d in clone.find_all("div", class_="amendNote"):
                    d.decompose()
                text = _txt(clone)
                if text:
                    out.append(("item", combined_label, text))
                out.extend(_walk_nested_items(text_cell, combined_label))
    return out

def _classify_fs(fs: Tag, text: str) -> tuple[str, str]:
    em = fs.find("em")
    em_txt = _txt(em).lower() if em else ""
    tl = text.strip().lower()
    if em_txt.startswith("illustration"):
        return ("heading", "") if tl in ("illustration", "illustrations") else ("illustration", "")
    if em_txt.startswith("explanation"):
        m = _EXPL_RE.match(text)
        return "explanation", (m.group(1) if m else "")
    if tl in ("illustration", "illustrations"): return "heading", ""
    m = _EXCEPT_RE.match(text)
    if m: return "exception", m.group(1)
    m = _EXPL_RE.match(text)
    if m: return "explanation", m.group(1)
    m = _SUB_RE.match(text)                               # check numeric (1), (2) first
    if m: return "subsection", m.group(1)
    m = _ALPHA_RE.match(text)
    if m: return "item", m.group(1)                       # ambiguous: illustration / proviso / list item
    if len(text) < 80 and not text.rstrip().endswith((".", ";", ":", ",")): return "heading", ""
    return "raw", ""

def _parse_section(prov: Tag) -> Section | None:
    # SSO layout for a fully-featured offence section:
    #   td.prov1Hdr (marginal note + anchor id)
    #   td.prov1Txt (body for subsection (1) or the only body — leading
    #                <strong>N.</strong> + main text + nested p1_1 table
    #                carrying (a)(b)(c) alternates)
    #   td.prov2Txt [repeated] (each is one numbered subsection (N) with its
    #                own body and its own nested (a)(b)(c)/(i)(ii)(iii) tables)
    #   td.prov1tbl > … > td.fs (cells carrying illustrations / explanations /
    #                exceptions / provisos — legacy layout)
    #   .amendNote (inline amendment markers)
    hdr = prov.select_one(".prov1Hdr, td.prov1Hdr")
    anchor = hdr.get("id") if hdr else prov.get("id")
    marginal = _txt(hdr)

    body_el = prov.select_one(".prov1Txt")
    number, body = "", ""
    if body_el:
        lead = body_el.find("strong")
        if lead:
            m = _LEAD_NUM_RE.match(_txt(lead))
            if m: number = m.group(1)
        body = _body_text(body_el)

    sub_items: list[SubItem] = []

    # (1a) Some sections (s377BD, others) wrap subsection (1) in a
    # `span.prov2TxtIL` nested inside prov1Txt. If present, treat it like any
    # prov2Txt subsection — extract its body text + walk its nested tables.
    if body_el:
        for span in body_el.select("span.prov2TxtIL"):
            span_text = _body_text(span)
            span_num_match = _SUB_RE.match(span_text)
            span_label = span_num_match.group(0).strip() if span_num_match else ""
            if span_text:
                sub_items.append(SubItem(
                    kind="subsection", label=span_label, text=span_text,
                ))
            for kind, label, text in _walk_nested_items(span, parent_label=span_label):
                sub_items.append(SubItem(kind=kind, label=label, text=text))

    # (1b) nested (a)(b)(c)/(i)(ii)(iii) items directly inside prov1Txt (no
    # span wrapper) — e.g. s415-style sections. Only runs if we didn't already
    # handle them via span.prov2TxtIL above, to avoid double-emission.
    if body_el and not body_el.select("span.prov2TxtIL"):
        for kind, label, text in _walk_nested_items(body_el, parent_label=""):
            sub_items.append(SubItem(kind=kind, label=label, text=text))

    # (2) each prov2Txt is a fresh subsection with its own body + nested tree
    for sub in prov.select("td.prov2Txt"):
        sub_text = _body_text(sub)
        sub_num_match = _SUB_RE.match(sub_text)
        sub_label = sub_num_match.group(0).strip() if sub_num_match else ""
        if sub_text:
            sub_items.append(SubItem(
                kind="subsection",
                label=sub_label,
                text=sub_text,
            ))
        # walk its nested p1_1 / p2_1 tables; prefix child labels with the
        # parent subsection marker so "(2)(a)(i)" reads hierarchically.
        for kind, label, text in _walk_nested_items(sub, parent_label=sub_label):
            sub_items.append(SubItem(kind=kind, label=label, text=text))

    # (3) legacy td.fs items (illustrations/explanations/exceptions). These
    # usually live inside prov1tbl tables and don't overlap with prov2Txt.
    for fs in prov.select("td.fs"):
        t = _txt(fs)
        if not t: continue
        kind, label = _classify_fs(fs, t)
        sub_items.append(SubItem(kind=kind, label=label, text=t))

    amends: list[Amendment] = []
    for el in prov.select(".amendNote, .amendMkr, .hist, sup.amend"):
        t = _txt(el)
        if t: amends.append(Amendment(marker=t))
    for m in _AMEND_RE.finditer(_txt(prov)):
        amends.append(Amendment(marker=m.group(0)))
    seen, uniq = set(), []
    for a in amends:
        if a.marker in seen: continue
        seen.add(a.marker); uniq.append(a)

    if not (number or marginal or body or sub_items): return None
    return Section(
        number=number, marginal_note=marginal, text=body,
        sub_items=sub_items, amendments=uniq, anchor_id=anchor,
    )

# -- index scrape -------------------------------------------------------------

async def fetch_historical_dates(client: SSOClient, act_code: str) -> list[str]:
    """Enumerate historical snapshot dates SSO advertises for an Act.

    SSO surfaces a "Versions" dropdown on the act-detail page; each option
    carries a ValidDate=YYYYMMDD value. Returns dates as YYYYMMDD strings,
    chronologically sorted.
    """
    url = f"{BASE}/Act/{act_code}"
    html = await client.fetch(url, wait_selector="select, .versions, a[href*='ValidDate=']")
    soup = BeautifulSoup(html, "lxml")
    dates: set[str] = set()
    # Pattern A: `<option value="…ValidDate=YYYYMMDD…">…</option>`.
    for opt in soup.select("option"):
        v = opt.get("value", "")
        m = re.search(r"ValidDate=(\d{8})", v)
        if m:
            dates.add(m.group(1))
    # Pattern B: anchors in a "Historical" or "Versions" panel.
    for a in soup.select("a[href*='ValidDate=']"):
        m = re.search(r"ValidDate=(\d{8})", a.get("href", ""))
        if m:
            dates.add(m.group(1))
    return sorted(dates)


async def fetch_index(client: SSOClient) -> list[dict]:
    url = f"{BASE}/Browse/Act/Current/All?PageSize=500&SortBy=Title&SortOrder=ASC"
    html = await client.fetch(url, wait_selector="a[href^='/Act/']")
    soup = BeautifulSoup(html, "lxml")
    seen, out = set(), []
    for a in soup.select("a[href^='/Act/']"):
        href = a.get("href", "")
        m = re.match(r"^/Act/([A-Za-z0-9]+)(?:[?/]|$)", href)
        if not m: continue
        code = m.group(1)
        if code in seen: continue
        title = _txt(a)
        if not title: continue
        seen.add(code)
        out.append({"act_code": code, "title": title, "href": href})
    return out

# -- cli ----------------------------------------------------------------------

async def _cmd_index(args) -> None:
    async with SSOClient(headless=not args.headed) as c:
        items = await fetch_index(c)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"wrote {len(items)} acts → {out}")

async def _cmd_act(args) -> None:
    async with SSOClient(headless=not args.headed) as c:
        html = await c.fetch_whole_doc(args.act_code)
    url = f"{BASE}/Act/{args.act_code}?WholeDoc=1"
    act = parse_whole_doc(html, act_code=args.act_code,
                          title=args.title or args.act_code,
                          url=url, valid_date=None)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(act.to_dict(), indent=2, ensure_ascii=False))
    if args.dump_html:
        Path(args.dump_html).write_text(html)
    print(f"wrote {len(act.sections)} sections → {out}")


async def _cmd_historical_list(args) -> None:
    async with SSOClient(headless=not args.headed) as c:
        dates = await fetch_historical_dates(c, args.act_code)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"act_code": args.act_code, "dates": dates},
                              indent=2, ensure_ascii=False))
    print(f"found {len(dates)} historical dates for {args.act_code} → {out}")


async def _cmd_historical(args) -> None:
    """Phase 2a v0 — fetch one historical snapshot.

    SSO addresses historical Act views via ``?ValidDate=YYYYMMDD&WholeDoc=1``.
    Output mirrors `_cmd_act` but stamps the requested ValidDate so
    downstream re-encoding sees a stable per-snapshot identifier.
    """
    async with SSOClient(headless=not args.headed) as c:
        html = await c.fetch_whole_doc(args.act_code, valid_date=args.date)
    url = f"{BASE}/Act/{args.act_code}?ValidDate={args.date}&WholeDoc=1"
    act = parse_whole_doc(html, act_code=args.act_code,
                          title=args.title or args.act_code,
                          url=url, valid_date=args.date)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(act.to_dict(), indent=2, ensure_ascii=False))
    if args.dump_html:
        Path(args.dump_html).write_text(html)
    print(f"wrote {len(act.sections)} sections @ {args.date} → {out}")


async def _cmd_historical_bulk(args) -> None:
    """Walk every advertised historical date and persist a snapshot file.

    Skips any date for which the output already exists unless
    ``--force`` is set. Output layout::

        <out_dir>/<act_code>/<YYYYMMDD>.json

    plus a sibling ``<act_code>/historical_index.json`` mapping date
    to relative path so downstream re-encoding can iterate in order.
    """
    out_dir = Path(args.out_dir) / args.act_code
    out_dir.mkdir(parents=True, exist_ok=True)
    async with SSOClient(headless=not args.headed) as c:
        dates = await fetch_historical_dates(c, args.act_code)
        if args.limit:
            dates = dates[: args.limit]
        index: dict[str, str] = {}
        n_done = n_skip = n_fail = 0
        for date in dates:
            fp = out_dir / f"{date}.json"
            if fp.exists() and not args.force:
                n_skip += 1
                index[date] = str(fp.relative_to(out_dir.parent))
                continue
            try:
                html = await c.fetch_whole_doc(args.act_code, valid_date=date)
                url = f"{BASE}/Act/{args.act_code}?ValidDate={date}&WholeDoc=1"
                act = parse_whole_doc(html, act_code=args.act_code,
                                      title=args.title or args.act_code,
                                      url=url, valid_date=date)
                fp.write_text(json.dumps(act.to_dict(), indent=2, ensure_ascii=False))
                n_done += 1
                index[date] = str(fp.relative_to(out_dir.parent))
                print(f"  ✓ {date}: {len(act.sections)} sections")
            except Exception as exc:  # noqa: BLE001 — keep going on per-date failure
                n_fail += 1
                print(f"  ! {date}: {exc}", file=sys.stderr)
    (out_dir / "historical_index.json").write_text(
        json.dumps({"act_code": args.act_code, "dates": index},
                   indent=2, ensure_ascii=False)
    )
    print(f"done: {n_done} fetched, {n_skip} cached, {n_fail} failed "
          f"→ {out_dir.relative_to(Path.cwd()) if out_dir.is_absolute() else out_dir}")

def main() -> None:
    p = argparse.ArgumentParser(prog="scrape_sso", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="scrape metadata for all current Acts")
    pi.add_argument("--out", default="library/_index/sso_acts.json")
    pi.add_argument("--headed", action="store_true", help="show browser window")

    pa = sub.add_parser("act", help="scrape whole document for one Act")
    pa.add_argument("--act-code", required=True, help="SSO act code, e.g. PC1871")
    pa.add_argument("--title", help="display title (default: act_code)")
    pa.add_argument("--out", required=True, help="output JSON path")
    pa.add_argument("--dump-html", help="optional: also save raw rendered HTML")
    pa.add_argument("--headed", action="store_true")

    phl = sub.add_parser("historical-list",
                         help="list every historical ValidDate SSO advertises for an Act")
    phl.add_argument("--act-code", required=True)
    phl.add_argument("--out", required=True, help="output JSON path")
    phl.add_argument("--headed", action="store_true")

    ph = sub.add_parser("historical",
                        help="scrape one historical snapshot of an Act (--date YYYYMMDD)")
    ph.add_argument("--act-code", required=True)
    ph.add_argument("--date", required=True, help="YYYYMMDD ValidDate to fetch")
    ph.add_argument("--title", help="display title (default: act_code)")
    ph.add_argument("--out", required=True, help="output JSON path")
    ph.add_argument("--dump-html")
    ph.add_argument("--headed", action="store_true")

    phb = sub.add_parser("historical-bulk",
                         help="walk every advertised ValidDate and persist a snapshot per date")
    phb.add_argument("--act-code", required=True)
    phb.add_argument("--title", help="display title (default: act_code)")
    phb.add_argument("--out-dir", required=True,
                     help="output directory; per-act subdir is created automatically")
    phb.add_argument("--limit", type=int, default=0,
                     help="cap number of historical dates fetched (0 = no cap)")
    phb.add_argument("--force", action="store_true",
                     help="re-fetch even when cached output exists")
    phb.add_argument("--headed", action="store_true")

    args = p.parse_args()
    asyncio.run({
        "index": _cmd_index,
        "act": _cmd_act,
        "historical-list": _cmd_historical_list,
        "historical": _cmd_historical,
        "historical-bulk": _cmd_historical_bulk,
    }[args.cmd](args))

if __name__ == "__main__":
    main()
