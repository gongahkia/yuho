"""Documentation contract tests for shipped CLI and DSL surfaces."""

from __future__ import annotations

import re
from pathlib import Path

from yuho.cli.main import cli


DOC_ROOTS = [
    Path(".github"),
    Path("docs"),
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
    reference = Path("docs/user/cli-reference.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"`yuho\s+([a-zA-Z0-9_-]+)", reference))

    assert documented
    assert documented.issubset(actual), sorted(documented - actual)


def test_dsl_docs_cover_new_constructs() -> None:
    """Syntax and semantics docs should mention the shipped advanced constructs."""
    syntax = Path("docs/researcher/syntax.md").read_text(encoding="utf-8")
    semantics = Path("docs/researcher/formal-semantics.md").read_text(encoding="utf-8")

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


def test_positioning_docs_are_linked() -> None:
    """Public honesty docs should stay discoverable."""
    readme = Path("README.md").read_text(encoding="utf-8")
    index = Path("docs/INDEX.md").read_text(encoding="utf-8")

    assert "docs/positioning/status-matrix.md" in readme
    assert "docs/researcher/canonical-semantics.md" in readme
    assert "researcher/canonical-semantics.md" in index
    assert "positioning/status-matrix.md" in index
    assert "positioning/comparisons.md" in index
    assert "contributor/expert-review-checklist.md" in index
    assert "faithful executable law" not in readme.lower()


def test_mechanisation_readme_states_claim_boundary() -> None:
    """Lean mechanisation docs should separate proof evidence from trust boundaries."""
    readme = Path("mechanisation/README.md").read_text(encoding="utf-8")

    for term in ("Proved", "Tested", "Trusted", "Out of scope"):
        assert f"| {term} |" in readme


def test_generic_docs_do_not_overstate_type_support() -> None:
    """Generic syntax docs should match the current erased implementation."""
    syntax = Path("docs/researcher/syntax.md").read_text(encoding="utf-8").lower()
    semantics = Path("docs/researcher/formal-semantics.md").read_text(
        encoding="utf-8"
    ).lower()

    assert "surface-only" in syntax
    assert "does not yet substitute" in syntax
    assert "runtime and export layers may erase" in syntax
    assert "generic type syntax is represented in the ast" in semantics
    assert "not fully" in semantics
    assert "erase or simplify type arguments" in semantics
    assert "strongly, statically-typed" not in syntax
