"""
AST visualization command for Yuho.

Displays statute AST structure as tree-like ASCII output in terminal.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import click


# Box-drawing characters for tree
TREE_CHARS = {
    "pipe": "│",
    "tee": "├",
    "elbow": "└",
    "dash": "─",
    "space": " ",
}

# Minimal fallback for terminals without unicode
TREE_CHARS_ASCII = {
    "pipe": "|",
    "tee": "+",
    "elbow": "`",
    "dash": "-",
    "space": " ",
}


class ASTVisualizer:
    """Generates tree visualization of Yuho AST."""
    
    def __init__(self, use_color: bool = True, use_unicode: bool = True):
        self.use_color = use_color
        self.chars = TREE_CHARS if use_unicode else TREE_CHARS_ASCII
        self.lines: List[str] = []
    
    def colorize(self, text: str, color: str, bold: bool = False) -> str:
        """Apply color if enabled."""
        if not self.use_color:
            return text
        return click.style(text, fg=color, bold=bold)
    
    def _get_node_display(self, node: Any) -> Tuple[str, str]:
        """
        Get display text and color for a node.
        
        Returns:
            (display_text, color)
        """
        node_type = type(node).__name__
        
        # Map node types to colors and display format
        type_info = {
            "Statute": ("cyan", True),
            "Section": ("blue", True),
            "Definitions": ("yellow", False),
            "Definition": ("yellow", False),
            "Elements": ("green", False),
            "Element": ("green", False),
            "ActusReus": ("green", False),
            "MensRea": ("green", False),
            "Circumstance": ("green", False),
            "Penalty": ("red", False),
            "PenaltyClause": ("red", False),
            "Imprisonment": ("red", False),
            "Fine": ("red", False),
            "Illustrations": ("magenta", False),
            "Illustration": ("magenta", False),
            "Import": ("white", False),
            "TypeDecl": ("cyan", False),
            "FuncDecl": ("cyan", False),
            "Block": ("white", False),
            "Program": ("cyan", True),
        }
        
        color, bold = type_info.get(node_type, ("white", False))
        
        # Build display text with node-specific info
        display = node_type
        
        if hasattr(node, "section_number"):
            display = f"{node_type}[{node.section_number}]"
        elif hasattr(node, "title") and node.title:
            title = node.title[:30] + "..." if len(str(node.title)) > 30 else node.title
            display = f"{node_type}: {title}"
        elif hasattr(node, "name") and node.name:
            display = f"{node_type}: {node.name}"
        elif hasattr(node, "term") and node.term:
            display = f"{node_type}: {node.term}"
        elif hasattr(node, "label") and node.label:
            display = f"{node_type}: {node.label}"
        elif hasattr(node, "element_type"):
            display = f"{node_type}({node.element_type})"
        
        return display, color
    
    def _get_children(self, node: Any) -> List[Tuple[str, Any]]:
        """
        Get child nodes with their attribute names.
        
        Returns:
            List of (attribute_name, child_node) tuples
        """
        children = []
        
        # Known container attributes
        container_attrs = [
            "statutes", "sections", "statements", "items", "children",
            "definitions", "elements", "illustrations", "penalties",
            "clauses", "imports", "declarations", "blocks", "body",
        ]
        
        # Check for container attributes first
        for attr in container_attrs:
            if hasattr(node, attr):
                items = getattr(node, attr)
                if isinstance(items, (list, tuple)):
                    for i, item in enumerate(items):
                        if item is not None:
                            children.append((f"{attr}[{i}]", item))
        
        # Check for single child attributes
        single_attrs = [
            "statute", "section", "penalty", "definition", "element",
            "illustration", "actus_reus", "mens_rea", "circumstance",
            "imprisonment", "fine", "supplementary", "condition",
            "consequence", "left", "right", "value", "expression",
        ]
        
        for attr in single_attrs:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child is not None and not isinstance(child, (str, int, float, bool)):
                    children.append((attr, child))
        
        return children
    
    def _render_node(
        self,
        node: Any,
        prefix: str = "",
        is_last: bool = True,
        show_attr: str = "",
    ) -> None:
        """Recursively render a node and its children."""
        # Determine connector
        if prefix:
            connector = self.chars["elbow"] if is_last else self.chars["tee"]
            connector += self.chars["dash"] * 2 + " "
        else:
            connector = ""
        
        # Get display text
        display, color = self._get_node_display(node)
        
        # Add attribute name if provided
        if show_attr:
            attr_text = self.colorize(f"{show_attr}: ", "white")
        else:
            attr_text = ""
        
        # Build line
        node_text = self.colorize(display, color, bold=(color == "cyan"))
        self.lines.append(f"{prefix}{connector}{attr_text}{node_text}")
        
        # Get children
        children = self._get_children(node)
        
        # Calculate new prefix for children
        if prefix:
            if is_last:
                new_prefix = prefix + "    "
            else:
                new_prefix = prefix + self.chars["pipe"] + "   "
        else:
            new_prefix = ""
        
        # Render children
        for i, (attr, child) in enumerate(children):
            is_last_child = (i == len(children) - 1)
            self._render_node(child, new_prefix, is_last_child, attr)
    
    def visualize(self, ast: Any) -> str:
        """
        Generate tree visualization of AST.
        
        Args:
            ast: The AST root node
            
        Returns:
            String containing the tree visualization
        """
        self.lines = []
        
        # Handle list of nodes
        if isinstance(ast, (list, tuple)):
            for i, node in enumerate(ast):
                is_last = (i == len(ast) - 1)
                self._render_node(node, "", is_last)
        else:
            self._render_node(ast, "", True)
        
        return "\n".join(self.lines)


def format_ast_stats(ast: Any) -> Dict[str, int]:
    """
    Collect statistics about the AST.
    
    Returns:
        Dict mapping node type to count
    """
    stats: Dict[str, int] = {}
    
    def visit(node: Any) -> None:
        if node is None:
            return
        
        if isinstance(node, (list, tuple)):
            for item in node:
                visit(item)
            return
        
        # Count this node type
        node_type = type(node).__name__
        stats[node_type] = stats.get(node_type, 0) + 1
        
        # Visit all attributes that might contain children
        for attr in dir(node):
            if attr.startswith("_"):
                continue
            try:
                value = getattr(node, attr)
                if isinstance(value, (list, tuple)):
                    for item in value:
                        if hasattr(item, "__class__") and not isinstance(item, (str, int, float, bool)):
                            visit(item)
                elif hasattr(value, "__class__") and not isinstance(value, (str, int, float, bool, type(None))):
                    if not callable(value):
                        visit(value)
            except (AttributeError, TypeError):
                pass
    
    visit(ast)
    return stats


def run_ast_viz(
    file: str,
    output: Optional[str] = None,
    stats: bool = False,
    depth: int = 0,
    no_unicode: bool = False,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Run AST visualization command.
    
    Args:
        file: Input .yh file
        output: Output file path (None = stdout)
        stats: Show statistics
        depth: Max depth (0 = unlimited)
        no_unicode: Use ASCII-only characters
        verbose: Verbose output
        color: Use colors
    """
    path = Path(file)
    
    if not path.exists():
        click.echo(f"Error: File not found: {file}", err=True)
        raise SystemExit(1)
    
    # Read source
    source = path.read_text()
    
    # Parse
    try:
        from yuho.parser.scanner import Scanner
        from yuho.parser.parser import Parser
        from yuho.ast.builder import ASTBuilder
        
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        
        parser = Parser(tokens)
        tree = parser.parse()
        
        builder = ASTBuilder()
        ast = builder.build(tree)
        
    except Exception as e:
        click.echo(f"Parse error: {e}", err=True)
        raise SystemExit(1)
    
    # Visualize
    visualizer = ASTVisualizer(use_color=color, use_unicode=not no_unicode)
    tree_output = visualizer.visualize(ast)
    
    # Build output
    lines = []
    
    # Header
    if verbose:
        lines.append(click.style(f"AST for: {path.name}", fg="cyan", bold=True))
        lines.append(click.style("=" * 50, fg="cyan"))
        lines.append("")
    
    lines.append(tree_output)
    
    # Stats
    if stats:
        lines.append("")
        lines.append(click.style("Statistics:", fg="yellow", bold=True))
        lines.append(click.style("-" * 30, fg="yellow"))
        
        ast_stats = format_ast_stats(ast)
        for node_type, count in sorted(ast_stats.items()):
            lines.append(f"  {node_type}: {count}")
        lines.append(f"  {'─' * 20}")
        lines.append(f"  Total nodes: {sum(ast_stats.values())}")
    
    result = "\n".join(lines)
    
    # Output
    if output:
        Path(output).write_text(result)
        click.echo(f"Written to {output}")
    else:
        click.echo(result)
