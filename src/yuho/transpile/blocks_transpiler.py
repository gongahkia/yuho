"""
Block-notation transpiler for Yuho.

Outputs a structured text representation of statute blocks,
providing a hierarchical view of the statute structure.
"""

from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass

from yuho.transpile.base import TranspilerBase, TranspileTarget
from yuho.ast.nodes import (
    ModuleNode,
    StatuteNode,
    DefinitionEntry,
    ElementNode,
    ElementGroupNode,
    PenaltyNode,
    IllustrationNode,
    ExceptionNode,
    CaseLawNode,
    ImportNode,
    StructDefNode,
    FunctionDefNode,
    VariableDecl,
    StringLit,
    MatchExprNode,
)
from yuho.ast.visitor import Visitor


@dataclass
class Block:
    """Represents a block in block-notation."""

    block_type: str
    name: str
    content: List[str]
    children: List["Block"]
    level: int = 0


class BlockBuilder(Visitor):
    """Builds block notation from AST."""

    def __init__(self):
        self.blocks: List[Block] = []
        self.current_statute: Optional[Block] = None

    def visit_module(self, node: ModuleNode) -> None:
        """Visit module node."""
        if node.imports:
            self._build_imports_block(node.imports)
        if node.type_defs:
            self._build_type_defs_block(node.type_defs)
        if node.function_defs:
            self._build_function_defs_block(node.function_defs)
        for statute in getattr(node, "statutes", ()) or ():
            self.visit_statute(statute)
        if node.variables:
            self._build_variables_block(node.variables)

    def visit_statute(self, node: StatuteNode) -> None:
        """Visit statute node."""
        section = getattr(node, "section_number", "") or getattr(node, "section", "") or "?"
        title_node = getattr(node, "title", "") or ""
        title = getattr(title_node, "value", str(title_node))

        meta = [f"title: {title}"]
        if getattr(node, "effective_date", None):
            meta.append(f"effective: {node.effective_date}")
        if getattr(node, "repealed_date", None):
            meta.append(f"repealed: {node.repealed_date}")
        if getattr(node, "subsumes", None):
            meta.append(f"subsumes: s{node.subsumes}")
        if getattr(node, "amends", None):
            meta.append(f"amends: s{node.amends}")
        statute_block = Block(
            block_type="STATUTE",
            name=f"S{section}",
            content=meta,
            children=[],
            level=0,
        )
        self.current_statute = statute_block

        # Visit children
        if hasattr(node, "definitions") and node.definitions:
            self._build_definitions_block(node.definitions)

        if hasattr(node, "elements") and node.elements:
            self._build_elements_block(node.elements)

        if hasattr(node, "penalty") and node.penalty:
            self._build_penalty_block(node.penalty)

        if hasattr(node, "illustrations") and node.illustrations:
            self._build_illustrations_block(node.illustrations)

        if hasattr(node, "exceptions") and node.exceptions:
            self._build_exceptions_block(node.exceptions)

        if hasattr(node, "case_law") and node.case_law:
            self._build_case_law_block(node.case_law)

        self.blocks.append(statute_block)
        self.current_statute = None

    def _build_definitions_block(self, definitions: Sequence[DefinitionEntry]) -> None:
        """Build definitions block."""
        if not self.current_statute:
            return

        content = []
        for defn in definitions:
            term = getattr(defn, "term", "") or getattr(defn, "name", "") or "?"
            definition = getattr(defn, "definition", "") or getattr(defn, "value", "") or ""
            definition = getattr(definition, "value", str(definition))  # unwrap StringLit
            if len(definition) > 60:
                definition = definition[:57] + "..."
            content.append(f"{term} := {definition}")

        block = Block(
            block_type="DEFINITIONS",
            name="defs",
            content=content,
            children=[],
            level=1,
        )
        self.current_statute.children.append(block)

    def _build_elements_block(self, elements: Sequence[ElementNode | ElementGroupNode]) -> None:
        """Build elements block."""
        if not self.current_statute:
            return

        children: List[Block] = []

        # Group by type
        groups: Dict[str, List[str]] = {
            "actus_reus": [],
            "mens_rea": [],
            "circumstance": [],
            "obligation": [],
            "prohibition": [],
            "permission": [],
        }

        def _collect_elements(elems: Sequence[ElementNode | ElementGroupNode]) -> None:
            for elem in elems:
                if isinstance(elem, ElementGroupNode):
                    _collect_elements(elem.members)
                    continue
                elem_type = getattr(elem, "element_type", "") or "element"
                name = getattr(elem, "name", "") or "?"
                desc = getattr(elem, "description", "") or ""
                desc = (
                    self._expr_to_str(desc)
                    if hasattr(desc, "children")
                    else getattr(desc, "value", str(desc))
                )
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                entry = f"{name}: {desc}"
                if getattr(elem, "caused_by", None):
                    entry += f" [caused_by: {elem.caused_by}]"
                if getattr(elem, "burden", None):
                    burden_str = elem.burden
                    if getattr(elem, "burden_standard", None):
                        burden_str += f"/{elem.burden_standard}"
                    entry += f" [burden: {burden_str}]"
                bucket = elem_type if elem_type in groups else "circumstance"
                groups[bucket].append(entry)

        _collect_elements(elements)

        type_labels = {
            "actus_reus": ("ACTUS_REUS", "act"),
            "mens_rea": ("MENS_REA", "intent"),
            "circumstance": ("CIRCUMSTANCE", "context"),
            "obligation": ("OBLIGATION", "obligation"),
            "prohibition": ("PROHIBITION", "prohibition"),
            "permission": ("PERMISSION", "permission"),
        }
        for key, entries in groups.items():
            if entries:
                bt, nm = type_labels[key]
                children.append(
                    Block(
                        block_type=bt,
                        name=nm,
                        content=entries,
                        children=[],
                        level=2,
                    )
                )

        block = Block(
            block_type="ELEMENTS",
            name="elements",
            content=[],
            children=children,
            level=1,
        )
        self.current_statute.children.append(block)

    def _build_penalty_block(self, penalty: Any) -> None:
        """Build penalty block."""
        if not self.current_statute:
            return

        content = []

        if getattr(penalty, "death_penalty", None):
            content.append("death: applicable")
        if getattr(penalty, "imprisonment_max", None):
            min_str = str(penalty.imprisonment_min) if penalty.imprisonment_min else "---"
            content.append(f"imprisonment: {min_str} to {penalty.imprisonment_max}")
        if getattr(penalty, "fine_max", None):
            min_str = self._expr_to_str(penalty.fine_min) if penalty.fine_min else "---"
            max_str = self._expr_to_str(penalty.fine_max)
            content.append(f"fine: {min_str} to {max_str}")
        if getattr(penalty, "caning_max", None):
            min_str = str(penalty.caning_min) if penalty.caning_min else "---"
            content.append(f"caning: {min_str} to {penalty.caning_max} strokes")
        if getattr(penalty, "supplementary", None):
            supp = getattr(penalty.supplementary, "value", str(penalty.supplementary))
            content.append(f"supplementary: {supp}")
        if getattr(penalty, "sentencing", None):
            content.append(f"sentencing: {penalty.sentencing}")
        if getattr(penalty, "mandatory_min_imprisonment", None):
            content.append(
                f"mandatory_min_imprisonment: {self._expr_to_str(penalty.mandatory_min_imprisonment)}"
            )
        if getattr(penalty, "mandatory_min_fine", None):
            content.append(f"mandatory_min_fine: {self._expr_to_str(penalty.mandatory_min_fine)}")

        if content:
            block = Block(
                block_type="PENALTY",
                name="penalty",
                content=content,
                children=[],
                level=1,
            )
            self.current_statute.children.append(block)

    def _build_illustrations_block(self, illustrations: Sequence[IllustrationNode]) -> None:
        """Build illustrations block."""
        if not self.current_statute:
            return

        content = []
        for illus in illustrations:
            label = getattr(illus, "label", "") or "?"
            text = getattr(illus, "text", "") or getattr(illus, "description", "") or ""
            text = getattr(text, "value", str(text))
            if len(text) > 60:
                text = text[:57] + "..."
            content.append(f"{label} {text}")

        if content:
            block = Block(
                block_type="ILLUSTRATIONS",
                name="examples",
                content=content,
                children=[],
                level=1,
            )
            self.current_statute.children.append(block)

    def _build_exceptions_block(self, exceptions: Sequence[ExceptionNode]) -> None:
        """Build exceptions block."""
        if not self.current_statute:
            return

        content = []
        for exc in exceptions:
            label = getattr(exc, "label", "") or "?"
            condition = getattr(exc, "condition", "") or ""
            condition = getattr(condition, "value", str(condition))
            if len(condition) > 50:
                condition = condition[:47] + "..."
            effect = getattr(exc, "effect", None)
            if effect:
                effect_str = getattr(effect, "value", str(effect))
                if len(effect_str) > 40:
                    effect_str = effect_str[:37] + "..."
                content.append(f"[{label}] IF {condition} THEN {effect_str}")
            else:
                content.append(f"[{label}] IF {condition}")

        if content:
            block = Block(
                block_type="EXCEPTIONS",
                name="exceptions",
                content=content,
                children=[],
                level=1,
            )
            self.current_statute.children.append(block)

    def _build_case_law_block(self, case_law: Sequence[CaseLawNode]) -> None:
        """Build case law block."""
        if not self.current_statute:
            return

        content = []
        for cl in case_law:
            case_name = getattr(cl, "case_name", "") or ""
            case_name = getattr(case_name, "value", str(case_name))
            citation = getattr(cl, "citation", None)
            citation_str = ""
            if citation:
                citation_str = f" {getattr(citation, 'value', str(citation))}"
            holding = getattr(cl, "holding", "") or ""
            holding = getattr(holding, "value", str(holding))
            if len(holding) > 40:
                holding = holding[:37] + "..."
            element_ref = getattr(cl, "element_ref", None)
            ref_str = f" -> {element_ref}" if element_ref else ""
            content.append(f"{case_name}{citation_str}")
            content.append(f"  holding: {holding}{ref_str}")

        if content:
            block = Block(
                block_type="CASE_LAW",
                name="cases",
                content=content,
                children=[],
                level=1,
            )
            self.current_statute.children.append(block)

    def _build_imports_block(self, imports: Sequence[ImportNode]) -> None:
        """Build imports block."""
        content = []
        for imp in imports:
            path = getattr(imp, "path", "") or "?"
            names = getattr(imp, "imported_names", ()) or ()
            is_wildcard = "*" in names
            if is_wildcard:
                content.append(f"* FROM {path}")
            elif names:
                content.append(f"{', '.join(names)} FROM {path}")
            else:
                content.append(f"IMPORT {path}")

        if content:
            block = Block(
                block_type="IMPORTS",
                name="imports",
                content=content,
                children=[],
                level=0,
            )
            self.blocks.append(block)

    def _build_type_defs_block(self, type_defs: Sequence[StructDefNode]) -> None:
        """Build type definitions block."""
        children = []
        for struct in type_defs:
            name = getattr(struct, "name", "") or "?"
            fields = getattr(struct, "fields", ()) or ()
            field_lines = []
            for f in fields:
                fname = getattr(f, "name", "") or "?"
                ftype = getattr(f, "type_annotation", None)
                type_str = self._type_to_str(ftype) if ftype else "?"
                field_lines.append(f"{fname}: {type_str}")
            children.append(
                Block(
                    block_type="STRUCT",
                    name=name,
                    content=field_lines,
                    children=[],
                    level=1,
                )
            )

        if children:
            block = Block(
                block_type="TYPE_DEFS",
                name="types",
                content=[],
                children=children,
                level=0,
            )
            self.blocks.append(block)

    def _build_function_defs_block(self, function_defs: Sequence[FunctionDefNode]) -> None:
        """Build function definitions block."""
        children = []
        for func in function_defs:
            name = getattr(func, "name", "") or "?"
            params = getattr(func, "params", ()) or ()
            ret = getattr(func, "return_type", None)
            param_strs = []
            for p in params:
                pname = getattr(p, "name", "") or "?"
                ptype = getattr(p, "type_annotation", None)
                type_str = self._type_to_str(ptype) if ptype else "?"
                param_strs.append(f"{pname}: {type_str}")
            sig = f"({', '.join(param_strs)})"
            if ret:
                sig += f" -> {self._type_to_str(ret)}"
            body = getattr(func, "body", None)
            body_lines = []
            if body:
                stmts = getattr(body, "statements", ()) or ()
                for stmt in stmts:
                    body_lines.append(self._stmt_to_str(stmt))
            content = [sig] + body_lines
            children.append(
                Block(
                    block_type="FUNCTION",
                    name=name,
                    content=content,
                    children=[],
                    level=1,
                )
            )

        if children:
            block = Block(
                block_type="FUNC_DEFS",
                name="functions",
                content=[],
                children=children,
                level=0,
            )
            self.blocks.append(block)

    def _build_variables_block(self, variables: Sequence[VariableDecl]) -> None:
        """Build variables block."""
        content = []
        for var in variables:
            name = getattr(var, "name", "") or "?"
            vtype = getattr(var, "type_annotation", None)
            type_str = self._type_to_str(vtype) if vtype else "?"
            value = getattr(var, "value", None)
            if value:
                val_str = self._expr_to_str(value)
                content.append(f"{name}: {type_str} = {val_str}")
            else:
                content.append(f"{name}: {type_str}")

        if content:
            block = Block(
                block_type="VARIABLES",
                name="vars",
                content=content,
                children=[],
                level=0,
            )
            self.blocks.append(block)

    # -- helper formatters for expressions, types, statements --

    def _type_to_str(self, node: Any) -> str:
        """Convert a type node to a short string."""
        from yuho.ast import nodes as n

        if isinstance(node, n.BuiltinType):
            return node.name
        elif isinstance(node, n.NamedType):
            return node.name
        elif isinstance(node, n.OptionalType):
            return f"{self._type_to_str(node.inner)}?"
        elif isinstance(node, n.ArrayType):
            return f"[{self._type_to_str(node.element_type)}]"
        elif isinstance(node, n.GenericType):
            args = ", ".join(self._type_to_str(a) for a in node.type_args)
            return f"{node.base}<{args}>"
        return str(node)

    def _expr_to_str(self, node: Any) -> str:
        """Convert an expression node to a short string."""
        from yuho.ast import nodes as n

        if isinstance(node, n.IntLit):
            return str(node.value)
        elif isinstance(node, n.FloatLit):
            return str(node.value)
        elif isinstance(node, n.BoolLit):
            return "TRUE" if node.value else "FALSE"
        elif isinstance(node, n.StringLit):
            v = node.value
            if len(v) > 30:
                v = v[:27] + "..."
            return f'"{v}"'
        elif isinstance(node, n.MoneyNode):
            return f"{node.currency.name} {node.amount}"
        elif isinstance(node, n.PercentNode):
            return f"{node.value}%"
        elif isinstance(node, n.DateNode):
            return node.value.isoformat()
        elif isinstance(node, n.DurationNode):
            return str(node)
        elif isinstance(node, n.IdentifierNode):
            return node.name
        elif isinstance(node, n.FieldAccessNode):
            return f"{self._expr_to_str(node.base)}.{node.field_name}"
        elif isinstance(node, n.IndexAccessNode):
            return f"{self._expr_to_str(node.base)}[{self._expr_to_str(node.index)}]"
        elif isinstance(node, n.FunctionCallNode):
            callee = self._expr_to_str(node.callee)
            args = ", ".join(self._expr_to_str(a) for a in node.args)
            return f"{callee}({args})"
        elif isinstance(node, n.BinaryExprNode):
            return f"{self._expr_to_str(node.left)} {node.operator} {self._expr_to_str(node.right)}"
        elif isinstance(node, n.UnaryExprNode):
            return f"{node.operator}{self._expr_to_str(node.operand)}"
        elif isinstance(node, n.PassExprNode):
            return "PASS"
        elif isinstance(node, n.MatchExprNode):
            return "MATCH {...}"
        elif isinstance(node, n.StructLiteralNode):
            name = node.struct_name or "anon"
            return f"{name} {{...}}"
        return str(node)

    def _stmt_to_str(self, node: Any) -> str:
        """Convert a statement node to a short string."""
        from yuho.ast import nodes as n

        if isinstance(node, n.VariableDecl):
            type_str = self._type_to_str(node.type_annotation)
            if node.value:
                return f"LET {node.name}: {type_str} = {self._expr_to_str(node.value)}"
            return f"LET {node.name}: {type_str}"
        elif isinstance(node, n.AssignmentStmt):
            return f"SET {self._expr_to_str(node.target)} = {self._expr_to_str(node.value)}"
        elif isinstance(node, n.ReturnStmt):
            if node.value:
                return f"RETURN {self._expr_to_str(node.value)}"
            return "RETURN"
        elif isinstance(node, n.PassStmt):
            return "PASS"
        elif isinstance(node, n.ExpressionStmt):
            return self._expr_to_str(node.expression)
        return str(node)


