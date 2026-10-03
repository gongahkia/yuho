"""Validate the current Markdown surface and local links."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
             ROOT / "mechanisation/README.md", ROOT / "research/singapore/CORPUS-INDEX.md"]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def local_target(document: Path, target: str) -> Path:
    """Resolve a local link, including extensionless links to Markdown files."""
    relative = target.split("#", 1)[0].split("?", 1)[0]
    candidate = document.parent / relative
    if candidate.exists() or candidate.suffix:
        return candidate
    markdown = candidate.with_suffix(".md")
    return markdown if markdown.exists() else candidate


def main() -> None:
    checked = 0
    for document in DOCUMENTS:
        text = document.read_text(encoding="utf-8")
        assert text.startswith(("# ", "<h1 ")), document
        for target in LINK.findall(text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            if not target.split("#", 1)[0].split("?", 1)[0]:
                continue
            assert local_target(document, target).exists(), (document, target)
            checked += 1
    print(f"documentation: {len(DOCUMENTS)} current files, {checked} local links resolve")


if __name__ == "__main__":
    main()
