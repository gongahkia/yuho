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

    def __init__(
        self,
        direction: str = "TD",
        use_subgraphs: bool = True,
        shape: str = "statute",
    ):
        """
        Args:
            direction: Mermaid layout direction (TD/LR/RL/BT).
            use_subgraphs: cluster nested match expressions into subgraphs.
            shape: ``"statute"`` (default) emits the statute-structure
                flowchart that has shipped since the project's earliest
                transpiler. ``"schema"`` emits a fact-pattern decision
                tree by walking a case-struct's enum-typed fields and
                surfacing the consuming ``fn``'s consequence per leaf.
                See ``_transpile_schema_module`` for the algorithm.
        """
        if shape not in ("statute", "schema"):
            raise ValueError(f"unknown mermaid shape: {shape!r}")
        self.direction = direction
        self.use_subgraphs = use_subgraphs
        self.shape = shape
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
        if self.shape == "schema":
            self._transpile_schema_module(ast)
        else:
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
        all_penalties = []
        if statute.penalty is not None:
            all_penalties.append(statute.penalty)
        all_penalties.extend(getattr(statute, "additional_penalties", ()) or ())
        for pen in all_penalties:
            penalty_id = self._new_node_id("PENALTY")
            penalty_text = self._penalty_to_label(pen)
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
    # Schema-shape rendering (--shape schema)
    # =========================================================================

    def _transpile_schema_module(self, ast: nodes.ModuleNode) -> None:
        """Render a schema-shape decision tree from struct + fn pairs.

        The 5-minutes.md illustration of a "Cheating" decision tree —
        ``Cheating -> Accused -> Action -> Attribution -> Deception ->
        Inducement -> CausesDamageHarm -> DamageHarmResult ->
        ConsequenceDefinition`` — is the target shape. We reconstruct it
        by:

        1. Finding the *case struct* (a struct whose fields are all
           plain types or string-named enums), e.g. ``CheatingCase``.
        2. Finding the *enum-like structs* — structs whose fields all
           have empty/no type annotation, e.g. ``DeceptionType``.
        3. Linking case-struct fields to enum-likes by naming
           convention: field ``deceptionType`` -> struct
           ``DeceptionType`` (capitalise first + suffix preserved).
        4. Finding the *consuming fn* — one whose params correspond
           1:1 (by name+order) to the case-struct's fields.
        5. Walking the case-struct fields in order, branching on each
           enum's variants, and terminating in the consuming fn's
           ``consequence`` outcomes (taken from its match arms).

        When any of (1)-(4) cannot be located the renderer emits a
        single ``no-schema-pair-found`` annotation and falls back to
        the standard statute-shape rendering for any statutes that
        happen to be present.
        """
        case_struct = self._find_case_struct(ast)
        enum_map = self._find_enum_structs(ast)
        consuming_fn = self._find_consuming_fn(ast, case_struct) if case_struct else None

        if not case_struct or not consuming_fn:
            self._emit("    %% schema-shape requires a struct + matching fn pair.")
            self._emit('    NOSCHEMA["No schema pair found — falling back to statute shape."]')
            for statute in ast.statutes:
                self._transpile_statute(statute)
            for func in ast.function_defs:
                self._transpile_function(func)
            return

        self._emit(f"    %% Schema decision tree: {case_struct.name} -> {consuming_fn.name}")
        # Root node: the case struct's display name (strip "Case" suffix
        # for legibility, mirroring the 5-minutes.md depiction).
        display = case_struct.name
        if display.endswith("Case"):
            display = display[:-4]
        root_id = self._new_node_id("SCHEMA")
        self._emit(f"    {root_id}([{self._q(display)}])")

        # Pre-compute consequence labels per (field_name, value) by walking
        # the consuming fn's match arms. The arms most commonly take the
        # shape `case TRUE if <field> == "<value>" := consequence "<X>"`,
        # but the value strings ("none", "fraudulently", …) typically use
        # different casing than the corresponding enum variant names
        # (Fraudulently, NA, …). We bucket case-insensitively and build a
        # default-arm fallback for the wildcard `case _ := consequence …`.
        consequence_terminals = self._consequences_by_field_value(consuming_fn)
        default_consequence = consequence_terminals.get(("__default__", "__default__"))

        # Variant-driven walk: each enum variant becomes a labelled edge
        # from the current field's decision diamond. The edge terminates
        # in either a consequence node (when a fn arm matches the variant
        # name case-insensitively) or the next field's decision diamond
        # via a "continue" anchor.
        prev_decision = root_id
        for i, field in enumerate(case_struct.fields):
            decision_id = self._new_node_id("FIELD")
            self._emit(f"    {decision_id}{{{{{self._q(field.name)}}}}}")
            self._emit(f"    {prev_decision} --> {decision_id}")

            enum_name = self._infer_enum_name(field.name)
            enum_struct = enum_map.get(enum_name)
            is_last_field = (i == len(case_struct.fields) - 1)

            # Build the "continue to next field" anchor up-front so every
            # variant edge that doesn't terminate in a consequence can
            # point at the same node. For the last field we point at a
            # default-consequence leaf instead.
            if is_last_field:
                if default_consequence:
                    cont_id = self._new_node_id("CON")
                    self._emit(f"    {cont_id}[{self._q(default_consequence)}]")
                else:
                    cont_id = self._new_node_id("END")
                    self._emit(f'    {cont_id}["evaluation complete"]')
            else:
                cont_id = self._new_node_id("CONT")
                self._emit(f'    {cont_id}["continue"]')

            if enum_struct is None:
                # Field has no matching enum; single "any value" edge.
                self._emit(f"    {decision_id} --> {cont_id}")
            else:
                emitted_any = False
                for variant in enum_struct.fields:
                    branch_label = f"{enum_struct.name}.{variant.name}"
                    term = consequence_terminals.get(
                        (field.name, variant.name.lower())
                    )
                    if term is not None:
                        leaf_id = self._new_node_id("CON")
                        self._emit(f"    {leaf_id}[{self._q(term)}]")
                        self._emit(
                            f"    {decision_id} -->|{self._q(branch_label)}| {leaf_id}"
                        )
                    else:
                        self._emit(
                            f"    {decision_id} -->|{self._q(branch_label)}| {cont_id}"
                        )
                    emitted_any = True
                if not emitted_any:
                    self._emit(f"    {decision_id} --> {cont_id}")

            prev_decision = cont_id if not is_last_field else cont_id

    def _find_case_struct(self, ast: nodes.ModuleNode) -> Optional[nodes.StructDefNode]:
        """Pick the most-likely 'fact pattern' struct in the module.

        Heuristic: the struct whose name ends in ``Case`` is the
        canonical pick. Otherwise, the struct with the most fields and
        no nested-struct types is preferred.
        """
        if not getattr(ast, "type_defs", None):
            return None
        case_named = [s for s in ast.type_defs
                      if isinstance(s, nodes.StructDefNode) and s.name.endswith("Case")]
        if case_named:
            return case_named[0]
        # Fallback: largest non-enum struct.
        candidates = [s for s in ast.type_defs
                      if isinstance(s, nodes.StructDefNode) and s.fields
                      and any(self._field_is_typed(f) for f in s.fields)]
        return max(candidates, key=lambda s: len(s.fields), default=None)

    def _find_enum_structs(self, ast: nodes.ModuleNode):
        """Return a name -> EnumDefNode mapping for the module's enums.

        Yuho exposes proper ``enum`` declarations (``enum DeceptionType
        { Fraudulently, Dishonestly, NA }``); the schema-flowchart links
        case-struct fields to these by capitalising the field name (the
        documented naming convention). We expose enum variants under
        the same ``.fields`` interface that ``StructDefNode`` uses so
        the rendering loop stays uniform.
        """
        from types import SimpleNamespace
        out: Dict[str, object] = {}
        for e in getattr(ast, "enum_defs", ()) or ():
            # Adapt EnumDefNode -> a struct-like object with .name + .fields.
            adapted_fields = [SimpleNamespace(name=v.name) for v in e.variants]
            out[e.name] = SimpleNamespace(name=e.name, fields=adapted_fields)
        # Also include enum-shaped structs (rare; some legacy fixtures use
        # the all-untyped-field convention from before `enum` landed).
        for s in getattr(ast, "type_defs", ()) or ():
            if not isinstance(s, nodes.StructDefNode) or not s.fields:
                continue
            if all(not self._field_is_typed(f) for f in s.fields):
                out.setdefault(s.name, s)
        return out

    @staticmethod
    def _field_is_typed(field: nodes.FieldDef) -> bool:
        """Heuristic: a field is 'typed' if it has a real type annotation
        beyond a bare name. Enum-like structs use field-as-variant where
        the type annotation is essentially empty / synthesised."""
        ta = getattr(field, "type_annotation", None)
        if ta is None:
            return False
        # Variant-style fields parse with a TypeNode whose name == the
        # field name. That's how we tell enum-likes apart.
        name = getattr(ta, "name", None)
        return bool(name) and name != field.name

    @staticmethod
    def _infer_enum_name(field_name: str) -> str:
        """Naming-convention link: field ``deceptionType`` -> struct
        ``DeceptionType``. Capitalises the first letter; preserves any
        embedded camelCase."""
        if not field_name:
            return field_name
        return field_name[0].upper() + field_name[1:]

    def _find_consuming_fn(
        self,
        ast: nodes.ModuleNode,
        case_struct: Optional[nodes.StructDefNode],
    ) -> Optional[nodes.FunctionDefNode]:
        """Return the fn whose parameters correspond to the case-struct's
        fields. We require name+order alignment between fn params and
        struct fields, since ``apply_scope``/``is_infringed`` would
        otherwise pick up scope-composition fns that don't apply here.
        """
        if not case_struct:
            return None
        field_names = [f.name for f in case_struct.fields]
        for fn in getattr(ast, "function_defs", ()) or ():
            param_names = [p.name for p in fn.params]
            # 1:1 alignment OR first-N alignment is acceptable.
            if param_names and param_names[: len(field_names)] == field_names[: len(param_names)]:
                return fn
        return None

    def _consequences_by_field_value(
        self, fn: nodes.FunctionDefNode
    ) -> Dict[tuple, str]:
        """Walk a fn's match arms and bucket consequences by (field, value)."""
        out: Dict[tuple, str] = {}
        match_exprs = self._find_match_exprs(fn.body)
        for m in match_exprs:
            for arm in m.arms:
                guard = getattr(arm, "guard", None)
                body = getattr(arm, "body", None)
                if not guard or not body:
                    continue
                # Patterns like `<param> == "<value>"`.
                fld, val = self._parse_field_eq_string(guard)
                if fld is not None and val is not None:
                    consequence_text = self._consequence_label(body)
                    if consequence_text:
                        out[(fld, val.lower())] = consequence_text
                else:
                    consequence_text = self._consequence_label(body)
                    if consequence_text:
                        out.setdefault(("__default__", "__default__"), consequence_text)
        return out

    @staticmethod
    def _parse_field_eq_string(expr) -> tuple:
        """Detect `<ident> == "<string>"`-shaped guards."""
        if isinstance(expr, nodes.BinaryExprNode) and expr.operator == "==":
            left, right = expr.left, expr.right
            if isinstance(left, nodes.IdentifierNode) and isinstance(right, nodes.StringLit):
                return left.name, right.value
            if isinstance(right, nodes.IdentifierNode) and isinstance(left, nodes.StringLit):
                return right.name, left.value
        return (None, None)

    @staticmethod
    def _consequence_label(body) -> Optional[str]:
        """Pull a string label out of a match-arm body when the body is
        a ``consequence "<text>"`` expression. Anything else surfaces as
        the plain expression text via ``repr`` so the diagram still emits."""
        # ConsequenceExpr nodes wrap an expression; walk the tree.
        if isinstance(body, nodes.StringLit):
            return body.value
        for child in body.children() if hasattr(body, "children") else []:
            r = MermaidTranspiler._consequence_label(child)
            if r is not None:
                return r
        return None

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
        """Convert penalty to label text.

        Honours the G8 / G14 sentinels (``fine := unlimited``,
        ``caning := unspecified``) and prefixes the combinator name when
        present so a viewer can tell ``cumulative`` from ``or_both``.
        """
        parts: List[str] = []
        if penalty.death_penalty:
            parts.append("Death")
        if penalty.imprisonment_max:
            duration = str(penalty.imprisonment_max)
            parts.append(f"Imprisonment up to {duration}")
        if penalty.fine_max:
            parts.append(f"Fine up to ${penalty.fine_max.amount}")
        elif getattr(penalty, "fine_unlimited", False):
            parts.append("Fine (unlimited)")
        if penalty.caning_max:
            if penalty.caning_min:
                parts.append(f"Caning {penalty.caning_min}-{penalty.caning_max} strokes")
            else:
                parts.append(f"Caning up to {penalty.caning_max} strokes")
        elif getattr(penalty, "caning_unspecified", False):
            parts.append("Caning (unspecified)")
        if penalty.supplementary:
            parts.append(penalty.supplementary.value)
        if getattr(penalty, "sentencing", None):
            parts.append(f"({penalty.sentencing})")
        if getattr(penalty, "mandatory_min_imprisonment", None):
            parts.append(f"Min imprisonment: {penalty.mandatory_min_imprisonment}")
        mandatory_min_fine = getattr(penalty, "mandatory_min_fine", None)
        if mandatory_min_fine is not None:
            parts.append(f"Min fine: ${mandatory_min_fine.amount}")
        body = "; ".join(parts) if parts else "Penalty TBD"
        combinator = getattr(penalty, "combinator", None)
        if combinator and combinator != "cumulative":
            # Default `cumulative` matches the no-combinator case; no need to label.
            return f"[{combinator}] {body}"
        return body

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
