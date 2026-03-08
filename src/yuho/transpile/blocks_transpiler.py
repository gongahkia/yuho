"""
Block-notation transpiler for Yuho.

Outputs a structured text representation of statute blocks,
providing a hierarchical view of the statute structure.
"""

from typing import List, Any, Optional
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
        for statute in getattr(node, "statutes", ()) or ():
            self.visit_statute(statute)
    
    def visit_statute(self, node: StatuteNode) -> None:
        """Visit statute node."""
        section = getattr(node, "section_number", "") or getattr(node, "section", "") or "?"
        title_node = getattr(node, "title", "") or ""
        title = getattr(title_node, "value", str(title_node))
        
        statute_block = Block(
            block_type="STATUTE",
            name=f"S{section}",
            content=[f"title: {title}"],
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
        
        self.blocks.append(statute_block)
        self.current_statute = None
    
    def _build_definitions_block(self, definitions: List[Any]) -> None:
        """Build definitions block."""
        if not self.current_statute:
            return
        
        content = []
        for defn in definitions:
            term = getattr(defn, "term", "") or getattr(defn, "name", "") or "?"
            definition = getattr(defn, "definition", "") or getattr(defn, "value", "") or ""
            definition = getattr(definition, "value", str(definition)) # unwrap StringLit
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
    
    def _build_elements_block(self, elements: List[Any]) -> None:
        """Build elements block."""
        if not self.current_statute:
            return
        
        children = []
        
        # Group by type
        actus_reus = []
        mens_rea = []
        other = []
        
        def _collect_elements(elems):
            for elem in elems:
                if isinstance(elem, ElementGroupNode):
                    _collect_elements(elem.members)
                    continue
                elem_type = getattr(elem, "element_type", "") or "element"
                name = getattr(elem, "name", "") or "?"
                desc = getattr(elem, "description", "") or ""
                if len(str(desc)) > 50:
                    desc = str(desc)[:47] + "..."
                entry = f"{name}: {desc}"
                if "actus" in elem_type.lower():
                    actus_reus.append(entry)
                elif "mens" in elem_type.lower():
                    mens_rea.append(entry)
                else:
                    other.append(entry)
        _collect_elements(elements)
        
        if actus_reus:
            children.append(Block(
                block_type="ACTUS_REUS",
                name="act",
                content=actus_reus,
                children=[],
                level=2,
            ))
        
        if mens_rea:
            children.append(Block(
                block_type="MENS_REA",
                name="intent",
                content=mens_rea,
                children=[],
                level=2,
            ))
        
        if other:
            children.append(Block(
                block_type="CIRCUMSTANCE",
                name="context",
                content=other,
                children=[],
                level=2,
            ))
        
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
            min_str = str(penalty.fine_min) if penalty.fine_min else "---"
            content.append(f"fine: {min_str} to {penalty.fine_max}")
        if getattr(penalty, "caning_max", None):
            min_str = str(penalty.caning_min) if penalty.caning_min else "---"
            content.append(f"caning: {min_str} to {penalty.caning_max} strokes")
        if getattr(penalty, "supplementary", None):
            content.append(f"supplementary: {penalty.supplementary}")
        
        if content:
            block = Block(
                block_type="PENALTY",
                name="penalty",
                content=content,
                children=[],
                level=1,
            )
            self.current_statute.children.append(block)
    
    def _build_illustrations_block(self, illustrations: List[Any]) -> None:
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
                line = line[:width - 7] + "..."
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
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║                    BLOCK NOTATION VIEW                      ║",
            "╚════════════════════════════════════════════════════════════╝",
            "",
        ]
        
        # Render blocks
        output = format_blocks(builder.blocks, style="box")
        lines.append(output)
        
        # Footer
        lines.append("")
        lines.append(f"Total statutes: {len(builder.blocks)}")
        
        return "\n".join(lines)
