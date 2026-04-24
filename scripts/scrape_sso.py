"""sso scraper for singapore statutes online (sso.agc.gov.sg).

generic: works for any Act, not just penal code. uses headless Chromium via
Playwright because SSO lazy-loads provisions over XHR after JS runs.

usage:
    python -m playwright install chromium
    python scripts/scrape_sso.py index --out library/_index/sso_acts.json
    python scripts/scrape_sso.py act --act-code PC1871 --title "Penal Code 1871" \\
        --out library/penal_code/_raw/act.json

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

    async def fetch_whole_doc(self, act_code: str, timeout_ms: int = 120000) -> str:
        """fetch the WholeDoc view and drive lazy-load until all provisions render."""
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
    """extract prov1Txt main-paragraph text, excluding nested tables and the
    leading <strong>N.</strong> section marker."""
    clone = BeautifulSoup(str(body_el), "lxml")
    for t in clone.find_all(["div"], class_="table-responsive"):
        t.decompose()
    for t in clone.find_all("table"):                     # belt-and-braces: any nested table
        if t.find_parent("table") is not None: t.decompose()
    # drop the very first <strong> (section-number prefix)
    lead = clone.find("strong")
    if lead and _LEAD_NUM_RE.match(_txt(lead)): lead.decompose()
    return _txt(clone)

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
    # SSO layout: td.prov1Hdr (marginal note + anchor id); td.prov1Txt (body with
    # leading <strong>N.</strong>); td.fs cells (all sub-items, nested in prov1tbl
    # tables); .amendNote (amendments).
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

    args = p.parse_args()
    asyncio.run({"index": _cmd_index, "act": _cmd_act}[args.cmd](args))

if __name__ == "__main__":
    main()
