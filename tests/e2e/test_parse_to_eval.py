"""E2E tests: parse library statutes through to evaluation."""
import pytest
from pathlib import Path
from yuho.eval.interpreter import Interpreter, Environment

class TestParseToEval:
    def test_statute_parses_cleanly(self, statute_dir, parse_file):
        """Every library statute should parse without errors."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip(f"No statute.yh in {statute_dir}")
        ast = parse_file(statute_path)
        assert ast is not None
        assert len(ast.statutes) > 0

    def test_statute_has_elements(self, statute_dir, parse_file):
        """Every statute should have at least one element."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        for statute in ast.statutes:
            assert len(statute.elements) > 0, f"Section {statute.section_number} has no elements"

    def test_interpreter_loads_statute(self, statute_dir, parse_file):
        """Interpreter should load statute definitions."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        interp = Interpreter()
        env = interp.interpret(ast)
        assert len(env.statutes) > 0

    def test_functions_callable(self, statute_dir, parse_file):
        """Functions defined in statutes should be callable."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        interp = Interpreter()
        env = interp.interpret(ast)
        # verify functions are registered
        for fn in ast.function_defs:
            assert env.get_function_def(fn.name) is not None
