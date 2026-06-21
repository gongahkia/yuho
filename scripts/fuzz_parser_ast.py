"""Atheris harness for Parser.parse + ASTBuilder.build.

Run:
  uv run --with atheris python scripts/fuzz_parser_ast.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MAX_FUZZ_SOURCE_CHARS = 64_000
_PARSER = None
_AST_BUILDER = None


def _load_runtime():
    global _AST_BUILDER, _PARSER
    if _PARSER is None or _AST_BUILDER is None:
        from yuho.ast import ASTBuilder
        from yuho.parser.wrapper import Parser

        _PARSER = Parser()
        _AST_BUILDER = ASTBuilder
    return _PARSER, _AST_BUILDER


def fuzz_one_input(data: bytes) -> None:
    source = data.decode("utf-8", "ignore").replace("\x00", "")
    if len(source) > MAX_FUZZ_SOURCE_CHARS:
        source = source[:MAX_FUZZ_SOURCE_CHARS]

    parser, ast_builder = _load_runtime()

    result = parser.parse(source, file="<atheris>")
    if result.root_node is None or result.errors:
        return

    ast_builder(result.source, "<atheris>").build(result.root_node)


def main() -> int:
    try:
        import atheris
    except ImportError:
        print("missing atheris: run `uv run --with atheris python scripts/fuzz_parser_ast.py`")
        return 2

    with atheris.instrument_imports():
        _load_runtime()

    atheris.Setup(sys.argv, fuzz_one_input)
    atheris.Fuzz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
