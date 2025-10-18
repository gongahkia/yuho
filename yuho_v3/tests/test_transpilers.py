"""
Tests for Yuho Transpilers

Tests transpilation to Mermaid and Alloy formats.
"""

import pytest
from yuho_v3.parser import YuhoParser
from yuho_v3.transpilers.mermaid_transpiler import MermaidTranspiler
from yuho_v3.transpilers.alloy_transpiler import AlloyTranspiler


class TestMermaidTranspiler:
    """Test Mermaid diagram generation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.transpiler = MermaidTranspiler()

    def test_transpiler_initialization(self):
        """Test transpiler initializes correctly"""
        assert self.transpiler is not None

    def test_flowchart_empty_program(self):
        """Test flowchart generation for empty program"""
        ast = self.parser.parse("")
        result = self.transpiler.transpile_to_flowchart(ast)
        assert result is not None
        assert "flowchart TD" in result

    def test_flowchart_struct_definition(self):
        """Test flowchart for struct definition"""
        code = """
        struct Person {
            string name,
            int age
        }
        """
        ast = self.parser.parse(code)
        result = self.transpiler.transpile_to_flowchart(ast)
        assert "Person" in result

    def test_mindmap_empty_program(self):
        """Test mindmap generation for empty program"""
        ast = self.parser.parse("")
        result = self.transpiler.transpile_to_mindmap(ast)
        assert result is not None
        assert "mindmap" in result

    def test_mindmap_struct_definition(self):
        """Test mindmap for struct definition"""
        code = """
        struct Person {
            string name,
            int age
        }
        """
        ast = self.parser.parse(code)
        result = self.transpiler.transpile_to_mindmap(ast)
        assert "Person" in result

    def test_flowchart_match_case(self):
        """Test flowchart with match-case"""
        code = """
        match {
            case TRUE := consequence TRUE;
            case _ := consequence pass;
        }
        """
        ast = self.parser.parse(code)
        result = self.transpiler.transpile_to_flowchart(ast)
        assert "Decision" in result or "Match" in result


class TestAlloyTranspiler:
    """Test Alloy specification generation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.transpiler = AlloyTranspiler()

    def test_transpiler_initialization(self):
        """Test transpiler initializes correctly"""
        assert self.transpiler is not None

    def test_alloy_empty_program(self):
        """Test Alloy generation for empty program"""
        ast = self.parser.parse("")
        result = self.transpiler.transpile(ast)
        assert result is not None
        assert "module YuhoGenerated" in result

    def test_alloy_struct_definition(self):
        """Test Alloy for struct definition"""
        code = """
        struct Person {
            string name,
            int age
        }
        """
        ast = self.parser.parse(code)
        result = self.transpiler.transpile(ast)
        assert "sig Person" in result
        assert "name" in result
        assert "age" in result

    def test_alloy_has_bool_signatures(self):
        """Test that Alloy output includes boolean signatures"""
        ast = self.parser.parse("")
        result = self.transpiler.transpile(ast)
        assert "sig Bool" in result
        assert "True" in result
        assert "False" in result

    def test_alloy_match_case(self):
        """Test Alloy generation with match-case"""
        code = """
        match {
            case TRUE := consequence TRUE;
        }
        """
        ast = self.parser.parse(code)
        result = self.transpiler.transpile(ast)
        assert "pred" in result  # Should generate predicate


class TestTranspilerEdgeCases:
    """Test transpiler edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.mermaid = MermaidTranspiler()
        self.alloy = AlloyTranspiler()

    def test_mermaid_complex_program(self):
        """Test Mermaid with complex program"""
        code = """
        struct Person {
            string name,
            int age
        }
        
        int x := 42;
        
        match {
            case x > 0 := consequence TRUE;
            case _ := consequence pass;
        }
        """
        ast = self.parser.parse(code)
        flowchart = self.mermaid.transpile_to_flowchart(ast)
        mindmap = self.mermaid.transpile_to_mindmap(ast)
        
        assert flowchart is not None
        assert mindmap is not None

    def test_alloy_complex_program(self):
        """Test Alloy with complex program"""
        code = """
        struct Person {
            string name,
            int age,
            bool active
        }
        
        match {
            case TRUE := consequence TRUE;
        }
        """
        ast = self.parser.parse(code)
        result = self.alloy.transpile(ast)
        
        assert "sig Person" in result
        assert len(result) > 100  # Should be substantial output

