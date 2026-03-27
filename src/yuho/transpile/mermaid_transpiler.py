"""
Mermaid transpiler - decision tree flowchart generation.

Converts match expressions to Mermaid flowchart diagrams.
"""

from typing import Dict, List, Optional

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
        self.direction = direction
        self.use_subgraphs = use_subgraphs
        self._output: List[str] = []
        self._node_counter = 0
        self._subgraph_counter = 0
        self._node_ids: Dict[int, str] = {}
        self._element_nodes: Dict[str, str] = {}
        self._nesting_depth = 0

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.MERMAID

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to Mermaid diagram."""
        self._output = []
        self._node_counter = 0
        self._subgraph_counter = 0
        self._element_nodes = {}
        self._nesting_depth = 0
        self._emit(f"flowchart {self.direction}")
        for statute in ast.statutes:
            self._transpile_statute(statute)
        for func in ast.function_defs:
            self._transpile_function(func)
        return "\n".join(self._output)

    def _emit(self, line: str) -> None:
        self._output.append(line)

    def _new_node_id(self, prefix: str = "N") -> str:
        self._node_counter += 1
        return f"{prefix}{self._node_counter}"

    def _new_subgraph_id(self, name: str = "sub") -> str:
        self._subgraph_counter += 1
        return f"{name}_{self._subgraph_counter}"

    def _indent(self) -> str:
        return "    " * (self._nesting_depth + 1)

    def _q(self, text: str) -> str:
        """Quote and escape text for Mermaid node labels."""
        text = text.replace('"', "'")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        if len(text) > 80:
            text = text[:77] + "..."
        return f'"{text}"'

    # =========================================================================
    # Statute processing
    # =========================================================================

    def _transpile_statute(self, statute: nodes.StatuteNode) -> None:
        """Generate flowchart for a statute."""
        title = statute.title.value if statute.title else statute.section_number
        self._emit(f"    %% Statute: {title}")
        start_id = self._new_node_id("START")
        start_label = f"Section {statute.section_number}: {title}"
        meta_parts = []
        if getattr(statute, "effective_date", None):
            meta_parts.append(f"eff: {statute.effective_date}")
        if getattr(statute, "repealed_date", None):
            meta_parts.append(f"repealed: {statute.repealed_date}")
        if getattr(statute, "subsumes", None):
            meta_parts.append(f"subsumes s{statute.subsumes}")
        if meta_parts:
            start_label += f" ({', '.join(meta_parts)})"
        self._emit(f"    {start_id}([{self._q(start_label)}])")
        prev_id = start_id
        for elem in statute.elements:
            if isinstance(elem, nodes.ElementGroupNode):
                prev_id = self._transpile_element_group(elem, prev_id)
            elif isinstance(elem.description, nodes.MatchExprNode):
                elem_start = self._new_node_id("ELEM")
                prefix = self._deontic_prefix(elem.element_type)
                self._emit(f"    {elem_start}[/{self._q(prefix + elem.name)}/]")
                self._emit(f"    {prev_id} --> {elem_start}")
                self._element_nodes[elem.name] = elem_start
                prev_id = self._transpile_match_expr(elem.description, elem_start)
            else:
                elem_id = self._new_node_id("ELEM")
                prefix = self._deontic_prefix(elem.element_type)
                label = prefix + self._expr_to_label(elem.description)
                suffix = self._element_suffix(elem)
                if suffix:
                    label += f" {suffix}"
                self._emit(f"    {elem_id}[{self._q(label)}]")
                self._emit(f"    {prev_id} --> {elem_id}")
                self._element_nodes[elem.name] = elem_id
                prev_id = elem_id
        if statute.exceptions:
            exc_id = self._new_node_id("EXC")
            self._emit(f"    {exc_id}{{{{{self._q('Exceptions / defences')}}}}}")
            self._emit(f"    {prev_id} --> {exc_id}")
            no_exc_id = self._new_node_id("NOEXC")
            self._emit(f"    {no_exc_id}[{self._q('No exception defeats liability')}]")
            self._emit(f"    {exc_id} -->|{self._q('None')}| {no_exc_id}")
            for exc in statute.exceptions:
                exc_out_id = self._new_node_id("EXCOUT")
                label = exc.label or "exception"
                effect = self._exception_outcome_label(exc)
                self._emit(f"    {exc_out_id}[{self._q(effect)}]")
                self._emit(f"    {exc_id} -->|{self._q(label)}| {exc_out_id}")
            prev_id = no_exc_id
        if statute.penalty:
            penalty_id = self._new_node_id("PENALTY")
            penalty_text = self._penalty_to_label(statute.penalty)
            self._emit(f"    {penalty_id}[[{self._q(penalty_text)}]]")
            self._emit(f"    {prev_id} --> {penalty_id}")
            prev_id = penalty_id
        self._emit_provenance_nodes(statute, start_id=start_id, fallback_id=prev_id)
        self._emit("")

    # =========================================================================
    # Function processing
    # =========================================================================

    def _transpile_function(self, func: nodes.FunctionDefNode) -> None:
        """Generate flowchart for function containing match expressions."""
        match_exprs = self._find_match_exprs(func.body)
        if not match_exprs:
            return
        self._emit(f"    %% Function: {func.name}")
        start_id = self._new_node_id("FN")
        params = ", ".join(p.name for p in func.params)
        self._emit(f"    {start_id}([{self._q(f'{func.name}({params})')}])")
        prev_id = start_id
        for match_expr in match_exprs:
            prev_id = self._transpile_match_expr(match_expr, prev_id)
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
    # Match expression to flowchart (no merge nodes)
    # =========================================================================

    def _transpile_match_expr(
        self,
        match: nodes.MatchExprNode,
        start_id: str,
        subgraph_name: Optional[str] = None,
    ) -> str:
        """Generate flowchart nodes for a match expression. Returns the decision node ID."""
        use_subgraph = self.use_subgraphs and (self._nesting_depth > 0 or subgraph_name is not None)
        if use_subgraph:
            sg_id = self._new_subgraph_id("match")
            label = subgraph_name or "nested decision"
            self._emit(f"{self._indent()}subgraph {sg_id}[{self._q(label)}]")
            self._nesting_depth += 1
        if match.scrutinee:
            scrutinee_label = self._expr_to_label(match.scrutinee)
            decision_id = self._new_node_id("D")
            self._emit(f"{self._indent()}{decision_id}{{{{{self._q(scrutinee_label)}}}}}")
            self._emit(f"{self._indent()}{start_id} --> {decision_id}")
        else:
            decision_id = start_id
        for arm in match.arms:
            self._transpile_match_arm(arm, decision_id)
        if use_subgraph:
            self._nesting_depth -= 1
            self._emit(f"{self._indent()}end")
        return decision_id

    def _transpile_match_arm(self, arm: nodes.MatchArm, from_id: str) -> None:
        """Generate nodes for a match arm (terminal — no merge)."""
        pattern_label = self._pattern_to_label(arm.pattern)
        if arm.guard:
            guard_id = self._new_node_id("G")
            guard_label = self._expr_to_label(arm.guard)
            self._emit(f"{self._indent()}{guard_id}{{{{{self._q(guard_label)}}}}}")
            self._emit(f"{self._indent()}{from_id} -->|{self._q(pattern_label)}| {guard_id}")
            if isinstance(arm.body, nodes.MatchExprNode):
                self._transpile_match_expr(arm.body, guard_id, f"when {pattern_label} (guarded)")
            else:
                outcome_id = self._new_node_id("O")
                body_label = self._expr_to_label(arm.body)
                self._emit(f"{self._indent()}{outcome_id}[{self._q(body_label)}]")
                self._emit(f"{self._indent()}{guard_id} -->|{self._q('Yes')}| {outcome_id}")
        else:
            if isinstance(arm.body, nodes.MatchExprNode):
                self._transpile_match_expr(arm.body, from_id, f"when {pattern_label}")
            else:
                outcome_id = self._new_node_id("O")
                body_label = self._expr_to_label(arm.body)
                self._emit(f"{self._indent()}{outcome_id}[{self._q(body_label)}]")
                self._emit(f"{self._indent()}{from_id} -->|{self._q(pattern_label)}| {outcome_id}")

    # =========================================================================
    # Element group processing (linear chain — no fan-in merge)
    # =========================================================================

    def _transpile_element_group(self, group: nodes.ElementGroupNode, prev_id: str) -> str:
        """Generate flowchart nodes for an element group. Returns last node ID."""
        combinator = (
            "ALL OF (conjunctive)" if group.combinator == "all_of" else "ANY OF (alternative limb)"
        )
        group_id = self._new_node_id("GRP")
        self._emit(f"    {group_id}{{{{{self._q(combinator)}}}}}")
        self._emit(f"    {prev_id} --> {group_id}")
        current = group_id
        for member in group.members:
            if isinstance(member, nodes.ElementGroupNode):
                current = self._transpile_element_group(member, current)
            else:
                member_id = self._new_node_id("ELEM")
                label = self._expr_to_label(member.description)
                self._emit(f"    {member_id}[{self._q(label)}]")
                self._emit(f"    {current} --> {member_id}")
                self._element_nodes[member.name] = member_id
                current = member_id
        return current

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
            return "nested decision"
        elif isinstance(node, nodes.StructLiteralNode):
            if node.struct_name:
                return f"new {node.struct_name}"
            return "..."
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
            return f"{pattern.type_name}: {fields}"
        else:
            return "?"

    def _penalty_to_label(self, penalty: nodes.PenaltyNode) -> str:
        """Convert penalty to label text."""
        parts: List[str] = []
        if penalty.death_penalty:
            parts.append("Death")
        if penalty.imprisonment_max:
            duration = str(penalty.imprisonment_max)
            parts.append(f"Imprisonment up to {duration}")
        if penalty.fine_max:
            parts.append(f"Fine up to ${penalty.fine_max.amount}")
        if penalty.caning_max:
            if penalty.caning_min:
                parts.append(f"Caning {penalty.caning_min}-{penalty.caning_max} strokes")
            else:
                parts.append(f"Caning up to {penalty.caning_max} strokes")
        if penalty.supplementary:
            parts.append(penalty.supplementary.value)
        if getattr(penalty, "sentencing", None):
            parts.append(f"({penalty.sentencing})")
        if getattr(penalty, "mandatory_min_imprisonment", None):
            parts.append(f"Min imprisonment: {penalty.mandatory_min_imprisonment}")
        mandatory_min_fine = getattr(penalty, "mandatory_min_fine", None)
        if mandatory_min_fine is not None:
            parts.append(f"Min fine: ${mandatory_min_fine.amount}")
        return "; ".join(parts) if parts else "Penalty TBD"

    def _deontic_prefix(self, element_type: str) -> str:
        """Return prefix for deontic element types."""
        prefixes = {
            "obligation": "OBL: ",
            "prohibition": "PRH: ",
            "permission": "PRM: ",
        }
        return prefixes.get(element_type, "")

    def _element_suffix(self, elem: nodes.ElementNode) -> str:
        """Return suffix for causation/burden info."""
        parts = []
        if getattr(elem, "caused_by", None):
            parts.append(f"caused by: {elem.caused_by}")
        burden = getattr(elem, "burden", None)
        if isinstance(burden, str):
            b = burden
            burden_standard = getattr(elem, "burden_standard", None)
            if isinstance(burden_standard, str):
                b += f"/{burden_standard}"
            parts.append(f"burden: {b}")
        return f"({', '.join(parts)})" if parts else ""

    def _exception_outcome_label(self, exception: nodes.ExceptionNode) -> str:
        """Explain how an exception path defeats or redirects liability."""
        effect = exception.effect.value if exception.effect else "Exception applies"
        parts = [effect]
        if exception.guard:
            parts.append(f"guard: {self._expr_to_label(exception.guard)}")
        if exception.priority is not None:
            parts.append(f"priority {exception.priority}")
        if exception.defeats:
            parts.append(f"defeats {exception.defeats}")
        return " | ".join(parts)

    def _emit_provenance_nodes(
        self, statute: nodes.StatuteNode, *, start_id: str, fallback_id: str
    ) -> None:
        """Link illustrations and case law back to the graph as provenance."""
        for illustration in statute.illustrations:
            illustration_id = self._new_node_id("ILLUS")
            label = illustration.label or "illustration"
            text = f"Illustration {label}: {illustration.description.value}"
            self._emit(f"    {illustration_id}[{self._q(text)}]")
            self._emit(
                f"    {start_id} -.->|{self._q('illustration provenance')}| {illustration_id}"
            )

        for case_law in statute.case_law:
            case_id = self._new_node_id("CASE")
            citation = f" {case_law.citation.value}" if case_law.citation else ""
            text = f"Case law: {case_law.case_name.value}{citation}"
            self._emit(f"    {case_id}[{self._q(text)}]")
            anchor_id = self._element_nodes.get(case_law.element_ref or "", fallback_id)
            edge_label = "interprets" if case_law.element_ref else "judicial authority"
            self._emit(f"    {anchor_id} -.->|{self._q(edge_label)}| {case_id}")
