"""
Mermaid Transpiler for Yuho
Generates Mermaid diagrams from Yuho AST
"""

from typing import List, Dict, Any
from ..ast_nodes import *

class MermaidTranspiler:
    """Transpiles Yuho AST to Mermaid diagram syntax"""

    def __init__(self):
        self.output = []
        self.node_counter = 0

    def transpile_to_flowchart(self, program: Program) -> str:
        """
        Generate Mermaid flowchart from Yuho program

        Args:
            program: Yuho Program AST

        Returns:
            Mermaid flowchart syntax
        """
        self.output = ["flowchart TD"]
        self.node_counter = 0

        for stmt in program.statements:
            self._process_statement_flowchart(stmt)

        return "\\n".join(self.output)

    def transpile_to_mindmap(self, program: Program) -> str:
        """
        Generate Mermaid mindmap from Yuho program

        Args:
            program: Yuho Program AST

        Returns:
            Mermaid mindmap syntax
        """
        self.output = ["mindmap"]
        self.node_counter = 0

        # Find main structs and their relationships
        structs = [stmt for stmt in program.statements if isinstance(stmt, StructDefinition)]
        match_cases = [stmt for stmt in program.statements if isinstance(stmt, MatchCase)]

        if structs:
            main_struct = structs[0]  # Use first struct as root
            self.output.append(f"  root((({main_struct.name})))")

            # Add struct members as branches
            for member in main_struct.members:
                self.output.append(f"    {member.name}")
                self.output.append(f"      {self.get_type_from_node(member.type_node)}")

        # Add match cases as decision branches
        for match_case in match_cases:
            self.output.append(f"    Decisions")
            for i, case in enumerate(match_case.cases):
                if case.condition:
                    self.output.append(f"      Case{i + 1}")
                else:
                    self.output.append(f"      Default")

        return "\\n".join(self.output)

    def _process_statement_flowchart(self, stmt: Statement):
        """Process a statement for flowchart generation"""
        if isinstance(stmt, StructDefinition):
            self._add_struct_flowchart(stmt)
        elif isinstance(stmt, MatchCase):
            self._add_match_case_flowchart(stmt)
        elif isinstance(stmt, Declaration):
            self._add_declaration_flowchart(stmt)

    def _add_struct_flowchart(self, struct: StructDefinition):
        """Add struct definition to flowchart"""
        struct_id = f"S{self.node_counter}"
        self.node_counter += 1

        # Main struct node
        self.output.append(f"    {struct_id}[{struct.name}]")

        # Add member nodes
        for member in struct.members:
            member_id = f"M{self.node_counter}"
            self.node_counter += 1

            self.output.append(f"    {member_id}[{member.name}: {self.get_type_from_node(member.type_node)}]")
            self.output.append(f"    {struct_id} --> {member_id}")

    def _add_match_case_flowchart(self, match_case: MatchCase):
        """Add match-case to flowchart"""
        match_id = f"MC{self.node_counter}"
        self.node_counter += 1

        # Decision diamond
        condition_text = "Decision"
        if match_case.expression:
            condition_text = f"Match Expression"

        self.output.append(f"    {match_id}{{{condition_text}}}")

        # Add case branches
        for i, case in enumerate(match_case.cases):
            case_id = f"C{self.node_counter}"
            self.node_counter += 1

            if case.condition:
                case_text = f"Case {i + 1}"
            else:
                case_text = "Default"

            self.output.append(f"    {case_id}[{case_text}]")
            self.output.append(f"    {match_id} --> {case_id}")

            # Add consequence
            if not isinstance(case.consequence, PassStatement):
                cons_id = f"CO{self.node_counter}"
                self.node_counter += 1
                self.output.append(f"    {cons_id}[Consequence]")
                self.output.append(f"    {case_id} --> {cons_id}")

    def _add_declaration_flowchart(self, decl: Declaration):
        """Add declaration to flowchart"""
        decl_id = f"D{self.node_counter}"
        self.node_counter += 1

        decl_text = f"{decl.name}: {self.get_type_from_node(decl.type_node)}"
        self.output.append(f"    {decl_id}[{decl_text}]")

    def get_type_from_node(self, type_node: TypeNode) -> str:
        """Extract type string from TypeNode"""
        if isinstance(type_node.type_name, YuhoType):
            return type_node.type_name.value
        return str(type_node.type_name)