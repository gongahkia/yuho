"""Pakistan Penal Code 1860 PDF scraper.

Pakistan Code lists PPC as "Under Review" and links a PDF, but the PDF
host can be unavailable from local networks. The default source is the
UNODC-hosted PPC PDF incorporating amendments to 16 February 2017; the
official Pakistan Code page/PDF URLs are recorded in output metadata.

Usage:
    python scripts/scrape_ppc.py act --out library/pakistan_penal_code/_raw/act.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import tempfile
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_SOURCE_URL = (
    "https://www.unodc.org/cld/uploads/res/document/pak/1860/"
    "pakistan_penal_code_1860_html/"
    "Pakistan_Penal_Code_1860_incorporating_amendments_to_16_February_2017.pdf"
)
PAKISTAN_CODE_PAGE = (
    "https://pakistancode.gov.pk/english/"
    "UY2FqaJw1-apaUY2Fqa-apaUY2Npa5lo-sg-jjjjjjjjjjjjj"
)
PAKISTAN_CODE_PDF = (
    "https://pakistancode.gov.pk/pdffiles/"
    "administratord5622ea3f15bfa00b17d2cf7770a8434.pdf"
)
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
    official_page: str
    official_pdf: str
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_SECTION_RE = re.compile(r"^\s*(?:\d+\[)?(\d+(?:\s*[A-Z])?(?:-[A-Z])?)\.\s+(.*)$")
_PAGE_RE = re.compile(r"^\s*Page\s+\d+\s+of\s+\d+", re.I)


def _norm_number(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\uf0be", "")).strip()


def _download(url: str, out: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        out.write_bytes(resp.read())


def _pdftotext(pdf_path: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _body_start(lines: list[str]) -> int:
    starts = [
        i for i, line in enumerate(lines)
        if re.match(r"^\s*1\.\s+Title and extent", line)
    ]
    if not starts:
        raise ValueError("could not locate PPC section 1 body start")
    return starts[-1]


def _parse_toc_titles(lines: list[str], body_start: int) -> dict[str, str]:
    titles: dict[str, str] = {}
    current: Optional[str] = None
    for i, line in enumerate(lines[:body_start]):
        if "THE PAKISTAN PENAL CODE" in line and current:
            break
        if "THE PAKISTAN PENAL CODE" in line:
            continue
        if _PAGE_RE.match(line):
            continue
        match = _SECTION_RE.match(line)
        if match:
            current = _norm_number(match.group(1))
            titles[current] = _clean(match.group(2))
            continue
        stripped = _clean(line)
        if current and stripped and not stripped.startswith(("CHAPTER", "CONTENTS", "SECTIONS:")):
            titles[current] = f"{titles[current]} {stripped}"
    return titles


def parse_pdf_text(text: str) -> list[Section]:
    lines = text.replace("\f", "\n").splitlines()
    start = _body_start(lines)
    titles = _parse_toc_titles(lines, start)
    sections: list[Section] = []
    current: Optional[dict] = None
    for line in lines[start:]:
        if _PAGE_RE.match(line) or set(line.strip()) <= {"_"}:
            continue
        stripped = _clean(line)
        if not stripped:
            continue
        match = _SECTION_RE.match(line)
        if match:
            number = _norm_number(match.group(1))
            if titles and number not in titles:
                if current:
                    current["parts"].append(stripped)
                continue
            if current:
                sections.append(Section(
                    number=current["number"],
                    marginal_note=current["title"],
                    text=_clean(" ".join(current["parts"])),
                ))
            title = titles.get(number, "")
            rest = _clean(match.group(2))
            body = rest
            if title and rest.lower().startswith(title.lower()):
                body = rest[len(title):].strip()
            elif not title:
                pieces = rest.split(".", 1)
                title = pieces[0].strip() + "."
                body = pieces[1].strip() if len(pieces) > 1 else ""
            current = {"number": number, "title": title, "parts": [body] if body else []}
        elif current:
            current["parts"].append(stripped)
    if current:
        sections.append(Section(
            number=current["number"],
            marginal_note=current["title"],
            text=_clean(" ".join(current["parts"])),
        ))
    return sections


def scrape_act(source_url: str, pdf_path: Optional[Path] = None) -> Act:
    with tempfile.TemporaryDirectory() as tmp:
        local_pdf = pdf_path or Path(tmp) / "ppc.pdf"
        if pdf_path is None:
            _download(source_url, local_pdf)
        text = _pdftotext(local_pdf)
    return Act(
        act_code="PPC1860",
        title="Pakistan Penal Code (PPC), 1860",
        url=source_url,
        scraped_at=_dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        source="unodc_pdf_2017" if "unodc.org" in source_url else "pdf",
        official_page=PAKISTAN_CODE_PAGE,
        official_pdf=PAKISTAN_CODE_PDF,
        sections=parse_pdf_text(text),
    )


def cmd_act(args) -> None:
    act = scrape_act(args.source_url, args.pdf)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(act.to_dict(), indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"wrote {len(act.sections)} sections -> {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("act", help="scrape/parse PPC PDF into raw JSON")
    pa.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    pa.add_argument("--pdf", type=Path, help="already-downloaded PDF path")
    pa.add_argument("--out", required=True)
    args = parser.parse_args()
    {"act": cmd_act}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
