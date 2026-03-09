"""E2E tests: parse library statutes through to evaluation."""
import pytest
from pathlib import Path
from yuho.eval.interpreter import Interpreter, Environment, Value
from yuho.ast.nodes import (
    StatuteNode, ElementNode, ElementGroupNode, StringLit,
    StructDefNode, FunctionDefNode,
)

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

    def test_statute_section_numbers_registered(self, statute_dir, parse_file):
        """Statute section numbers should be keys in env.statutes."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        interp = Interpreter()
        env = interp.interpret(ast)
        for statute in ast.statutes:
            assert statute.section_number in env.statutes
            retrieved = env.get_statute(statute.section_number)
            assert retrieved is not None
            assert retrieved.section_number == statute.section_number

    def test_struct_defs_populated(self, statute_dir, parse_file):
        """Struct definitions from statutes should be in env.struct_defs."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        interp = Interpreter()
        env = interp.interpret(ast)
        for sd in ast.type_defs:
            assert sd.name in env.struct_defs
            assert isinstance(env.struct_defs[sd.name], StructDefNode)
            assert len(env.struct_defs[sd.name].fields) == len(sd.fields)

    def test_statute_title_is_string(self, statute_dir, parse_file):
        """Every statute title should be a StringLit with non-empty value."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        for statute in ast.statutes:
            if statute.title is not None:
                assert isinstance(statute.title, StringLit)
                assert len(statute.title.value) > 0

    def test_statute_elements_have_valid_types(self, statute_dir, parse_file):
        """All leaf elements should have a recognised element_type."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        valid_types = {"actus_reus", "mens_rea", "circumstance"}
        ast = parse_file(statute_path)
        def _check_elements(members):
            for m in members:
                if isinstance(m, ElementNode):
                    assert m.element_type in valid_types, (
                        f"Unexpected element_type '{m.element_type}' for '{m.name}'"
                    )
                    assert len(m.name) > 0
                elif isinstance(m, ElementGroupNode):
                    assert m.combinator in ("all_of", "any_of")
                    _check_elements(m.members)
        for statute in ast.statutes:
            _check_elements(statute.elements)

    def test_environment_child_scope_isolation(self, parse_source):
        """Variables set in a child scope should not leak to the parent."""
        source = '''
struct Dummy { bool flag, }
statute 100 "Test" {
    elements {
        actus_reus act := "An act";
    }
}
'''
        ast = parse_source(source)
        interp = Interpreter()
        env = interp.interpret(ast)
        child = env.child()
        child.set("localVar", Value(42, "int"))
        assert child.get("localVar") is not None
        assert env.get("localVar") is None # parent unaffected

    def test_function_defs_have_correct_param_count(self, statute_dir, parse_file):
        """Registered function defs should match AST param counts."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        interp = Interpreter()
        env = interp.interpret(ast)
        for fd in ast.function_defs:
            registered = env.get_function_def(fd.name)
            assert registered is not None
            assert len(registered.params) == len(fd.params)

    def test_multiple_statutes_all_registered(self, parse_source):
        """Multiple statutes in a single module should all be registered."""
        source = '''
statute 101 "First" {
    elements { actus_reus a1 := "Act 1"; }
}
statute 102 "Second" {
    elements { actus_reus a2 := "Act 2"; }
}
'''
        ast = parse_source(source)
        interp = Interpreter()
        env = interp.interpret(ast)
        assert "101" in env.statutes
        assert "102" in env.statutes
        assert env.statutes["101"].title.value == "First"
        assert env.statutes["102"].title.value == "Second"
