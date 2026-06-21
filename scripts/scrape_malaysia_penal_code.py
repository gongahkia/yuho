"""Malaysia Penal Code Act 574 PDF scraper.

Usage:
    python scripts/scrape_malaysia_penal_code.py act --out library/malaysia_penal_code/_raw/act.json
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
    "https://lom.agc.gov.my/ilims/upload/portal/akta/outputaktap/1841145_BI/"
    "WJW23%EF%80%A21011%20Act%20574.pdf"
)
AGC_ACT_PAGE = "https://lom.agc.gov.my/act-detail.php?act=574&lang=BI"
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
    as_at: str
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_SECTION_RE = re.compile(r"^\s*(\d+(?:\s*[A-Za-z])?)\.\s+(.*)$")
_PAGE_RE = re.compile(
    r"^(?:\d+\s+)?(?:Penal Code|Laws of Malaysia)(?:\s+Act\s+574)?(?:\s+\d+)?$"
)


def _norm_number(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


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
        if re.match(r"^\s*1\.\s+This Act may be cited", line)
    ]
    if not starts:
        raise ValueError("could not locate Malaysia Penal Code section 1 body start")
    return starts[-1]


def _body_end(lines: list[str], start: int) -> int:
    for i in range(start, len(lines) - 1):
        if "*NOTE" in lines[i] and "Act 846" in lines[i + 1]:
            return i
    for i in range(start, len(lines)):
        if _clean(lines[i]) == "LIST OF AMENDMENTS":
            return i
    return len(lines)


def _skip_toc_line(text: str) -> bool:
    return (
        not text
        or text == "Act 574"
        or text.startswith(("Chapter", "LAWS OF MALAYSIA", "ARRANGEMENT", "Section"))
        or text.isupper()
        or _PAGE_RE.match(text) is not None
        or re.match(r"^\(?There (?:is|are) no ss?\.", text) is not None
        or re.match(r"^\d+$", text) is not None
    )


def _parse_toc_titles(lines: list[str], body_start: int) -> dict[str, str]:
    titles: dict[str, str] = {}
    current: Optional[str] = None
    for line in lines[:body_start]:
        stripped = _clean(line)
        indent = len(line) - len(line.lstrip(" "))
        if current and stripped == "An Act relating to criminal offences.":
            break
        match = _SECTION_RE.match(line)
        if match:
            current = _norm_number(match.group(1))
            titles[current] = _clean(match.group(2))
            continue
        if current and 8 <= indent <= 12 and not _skip_toc_line(stripped):
            titles[current] = _clean(f"{titles[current]} {stripped}")
    return titles


def _section_starts(
    lines: list[str],
    start: int,
    end: int,
    titles: dict[str, str],
) -> list[tuple[int, str]]:
    starts: list[tuple[int, str]] = []
    for i in range(start, end):
        match = _SECTION_RE.match(lines[i])
        if match:
            number = _norm_number(match.group(1))
            if not titles or number in titles:
                starts.append((i, number))
    return starts


def _trim_next_heading(lines: list[str], next_title: str) -> list[str]:
    out = list(lines)
    while out and not _clean(out[-1]):
        out.pop()
    cleaned = [_clean(line) for line in out]
    for size in range(1, min(5, len(cleaned)) + 1):
        if _clean(" ".join(cleaned[-size:])) == next_title:
            del out[-size:]
            while out and not _clean(out[-1]):
                out.pop()
            while out:
                tail = _clean(out[-1])
                if not tail:
                    out.pop()
                    continue
                if tail.startswith("Chapter ") or tail.isupper():
                    out.pop()
                    continue
                break
            break
    return out


def _body_lines(lines: list[str]) -> list[str]:
    body: list[str] = []
    for line in lines:
        stripped = _clean(line)
        if not stripped or _PAGE_RE.match(stripped):
            continue
        body.append(stripped)
    return body


def parse_pdf_text(text: str) -> list[Section]:
    lines = text.replace("\f", "\n").splitlines()
    start = _body_start(lines)
    end = _body_end(lines, start)
    titles = _parse_toc_titles(lines, start)
    starts = _section_starts(lines, start, end, titles)
    sections: list[Section] = []
    for idx, (line_index, number) in enumerate(starts):
        next_index = starts[idx + 1][0] if idx + 1 < len(starts) else end
        next_title = titles.get(starts[idx + 1][1], "") if idx + 1 < len(starts) else ""
        segment = _trim_next_heading(lines[line_index:next_index], next_title)
        match = _SECTION_RE.match(segment[0])
        if not match:
            continue
        parts = [_clean(match.group(2))]
        parts.extend(_body_lines(segment[1:]))
        sections.append(Section(
            number=number,
            marginal_note=titles.get(number, ""),
            text=_clean(" ".join(parts)),
        ))
    return sections


def scrape_act(source_url: str, pdf_path: Optional[Path] = None) -> Act:
    with tempfile.TemporaryDirectory() as tmp:
        local_pdf = pdf_path or Path(tmp) / "act574.pdf"
        if pdf_path is None:
            _download(source_url, local_pdf)
        text = _pdftotext(local_pdf)
    return Act(
        act_code="MY_ACT574",
        title="Penal Code (Act 574)",
        url=source_url,
        scraped_at=_dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        source="agc_lom_pdf_2023",
        official_page=AGC_ACT_PAGE,
        as_at="2023-07-04",
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
    pa = sub.add_parser("act", help="scrape/parse Act 574 PDF into raw JSON")
    pa.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    pa.add_argument("--pdf", type=Path, help="already-downloaded PDF path")
    pa.add_argument("--out", required=True)
    args = parser.parse_args()
    {"act": cmd_act}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
