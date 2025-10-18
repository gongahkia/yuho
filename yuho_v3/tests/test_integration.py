"""
Integration Tests for Yuho

End-to-end tests that validate the complete workflow from parsing to transpilation.
"""

import pytest
import os
import tempfile
from pathlib import Path
from yuho_v3.parser import YuhoParser
from yuho_v3.semantic_analyzer import SemanticAnalyzer
from yuho_v3.transpilers.mermaid_transpiler import MermaidTranspiler
from yuho_v3.transpilers.alloy_transpiler import AlloyTranspiler


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()
        self.mermaid = MermaidTranspiler()
        self.alloy = AlloyTranspiler()

    def test_complete_workflow_simple_struct(self):
        """Test complete workflow with simple struct"""
        code = """
        struct Person {
            string name,
            int age
        }
        """
        
        # Parse
        ast = self.parser.parse(code)
        assert ast is not None
        
        # Analyze
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0
        
        # Transpile to Mermaid
        flowchart = self.mermaid.transpile_to_flowchart(ast)
        assert flowchart is not None
        assert len(flowchart) > 0
        
        # Transpile to Alloy
        alloy_spec = self.alloy.transpile(ast)
        assert alloy_spec is not None
        assert len(alloy_spec) > 0

    def test_complete_workflow_with_logic(self):
        """Test complete workflow with logical constructs"""
        code = """
        struct Cheating {
            string accused,
            string victim,
            bool deception,
            bool harm
        }
        
        match {
            case TRUE := consequence TRUE;
            case _ := consequence pass;
        }
        """
        
        # Parse
        ast = self.parser.parse(code)
        assert ast is not None
        
        # Analyze
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0
        
        # Transpile
        flowchart = self.mermaid.transpile_to_flowchart(ast)
        alloy_spec = self.alloy.transpile(ast)
        
        assert "Cheating" in flowchart
        assert "Cheating" in alloy_spec


class TestFileBasedWorkflow:
    """Test workflows with actual files"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_parse_file_simple(self):
        """Test parsing from a file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yh', delete=False) as f:
            f.write('int x := 42;')
            temp_file = f.name
        
        try:
            ast = self.parser.parse_file(temp_file)
            assert ast is not None
            assert len(ast.statements) == 1
        finally:
            os.unlink(temp_file)

    def test_parse_file_complex(self):
        """Test parsing complex file"""
        code = """
        // This is a comment
        struct Person {
            string name,
            int age,
            bool active
        }
        
        int count := 10;
        
        match {
            case count > 5 := consequence TRUE;
            case _ := consequence FALSE;
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yh', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            ast = self.parser.parse_file(temp_file)
            errors = self.analyzer.analyze(ast)
            
            assert ast is not None
            assert len(ast.statements) >= 3
            assert len(errors) == 0
        finally:
            os.unlink(temp_file)


class TestRealWorldExamples:
    """Test with real-world example patterns"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()
        self.mermaid = MermaidTranspiler()
        self.alloy = AlloyTranspiler()

    def test_legal_statute_pattern(self):
        """Test typical legal statute representation pattern"""
        code = """
        struct Offense {
            string accused,
            string action,
            string victim,
            bool intentional,
            bool harm
        }
        
        match {
            case intentional && harm := consequence "guilty";
            case _ := consequence "not guilty";
        }
        """
        
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        
        assert len(errors) == 0
        
        flowchart = self.mermaid.transpile_to_flowchart(ast)
        alloy_spec = self.alloy.transpile(ast)
        
        assert "Offense" in flowchart
        assert "Offense" in alloy_spec

    def test_multiple_conditions_pattern(self):
        """Test pattern with multiple conditions"""
        code = """
        struct Case {
            bool conditionA,
            bool conditionB,
            bool conditionC
        }
        
        match {
            case conditionA && conditionB && conditionC := consequence TRUE;
            case conditionA && conditionB := consequence TRUE;
            case conditionA := consequence TRUE;
            case _ := consequence FALSE;
        }
        """
        
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        
        assert len(errors) == 0


class TestErrorRecovery:
    """Test error handling and recovery in workflows"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_syntax_error_handling(self):
        """Test that syntax errors are properly caught"""
        code = "int x = 42;"  # Wrong syntax
        
        with pytest.raises(SyntaxError):
            self.parser.parse(code)

    def test_semantic_error_collection(self):
        """Test that semantic errors are collected"""
        code = """
        int x := 1;
        int x := 2;
        """
        
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        
        assert len(errors) > 0

    def test_type_error_collection(self):
        """Test that type errors are collected"""
        code = 'int x := "not an integer";'
        
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        
        assert len(errors) > 0


class TestPerformance:
    """Basic performance tests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_large_struct_performance(self):
        """Test performance with large struct"""
        # Generate a struct with many fields
        fields = [f"string field{i}," for i in range(100)]
        code = f"""
        struct LargeStruct {{
            {' '.join(fields)}
            int lastField
        }}
        """
        
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        
        assert len(errors) == 0

    def test_many_statements_performance(self):
        """Test performance with many statements"""
        # Generate many variable declarations
        statements = [f"int var{i} := {i};" for i in range(100)]
        code = '\n'.join(statements)
        
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        
        assert len(errors) == 0

