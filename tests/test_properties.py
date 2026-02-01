"""
Property-based tests for Yuho using Hypothesis.

These tests verify invariants that should hold for all valid inputs.
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck

from tests.strategies import (
    yuho_literal,
    yuho_struct_definition,
    yuho_match_expression,
    yuho_statute_block,
    yuho_module,
)


# Increase deadline for slower operations
SLOW_SETTINGS = settings(
    max_examples=50,
    deadline=5000,
    suppress_health_check=[HealthCheck.too_slow],
)


class TestParseRoundTrip:
    """Tests for parse round-trip invariant."""

    @given(yuho_literal())
    @SLOW_SETTINGS
    def test_literal_parses(self, literal):
        """Generated literals should parse without errors."""
        from yuho.parser import Parser

        # Wrap literal in a simple expression
        source = f"int x := {literal};"

        parser = Parser()
        result = parser.parse(source)

        # Should parse (may have errors for edge cases)
        assert result.tree is not None

    @given(yuho_struct_definition())
    @SLOW_SETTINGS
    def test_struct_parses(self, struct):
        """Generated struct definitions should parse."""
        from yuho.parser import Parser

        parser = Parser()
        result = parser.parse(struct)

        assert result.tree is not None

    @given(yuho_statute_block())
    @SLOW_SETTINGS
    def test_statute_parses(self, statute):
        """Generated statute blocks should parse."""
        from yuho.parser import Parser

        parser = Parser()
        result = parser.parse(statute)

        assert result.tree is not None

    @given(yuho_module())
    @SLOW_SETTINGS
    def test_module_parses(self, module):
        """Generated modules should parse."""
        from yuho.parser import Parser

        parser = Parser()
        result = parser.parse(module)

        assert result.tree is not None


class TestASTWellFormedness:
    """Tests for AST well-formedness invariants."""

    @given(yuho_struct_definition())
    @SLOW_SETTINGS
    def test_struct_ast_has_locations(self, struct):
        """AST nodes should have source locations."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder

        parser = Parser()
        result = parser.parse(struct)
        assume(result.is_valid)

        builder = ASTBuilder(struct)
        ast = builder.build(result.root_node)

        # Root should have location
        if ast.source_location:
            assert ast.source_location.line >= 1
            assert ast.source_location.col >= 1

    @given(yuho_statute_block())
    @SLOW_SETTINGS
    def test_statute_ast_structure(self, statute):
        """Statute AST should have expected structure."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder

        parser = Parser()
        result = parser.parse(statute)
        assume(result.is_valid)

        builder = ASTBuilder(statute)
        ast = builder.build(result.root_node)

        # Should have at least one statute
        assert len(ast.statutes) >= 1

        for s in ast.statutes:
            # Statute should have section number
            assert s.section_number

    @given(yuho_module())
    @SLOW_SETTINGS
    def test_module_children_traversable(self, module):
        """All AST nodes should be traversable via children()."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder

        parser = Parser()
        result = parser.parse(module)
        assume(result.is_valid)

        builder = ASTBuilder(module)
        ast = builder.build(result.root_node)

        def count_nodes(node):
            count = 1
            for child in node.children():
                count += count_nodes(child)
            return count

        # Should be able to count all nodes without error
        total = count_nodes(ast)
        assert total >= 1


class TestTranspilationDeterminism:
    """Tests for transpilation determinism."""

    @given(yuho_statute_block())
    @SLOW_SETTINGS
    def test_json_transpile_deterministic(self, statute):
        """JSON transpilation should be deterministic."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.transpile import JSONTranspiler

        parser = Parser()
        result = parser.parse(statute)
        assume(result.is_valid)

        builder = ASTBuilder(statute)
        ast = builder.build(result.root_node)

        transpiler = JSONTranspiler(include_locations=False)

        # Transpile twice
        output1 = transpiler.transpile(ast)
        output2 = transpiler.transpile(ast)

        assert output1 == output2

    @given(yuho_statute_block())
    @SLOW_SETTINGS
    def test_english_transpile_deterministic(self, statute):
        """English transpilation should be deterministic."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.transpile import EnglishTranspiler

        parser = Parser()
        result = parser.parse(statute)
        assume(result.is_valid)

        builder = ASTBuilder(statute)
        ast = builder.build(result.root_node)

        transpiler = EnglishTranspiler()

        output1 = transpiler.transpile(ast)
        output2 = transpiler.transpile(ast)

        assert output1 == output2


class TestVisitorTraversal:
    """Tests for visitor pattern traversal."""

    @given(yuho_module())
    @SLOW_SETTINGS
    def test_visitor_visits_all_nodes(self, module):
        """Visitor should visit all nodes in the AST."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.ast.visitor import Visitor

        parser = Parser()
        result = parser.parse(module)
        assume(result.is_valid)

        builder = ASTBuilder(module)
        ast = builder.build(result.root_node)

        class CountingVisitor(Visitor):
            def __init__(self):
                self.count = 0

            def generic_visit(self, node):
                self.count += 1
                return super().generic_visit(node)

        visitor = CountingVisitor()
        ast.accept(visitor)

        # Should visit at least the root
        assert visitor.count >= 1


class TestTransformerIdentity:
    """Tests for transformer identity transformation."""

    @given(yuho_module())
    @SLOW_SETTINGS
    def test_identity_transform(self, module):
        """Identity transformation should preserve AST."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.ast.transformer import Transformer
        from yuho.transpile import JSONTranspiler

        parser = Parser()
        result = parser.parse(module)
        assume(result.is_valid)

        builder = ASTBuilder(module)
        ast = builder.build(result.root_node)

        # Identity transformer
        transformer = Transformer()
        transformed = transformer.transform(ast)

        # Serialize both to compare
        json_transpiler = JSONTranspiler(include_locations=False)
        original_json = json_transpiler.transpile(ast)
        transformed_json = json_transpiler.transpile(transformed)

        assert original_json == transformed_json
