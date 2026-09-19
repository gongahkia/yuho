"""Validate the current Markdown surface and local links."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [ROOT / "README.md", ROOT / "CHANGELOG.md", ROOT / "SECURITY.md",
             ROOT / ".github/CONTRIBUTING.md", *sorted((ROOT / "docs").glob("*.md")),
             ROOT / "mechanisation/README.md", ROOT / "research/singapore/CORPUS-INDEX.md"]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> None:
    checked = 0
    for document in DOCUMENTS:
        text = document.read_text(encoding="utf-8")
        assert text.startswith(("# ", "<h1 ")), document
        for target in LINK.findall(text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            relative = target.split("#", 1)[0].split("?", 1)[0]
            if not relative:
                continue
            assert (document.parent / relative).exists(), (document, target)
            checked += 1
    print(f"documentation: {len(DOCUMENTS)} current files, {checked} local links resolve")


if __name__ == "__main__":
    main()
