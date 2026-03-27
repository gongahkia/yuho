"""Documentation contract tests for shipped CLI and DSL surfaces."""

from __future__ import annotations

import re
from pathlib import Path

from yuho.cli.main import cli


DOC_ROOTS = [
    Path(".github"),
    Path("doc"),
    Path("library"),
]

CONSTRUCT_TERMS = ["legal_test", "conflict_check", "annotation"]


def _local_markdown_links(markdown_text: str) -> list[str]:
    """Return local markdown link targets from a markdown document."""
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown_text)
    return [
        target
        for target in targets
        if not target.startswith(("http://", "https://", "#", "mailto:"))
    ]


def test_documented_cli_commands_exist() -> None:
    """Every CLI command documented in the reference should be implemented."""
    actual = set(cli.commands.keys())
    reference = Path("doc/CLI_REFERENCE.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"`yuho\s+([a-zA-Z0-9_-]+)", reference))

    assert documented
    assert documented.issubset(actual), sorted(documented - actual)


def test_dsl_docs_cover_new_constructs() -> None:
    """Syntax and semantics docs should mention the shipped advanced constructs."""
    syntax = Path("doc/SYNTAX.md").read_text(encoding="utf-8")
    semantics = Path("doc/FORMAL_SEMANTICS.md").read_text(encoding="utf-8")

    for term in CONSTRUCT_TERMS:
        assert term in syntax
        assert term in semantics


def test_local_markdown_links_resolve() -> None:
    """All non-README local markdown links in docs should resolve."""
    missing: list[tuple[str, str]] = []

    for root in DOC_ROOTS:
        for md_path in root.rglob("*.md"):
            content = md_path.read_text(encoding="utf-8", errors="ignore")
            for target in _local_markdown_links(content):
                clean_target = target.split("#", 1)[0]
                if not clean_target:
                    continue
                resolved = (md_path.parent / clean_target).resolve()
                if not resolved.exists():
                    missing.append((str(md_path), target))

    assert not missing, missing
