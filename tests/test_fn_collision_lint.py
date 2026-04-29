"""Tests for cross-module fn-name collision detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.ast import ASTBuilder
from yuho.ast.statute_lint import _check_fn_name_collisions, lint_module
from yuho.parser import get_parser

REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "library" / "penal_code"


def _parse(source: str):
    p = get_parser()
    pr = p.parse(source, file="<test>")
    return ASTBuilder(source, file="<test>").build(pr.root_node)


def test_no_collision_when_fn_names_unique():
    a = _parse("fn helper_a() : bool { match { case _ := consequence TRUE; } }")
    b = _parse("fn helper_b() : bool { match { case _ := consequence TRUE; } }")
    assert _check_fn_name_collisions([a, b]) == []


def test_collision_flagged_across_modules():
    a = _parse(
        "fn helper() : bool { match { case _ := consequence TRUE; } }\n"
        'statute 100 "x" effective 1872-01-01 { '
        'elements { actus_reus a := "a"; } '
        "penalty alternative { imprisonment := 0 years..1 years; } }"
    )
    b = _parse(
        "fn helper() : bool { match { case _ := consequence FALSE; } }\n"
        'statute 200 "y" effective 1872-01-01 { '
        'elements { actus_reus a := "a"; } '
        "penalty alternative { imprisonment := 0 years..1 years; } }"
    )
    warnings = _check_fn_name_collisions([a, b])
    assert len(warnings) == 1
    assert "helper" in warnings[0].message
    assert "100" in warnings[0].message  # cites first-seen section
    assert warnings[0].severity == "warning"


def test_lint_module_includes_collision_check():
    """lint_module should pick up collisions when handed referenced modules."""
    main = _parse("fn helper() : bool { match { case _ := consequence TRUE; } }")
    other = _parse("fn helper() : bool { match { case _ := consequence FALSE; } }")
    warnings = lint_module(main, referenced_modules=[other])
    msgs = [w.message for w in warnings]
    assert any("helper" in m and "collides" in m for m in msgs)


def test_lint_module_no_referenced_modules_means_no_collision():
    """A bare module with no closure can't have cross-module collisions."""
    m = _parse("fn helper() : bool { match { case _ := consequence TRUE; } }")
    # any warnings emitted must not be collision-related
    msgs = [w.message for w in lint_module(m)]
    assert not any("collides" in m for m in msgs)


def test_corpus_has_no_residual_fn_collisions():
    """Regression: after the 2026-04-29 prefix sweep, the live corpus must
    stay free of duplicate top-level `fn` names. New collisions surface
    here so the manual prefix policy doesn't drift."""
    if not LIBRARY.is_dir():
        pytest.skip("penal_code library not available")
    parser = get_parser()
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    for stat_path in sorted(LIBRARY.glob("*/statute.yh")):
        source = stat_path.read_text(encoding="utf-8")
        pr = parser.parse(source, file=str(stat_path))
        if pr.root_node is None:
            continue
        ast = ASTBuilder(source, file=str(stat_path)).build(pr.root_node)
        for fn in ast.function_defs:
            if fn.name in seen and seen[fn.name] != stat_path.parent.name:
                duplicates.append((fn.name, seen[fn.name], stat_path.parent.name))
            else:
                seen[fn.name] = stat_path.parent.name
    assert duplicates == [], (
        "fn name collisions in penal_code corpus — prefix with section number:\n  "
        + "\n  ".join(f"{n} in {a} and {b}" for n, a, b in duplicates)
    )
