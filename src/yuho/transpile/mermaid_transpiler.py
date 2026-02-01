"""
Mermaid transpiler - decision tree flowchart generation.

Converts match expressions to Mermaid flowchart diagrams.
"""

from typing import List, Optional, Dict, Set

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.transpile.base import TranspileTarget, TranspilerBase


class MermaidTranspiler(TranspilerBase, Visitor):
    """
    Transpile Yuho AST to Mermaid flowchart diagrams.

    Generates decision tree flowcharts from match expressions,
    with diamonds for conditions and rectangles for outcomes.
    """

    def __init__(self, direction: str = "TD", use_subgraphs: bool = True):
        """
        Initialize the Mermaid transpiler.

        Args:
            direction: Flowchart direction (TD=top-down, LR=left-right)
            use_subgraphs: Whether to wrap nested match expressions in subgraphs
        """
        self.direction = direction
        self.use_subgraphs = use_subgraphs
        self._output: List[str] = []
        self._node_counter = 0
        self._subgraph_counter = 0
        self._node_ids: Dict[int, str] = {}
        self._nesting_depth = 0  # Track nesting level for subgraph indentation

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.MERMAID

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to Mermaid diagram."""
        self._output = []
        self._node_counter = 0
        self._subgraph_counter = 0
        self._nesting_depth = 0

        # Header
        self._emit(f"flowchart {self.direction}")

        # Process each statute
        for statute in ast.statutes:
            self._transpile_statute(statute)

        # Process standalone match expressions in functions
        for func in ast.function_defs:
            self._transpile_function(func)

        return "\n".join(self._output)

    def _emit(self, line: str) -> None:
        """Add a line to output."""
        self._output.append(line)

    def _new_node_id(self, prefix: str = "N") -> str:
        """Generate a new unique node ID."""
        self._node_counter += 1
        return f"{prefix}{self._node_counter}"

    def _new_subgraph_id(self, name: str = "sub") -> str:
        """Generate a new unique subgraph ID."""
        self._subgraph_counter += 1
        return f"{name}_{self._subgraph_counter}"

    def _indent(self) -> str:
        """Get current indentation string based on nesting depth."""
        return "    " * (self._nesting_depth + 1)

    def _escape_text(self, text: str) -> str:
        """Escape text for Mermaid labels."""
        # Escape quotes and special chars
        text = text.replace('"', "'")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        # Truncate long text
        if len(text) > 50:
            text = text[:47] + "..."
        return text

    # =========================================================================
    # Statute processing
    # =========================================================================

    def _transpile_statute(self, statute: nodes.StatuteNode) -> None:
        """Generate flowchart for a statute."""
        title = statute.title.value if statute.title else statute.section_number
        self._emit(f"    %% Statute: {self._escape_text(title)}")

        # Start node
        start_id = self._new_node_id("START")
        self._emit(f"    {start_id}([Section {statute.section_number}])")

        # Process elements that contain match expressions
        prev_id = start_id
        for elem in statute.elements:
            if isinstance(elem.description, nodes.MatchExprNode):
                elem_start = self._new_node_id("ELEM")
                self._emit(f"    {elem_start}[/{elem.name}/]")
                self._emit(f"    {prev_id} --> {elem_start}")

                end_id = self._transpile_match_expr(elem.description, elem_start)
                prev_id = end_id
            else:
                elem_id = self._new_node_id("ELEM")
                label = self._escape_text(self._expr_to_label(elem.description))
                self._emit(f"    {elem_id}[{label}]")
                self._emit(f"    {prev_id} --> {elem_id}")
                prev_id = elem_id

        # Penalty outcome
        if statute.penalty:
            penalty_id = self._new_node_id("PENALTY")
            penalty_text = self._penalty_to_label(statute.penalty)
            self._emit(f"    {penalty_id}[[\"{self._escape_text(penalty_text)}\"]]")
            self._emit(f"    {prev_id} --> {penalty_id}")

        self._emit("")

    # =========================================================================
    # Function processing
    # =========================================================================

    def _transpile_function(self, func: nodes.FunctionDefNode) -> None:
        """Generate flowchart for function containing match expressions."""
        # Find match expressions in function body
        match_exprs = self._find_match_exprs(func.body)
        if not match_exprs:
            return

        self._emit(f"    %% Function: {func.name}")

        start_id = self._new_node_id("FN")
        params = ", ".join(p.name for p in func.params)
        self._emit(f"    {start_id}([{func.name}({params})])")

        prev_id = start_id
        for match_expr in match_exprs:
            end_id = self._transpile_match_expr(match_expr, prev_id)
            prev_id = end_id

        self._emit("")

    def _find_match_exprs(self, node: nodes.ASTNode) -> List[nodes.MatchExprNode]:
        """Find all match expressions in a node tree."""
        matches: List[nodes.MatchExprNode] = []

        if isinstance(node, nodes.MatchExprNode):
            matches.append(node)

        for child in node.children():
            matches.extend(self._find_match_exprs(child))

        return matches

    # =========================================================================
    # Match expression to flowchart
    # =========================================================================

    def _transpile_match_expr(
        self, 
        match: nodes.MatchExprNode, 
        start_id: str,
        subgraph_name: Optional[str] = None,
    ) -> str:
        """
        Generate flowchart nodes for a match expression.

        Returns the ID of the end/merge node.
        """
        # Check if this contains nested match expressions
        has_nested = any(
            isinstance(arm.body, nodes.MatchExprNode) 
            for arm in match.arms
        )
        
        # Use subgraph for nested match at depth > 0 or if explicitly named
        use_subgraph = (
            self.use_subgraphs and 
            (self._nesting_depth > 0 or subgraph_name is not None)
        )
        
        subgraph_id = None
        if use_subgraph:
            subgraph_id = self._new_subgraph_id("match")
            label = subgraph_name or "nested decision"
            self._emit(f"{self._indent()}subgraph {subgraph_id}[\"{self._escape_text(label)}\"]")
            self._nesting_depth += 1
        
        # Create decision node for scrutinee
        if match.scrutinee:
            scrutinee_label = self._expr_to_label(match.scrutinee)
            decision_id = self._new_node_id("D")
            self._emit(f"{self._indent()}{decision_id}{{{{{self._escape_text(scrutinee_label)}}}}}")
            self._emit(f"{self._indent()}{start_id} --> {decision_id}")
        else:
            decision_id = start_id

        # End node for merging
        end_id = self._new_node_id("END")

        # Process each arm
        for i, arm in enumerate(match.arms):
            arm_outcome_id = self._transpile_match_arm(arm, decision_id, i)
            self._emit(f"{self._indent()}{arm_outcome_id} --> {end_id}")

        # Create end node (circle for merge point)
        self._emit(f"{self._indent()}{end_id}((*))")
        
        # Close subgraph if opened
        if use_subgraph:
            self._nesting_depth -= 1
            self._emit(f"{self._indent()}end")

        return end_id

    def _transpile_match_arm(self, arm: nodes.MatchArm, from_id: str, index: int) -> str:
        """
        Generate nodes for a match arm.

        Returns the ID of the outcome node.
        """
        # Edge label from pattern
        pattern_label = self._pattern_to_label(arm.pattern)

        # If there's a guard, create intermediate decision node
        if arm.guard:
            guard_id = self._new_node_id("G")
            guard_label = self._expr_to_label(arm.guard)
            self._emit(f"{self._indent()}{guard_id}{{{{{self._escape_text(guard_label)}}}}}")
            self._emit(f"{self._indent()}{from_id} -->|\"{self._escape_text(pattern_label)}\"| {guard_id}")

            # Check if body is a nested match expression
            if isinstance(arm.body, nodes.MatchExprNode):
                # Generate subgraph for nested match
                nested_label = f"when {pattern_label} (guarded)"
                end_id = self._transpile_match_expr(arm.body, guard_id, nested_label)
                return end_id
            else:
                # True path goes to outcome
                outcome_id = self._new_node_id("O")
                body_label = self._expr_to_label(arm.body)
                self._emit(f"{self._indent()}{outcome_id}[\"{self._escape_text(body_label)}\"]")
                self._emit(f"{self._indent()}{guard_id} -->|\"Yes\"| {outcome_id}")
                return outcome_id
        else:
            # Check if body is a nested match expression
            if isinstance(arm.body, nodes.MatchExprNode):
                # Create a connector node for the nested match
                connector_id = self._new_node_id("C")
                self._emit(f"{self._indent()}{connector_id}((...))")  
                self._emit(f"{self._indent()}{from_id} -->|\"{self._escape_text(pattern_label)}\"| {connector_id}")
                
                # Generate subgraph for nested match
                nested_label = f"when {pattern_label}"
                end_id = self._transpile_match_expr(arm.body, connector_id, nested_label)
                return end_id
            else:
                # Direct path to outcome
                outcome_id = self._new_node_id("O")
                body_label = self._expr_to_label(arm.body)
                self._emit(f"{self._indent()}{outcome_id}[\"{self._escape_text(body_label)}\"]")
                self._emit(f"{self._indent()}{from_id} -->|\"{self._escape_text(pattern_label)}\"| {outcome_id}")
                return outcome_id

    # =========================================================================
    # Label generation helpers
    # =========================================================================

    def _expr_to_label(self, node: nodes.ASTNode) -> str:
        """Convert expression to label text."""
        if isinstance(node, nodes.IntLit):
            return str(node.value)
        elif isinstance(node, nodes.FloatLit):
            return str(node.value)
        elif isinstance(node, nodes.BoolLit):
            return "TRUE" if node.value else "FALSE"
        elif isinstance(node, nodes.StringLit):
            return node.value
        elif isinstance(node, nodes.MoneyNode):
            return f"${node.amount}"
        elif isinstance(node, nodes.PercentNode):
            return f"{node.value}%"
        elif isinstance(node, nodes.DateNode):
            return node.value.isoformat()
        elif isinstance(node, nodes.DurationNode):
            return str(node)
        elif isinstance(node, nodes.IdentifierNode):
            return node.name
        elif isinstance(node, nodes.FieldAccessNode):
            base = self._expr_to_label(node.base)
            return f"{base}.{node.field_name}"
        elif isinstance(node, nodes.IndexAccessNode):
            base = self._expr_to_label(node.base)
            index = self._expr_to_label(node.index)
            return f"{base}[{index}]"
        elif isinstance(node, nodes.FunctionCallNode):
            callee = self._expr_to_label(node.callee)
            args = ", ".join(self._expr_to_label(a) for a in node.args)
            return f"{callee}({args})"
        elif isinstance(node, nodes.BinaryExprNode):
            left = self._expr_to_label(node.left)
            right = self._expr_to_label(node.right)
            return f"{left} {node.operator} {right}"
        elif isinstance(node, nodes.UnaryExprNode):
            operand = self._expr_to_label(node.operand)
            return f"{node.operator}{operand}"
        elif isinstance(node, nodes.PassExprNode):
            return "pass"
        elif isinstance(node, nodes.MatchExprNode):
            return "[nested decision]"
        elif isinstance(node, nodes.StructLiteralNode):
            if node.struct_name:
                return f"new {node.struct_name}"
            return "{...}"
        else:
            return "?"

    def _pattern_to_label(self, pattern: nodes.PatternNode) -> str:
        """Convert pattern to edge label."""
        if isinstance(pattern, nodes.WildcardPattern):
            return "otherwise"
        elif isinstance(pattern, nodes.LiteralPattern):
            return self._expr_to_label(pattern.literal)
        elif isinstance(pattern, nodes.BindingPattern):
            return f"-> {pattern.name}"
        elif isinstance(pattern, nodes.StructPattern):
            fields = ", ".join(fp.name for fp in pattern.fields)
            return f"{pattern.type_name}{{{fields}}}"
        else:
            return "?"

    def _penalty_to_label(self, penalty: nodes.PenaltyNode) -> str:
        """Convert penalty to label text."""
        parts: List[str] = []

        if penalty.imprisonment_max:
            duration = str(penalty.imprisonment_max)
            parts.append(f"Imprisonment up to {duration}")

        if penalty.fine_max:
            parts.append(f"Fine up to ${penalty.fine_max.amount}")

        if penalty.supplementary:
            parts.append(penalty.supplementary.value)

        return "; ".join(parts) if parts else "Penalty TBD"