def format_blocks(blocks: List[Block], style: str = "box") -> str:
    """
    Format blocks into text output.

    Args:
        blocks: List of Block objects
        style: "box" for box drawing, "indent" for simple indentation

    Returns:
        Formatted string
    """
    lines: List[str] = []

    def render_block_box(block: Block, indent: int = 0) -> None:
        """Render a block with box drawing characters."""
        prefix = "  " * indent
        width = 60 - (indent * 2)

        # Top border
        lines.append(f"{prefix}┌{'─' * (width - 2)}┐")

        # Header
        header = f" [{block.block_type}] {block.name} "
        padding = width - 4 - len(header)
        lines.append(f"{prefix}│{header}{'─' * max(0, padding)}│")

        # Separator
        lines.append(f"{prefix}├{'─' * (width - 2)}┤")

        # Content
        for line in block.content:
            # Wrap long lines
            if len(line) > width - 4:
                line = line[: width - 7] + "..."
            padding = width - 4 - len(line)
            lines.append(f"{prefix}│ {line}{' ' * max(0, padding)} │")

        if not block.content and not block.children:
            lines.append(f"{prefix}│{' ' * (width - 2)}│")

        # Children
        if block.children:
            if block.content:
                lines.append(f"{prefix}├{'─' * (width - 2)}┤")
            for child in block.children:
                render_block_box(child, indent + 1)

        # Bottom border
        lines.append(f"{prefix}└{'─' * (width - 2)}┘")

    def render_block_indent(block: Block, indent: int = 0) -> None:
        """Render a block with simple indentation."""
        prefix = "  " * indent

        lines.append(f"{prefix}[{block.block_type}] {block.name}")

        for line in block.content:
            lines.append(f"{prefix}  | {line}")

        for child in block.children:
            render_block_indent(child, indent + 1)

    # Choose renderer
    renderer = render_block_box if style == "box" else render_block_indent

    for block in blocks:
        renderer(block)
        lines.append("")

    return "\n".join(lines)


class BlocksTranspiler(TranspilerBase):
    """Transpiler that outputs block-notation format."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.BLOCKS

    def transpile(self, ast: ModuleNode) -> str:
        """
        Transpile AST to block-notation format.

        Args:
            ast: The root ModuleNode

        Returns:
            Block-notation string
        """
        builder = BlockBuilder()
        builder.visit(ast)

        # Header
        width = 60
        title = "BLOCK NOTATION VIEW"
        pad = width - 2 - len(title)
        lpad = pad // 2
        rpad = pad - lpad
        lines = [
            f"┌{'─' * (width - 2)}┐",
            f"│{' ' * lpad}{title}{' ' * rpad}│",
            f"└{'─' * (width - 2)}┘",
            "",
        ]

        # Render blocks
        output = format_blocks(builder.blocks, style="box")
        lines.append(output)

        # Footer
        lines.append("")
        statute_count = sum(1 for b in builder.blocks if b.block_type == "STATUTE")
        lines.append(f"Total statutes: {statute_count}")

        return "\n".join(lines)
