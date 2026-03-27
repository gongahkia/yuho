"""Shared fixtures for E2E tests."""

import pytest
from pathlib import Path
from yuho.parser import get_parser
from yuho.ast import ASTBuilder
from yuho.ast.nodes import ModuleNode

LIBRARY_ROOT = Path(__file__).parent.parent.parent / "library" / "penal_code"
STATUTE_DIRS = sorted(LIBRARY_ROOT.glob("s*_*/")) if LIBRARY_ROOT.exists() else []


@pytest.fixture
def parser():
    return get_parser()


@pytest.fixture
def parse_source(parser):
    def _parse(source: str, filename: str = "<test>") -> ModuleNode:
        result = parser.parse(source, filename)
        builder = ASTBuilder(result.source, filename)
        return builder.build(result.root_node)

    return _parse


@pytest.fixture
def parse_file(parser):
    def _parse(path: Path) -> ModuleNode:
        result = parser.parse_file(path)
        builder = ASTBuilder(result.source, str(path))
        return builder.build(result.root_node)

    return _parse


@pytest.fixture(params=[str(d.name) for d in STATUTE_DIRS] if STATUTE_DIRS else ["skip"])
def statute_dir(request):
    if request.param == "skip":
        pytest.skip("No library statutes found")
    return LIBRARY_ROOT / request.param
