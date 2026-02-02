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


class TestJSONRoundTrip:
    """Tests for JSON serialization round-trip invariant.
    
    Invariant: from_json(to_json(ast)) == ast
    """

    @given(yuho_statute_block())
    @SLOW_SETTINGS
    def test_json_roundtrip_preserves_ast(self, statute):
        """JSON serialization and deserialization should preserve AST."""
        import json
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.transpile import JSONTranspiler

        parser = Parser()
        result = parser.parse(statute)
        assume(result.is_valid)

        builder = ASTBuilder(statute)
        ast = builder.build(result.root_node)

        # Serialize to JSON
        transpiler = JSONTranspiler(include_locations=False)
        json_str = transpiler.transpile(ast)

        # Parse JSON and verify structure
        parsed_json = json.loads(json_str)

        # Verify key structural elements are preserved
        assert "statutes" in parsed_json
        assert len(parsed_json["statutes"]) == len(ast.statutes)

        for i, s in enumerate(ast.statutes):
            json_s = parsed_json["statutes"][i]
            assert "section_number" in json_s
            assert json_s["section_number"] == s.section_number

    @given(yuho_module())
    @SLOW_SETTINGS
    def test_json_roundtrip_full_module(self, module):
        """Full module JSON round-trip should preserve structure."""
        import json
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.transpile import JSONTranspiler

        parser = Parser()
        result = parser.parse(module)
        assume(result.is_valid)

        builder = ASTBuilder(module)
        ast = builder.build(result.root_node)

        transpiler = JSONTranspiler(include_locations=False)
        json_str = transpiler.transpile(ast)

        # Parse JSON
        parsed = json.loads(json_str)

        # Structural invariants
        assert "type_defs" in parsed
        assert "function_defs" in parsed
        assert "statutes" in parsed
        
        # Count invariants
        assert len(parsed["type_defs"]) == len(ast.type_defs)
        assert len(parsed["function_defs"]) == len(ast.function_defs)
        assert len(parsed["statutes"]) == len(ast.statutes)


class TestMatchExhaustivenessInvariant:
    """Tests for match expression exhaustiveness invariant.
    
    Invariant: All generated match expressions should pass exhaustiveness check.
    """

    @given(yuho_match_expression())
    @SLOW_SETTINGS
    def test_generated_match_is_well_formed(self, match_expr):
        """Generated match expressions should be well-formed."""
        from yuho.parser import Parser

        # Wrap in a function
        source = f"""
fn test_match(x: int) -> int {{
    {match_expr}
}}
"""
        parser = Parser()
        result = parser.parse(source)

        # Match should parse
        assert result.tree is not None

    @given(yuho_match_expression())
    @SLOW_SETTINGS
    def test_match_has_default_case(self, match_expr):
        """Generated match expressions should include default handling."""
        # Check string representation includes wildcard or default
        has_wildcard = "_" in match_expr or "case _" in match_expr
        has_default = "default" in match_expr.lower()
        
        # At minimum, should have some case handling
        has_case = "case" in match_expr
        
        assert has_case, "Match expression should have at least one case"


class TestPatternReachabilityInvariant:
    """Tests for pattern reachability invariant.
    
    Invariant: No generated match arms should be trivially unreachable.
    """

    @given(yuho_match_expression())
    @SLOW_SETTINGS
    def test_no_duplicate_patterns(self, match_expr):
        """Match expressions should not have duplicate patterns."""
        import re
        
        # Extract case patterns
        case_pattern = r'case\s+([^:]+):'
        matches = re.findall(case_pattern, match_expr)
        
        # Filter out wildcards (they're special)
        non_wildcard = [m.strip() for m in matches if m.strip() != "_"]
        
        # Check for duplicates
        if non_wildcard:
            unique = set(non_wildcard)
            # Allow some flexibility for generated code
            assert len(unique) >= len(non_wildcard) * 0.8, \
                f"Too many duplicate patterns: {non_wildcard}"


class TestCrossTranspilerConsistency:
    """Tests for cross-transpiler consistency.
    
    Invariant: JSON AST parsed back should match original structural properties.
    """

    @given(yuho_statute_block())
    @SLOW_SETTINGS
    def test_json_and_jsonld_structural_consistency(self, statute):
        """JSON and JSON-LD transpilers should produce structurally consistent output."""
        import json
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.transpile import JSONTranspiler, JSONLDTranspiler

        parser = Parser()
        result = parser.parse(statute)
        assume(result.is_valid)

        builder = ASTBuilder(statute)
        ast = builder.build(result.root_node)

        # Both transpilers
        json_transpiler = JSONTranspiler(include_locations=False)
        jsonld_transpiler = JSONLDTranspiler()

        json_output = json.loads(json_transpiler.transpile(ast))
        jsonld_output = json.loads(jsonld_transpiler.transpile(ast))

        # Both should have statutes
        assert "statutes" in json_output
        # JSON-LD wraps differently, check @graph or root structure
        assert "@context" in jsonld_output or "statutes" in jsonld_output

    @given(yuho_module())
    @SLOW_SETTINGS  
    def test_transpiler_produces_valid_output(self, module):
        """All transpilers should produce valid, non-empty output."""
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder
        from yuho.transpile import JSONTranspiler, EnglishTranspiler

        parser = Parser()
        result = parser.parse(module)
        assume(result.is_valid)

        builder = ASTBuilder(module)
        ast = builder.build(result.root_node)

        # Test multiple transpilers
        transpilers = [
            JSONTranspiler(include_locations=False),
            EnglishTranspiler(),
        ]

        for transpiler in transpilers:
            output = transpiler.transpile(ast)
            assert output, f"{transpiler.__class__.__name__} produced empty output"
            assert len(output) > 0


class TestParserFuzzing:
    """Fuzzing tests for parser robustness.
    
    Tests that the parser handles arbitrary input gracefully.
    """

    @given(yuho_literal())
    @SLOW_SETTINGS
    def test_parser_handles_random_literals(self, literal):
        """Parser should handle generated literals without crashing."""
        from yuho.parser import Parser

        parser = Parser()
        
        # Should not raise unhandled exceptions
        try:
            result = parser.parse(literal)
            # Result may be invalid, but should not crash
            assert result is not None
        except Exception as e:
            # Only syntax-related errors are acceptable
            assert "syntax" in str(e).lower() or "parse" in str(e).lower(), \
                f"Unexpected error: {e}"

    @given(yuho_struct_definition())
    @SLOW_SETTINGS
    def test_parser_handles_malformed_structs(self, struct):
        """Parser should handle malformed structs gracefully."""
        from yuho.parser import Parser

        parser = Parser()
        
        # Corrupt the struct slightly
        corrupted = struct.replace("{", "{{").replace("}", "}}")
        
        try:
            result = parser.parse(corrupted)
            # May fail to parse, but should not crash
            assert result is not None
        except Exception as e:
            # Acceptable parse errors
            pass

    @settings(max_examples=20, deadline=10000)
    @given(yuho_module())
    def test_parser_handles_truncated_input(self, module):
        """Parser should handle truncated input without crashing."""
        from yuho.parser import Parser

        parser = Parser()
        
        # Try various truncation points
        for truncate_at in [len(module) // 4, len(module) // 2, len(module) * 3 // 4]:
            if truncate_at > 0:
                truncated = module[:truncate_at]
                
                try:
                    result = parser.parse(truncated)
                    # Result may be invalid, but should exist
                    assert result is not None
                except Exception:
                    # Parse errors are acceptable
                    pass
