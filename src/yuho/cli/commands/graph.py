"""
Graph command - visualize statute dependencies.

Generates dependency graphs in DOT or Mermaid format showing:
- Statute cross-references
- Import relationships
- Type dependencies
- Function call graphs
"""

import sys
from pathlib import Path
from typing import Optional, List, Set, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.ast.nodes import (
    ModuleNode, StatuteNode, ImportNode, IdentifierNode,
    FunctionCallNode, FieldAccessNode
)
from yuho.ast.visitor import Visitor
from yuho.cli.error_formatter import Colors, colorize


class GraphFormat(Enum):
    """Supported graph output formats."""
    DOT = "dot"
    MERMAID = "mermaid"


@dataclass
class GraphNode:
    """A node in the dependency graph."""
    id: str
    label: str
    node_type: str  # "statute", "import", "type", "function"
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, GraphNode) and self.id == other.id


@dataclass
class GraphEdge:
    """An edge in the dependency graph."""
    source: str
    target: str
    edge_type: str  # "references", "imports", "calls", "uses"
    label: str = ""
    
    def __hash__(self):
        return hash((self.source, self.target, self.edge_type))
    
    def __eq__(self, other):
        return (isinstance(other, GraphEdge) and 
                self.source == other.source and 
                self.target == other.target and
                self.edge_type == other.edge_type)


@dataclass
class DependencyGraph:
    """Represents the full dependency graph."""
    nodes: Set[GraphNode] = field(default_factory=set)
    edges: Set[GraphEdge] = field(default_factory=set)
    
    def add_node(self, node: GraphNode) -> None:
        self.nodes.add(node)
    
    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.add(edge)


class DependencyExtractor(Visitor):
    """
    Extract dependencies from a Yuho AST.
    
    Identifies:
    - Statute cross-references (via section numbers)
    - Import statements
    - Type usages
    - Function calls
    """

    def __init__(self):
        self.graph = DependencyGraph()
        self._current_context: Optional[str] = None

    def extract(self, ast: ModuleNode, filename: str = "main") -> DependencyGraph:
        """Extract dependency graph from AST."""
        self.graph = DependencyGraph()
        self._current_context = None
        
        # Add module node
        module_id = f"module:{filename}"
        self.graph.add_node(GraphNode(
            id=module_id,
            label=filename,
            node_type="module"
        ))
        
        # Process imports
        for imp in ast.imports:
            self._process_import(module_id, imp)
        
        # Process type definitions
        for type_def in ast.type_defs:
            type_id = f"type:{type_def.name}"
            self.graph.add_node(GraphNode(
                id=type_id,
                label=type_def.name,
                node_type="type"
            ))
            self.graph.add_edge(GraphEdge(
                source=module_id,
                target=type_id,
                edge_type="defines"
            ))
        
        # Process functions
        for func in ast.function_defs:
            func_id = f"function:{func.name}"
            self.graph.add_node(GraphNode(
                id=func_id,
                label=func.name,
                node_type="function"
            ))
            self.graph.add_edge(GraphEdge(
                source=module_id,
                target=func_id,
                edge_type="defines"
            ))
        
        # Process statutes
        for statute in ast.statutes:
            self._process_statute(module_id, statute)
        
        return self.graph

    def _process_import(self, module_id: str, imp: ImportNode) -> None:
        """Process import statement."""
        import_id = f"import:{imp.path}"
        self.graph.add_node(GraphNode(
            id=import_id,
            label=imp.path,
            node_type="import"
        ))
        
        if imp.is_wildcard:
            label = "*"
        elif imp.imported_names:
            label = ", ".join(imp.imported_names[:3])
            if len(imp.imported_names) > 3:
                label += "..."
        else:
            label = ""
        
        self.graph.add_edge(GraphEdge(
            source=module_id,
            target=import_id,
            edge_type="imports",
            label=label
        ))

    def _process_statute(self, module_id: str, statute: StatuteNode) -> None:
        """Process statute node."""
        statute_id = f"statute:{statute.section_number}"
        title = statute.title.value if statute.title else f"Section {statute.section_number}"
        
        self.graph.add_node(GraphNode(
            id=statute_id,
            label=f"S.{statute.section_number}\\n{title[:30]}",
            node_type="statute"
        ))
        
        self.graph.add_edge(GraphEdge(
            source=module_id,
            target=statute_id,
            edge_type="contains"
        ))
        
        # Look for cross-references in definitions and elements
        self._current_context = statute_id
        
        # Check definitions for section references
        for defn in statute.definitions:
            self._extract_section_refs(statute_id, defn.definition.value)
        
        # Check illustrations
        for illus in statute.illustrations:
            self._extract_section_refs(statute_id, illus.description.value)

    def _extract_section_refs(self, source_id: str, text: str) -> None:
        """Extract section number references from text."""
        import re
        
        # Patterns for section references
        patterns = [
            r'[Ss]ection\s+(\d+[A-Za-z]*)',
            r'[Ss]\.\s*(\d+[A-Za-z]*)',
            r'§\s*(\d+[A-Za-z]*)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                ref_section = match.group(1)
                ref_id = f"statute:{ref_section}"
                
                # Add target node if not exists
                self.graph.add_node(GraphNode(
                    id=ref_id,
                    label=f"S.{ref_section}",
                    node_type="statute"
                ))
                
                # Add reference edge
                self.graph.add_edge(GraphEdge(
                    source=source_id,
                    target=ref_id,
                    edge_type="references"
                ))


def generate_dot(graph: DependencyGraph, title: str = "Yuho Dependencies") -> str:
    """
    Generate DOT format graph.
    
    Args:
        graph: The dependency graph
        title: Graph title
        
    Returns:
        DOT format string
    """
    lines = [
        f'digraph "{title}" {{',
        '  rankdir=TB;',
        '  node [fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=8];',
        '',
    ]
    
    # Node styles by type
    node_styles = {
        "module": 'shape=box, style=filled, fillcolor="#E8F4F8"',
        "statute": 'shape=box, style="filled,rounded", fillcolor="#FFF3CD"',
        "import": 'shape=ellipse, style=filled, fillcolor="#D4EDDA"',
        "type": 'shape=hexagon, style=filled, fillcolor="#F8D7DA"',
        "function": 'shape=ellipse, style=filled, fillcolor="#CCE5FF"',
    }
    
    # Add nodes
    for node in sorted(graph.nodes, key=lambda n: n.id):
        style = node_styles.get(node.node_type, '')
        safe_label = node.label.replace('"', '\\"')
        lines.append(f'  "{node.id}" [label="{safe_label}", {style}];')
    
    lines.append('')
    
    # Edge styles by type
    edge_styles = {
        "imports": 'style=dashed, color="#28a745"',
        "references": 'style=solid, color="#dc3545"',
        "defines": 'style=solid, color="#6c757d"',
        "contains": 'style=dotted, color="#6c757d"',
        "calls": 'style=solid, color="#007bff"',
        "uses": 'style=dashed, color="#17a2b8"',
    }
    
    # Add edges
    for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
        style = edge_styles.get(edge.edge_type, '')
        label_part = f', label="{edge.label}"' if edge.label else ''
        lines.append(f'  "{edge.source}" -> "{edge.target}" [{style}{label_part}];')
    
    lines.append('}')
    return '\n'.join(lines)


def generate_mermaid(graph: DependencyGraph, title: str = "Yuho Dependencies") -> str:
    """
    Generate Mermaid format graph.
    
    Args:
        graph: The dependency graph
        title: Graph title
        
    Returns:
        Mermaid format string
    """
    lines = [
        '```mermaid',
        'flowchart TB',
        f'    %% {title}',
        '',
    ]
    
    # Node shapes by type
    def node_shape(node: GraphNode) -> str:
        safe_label = node.label.replace('"', "'").replace('\n', ' ')
        shapes = {
            "module": f'["{safe_label}"]',
            "statute": f'("{safe_label}")',
            "import": f'[["{safe_label}"]]',
            "type": f'{{{{{safe_label}}}}}',
            "function": f'(["{safe_label}"])',
        }
        return shapes.get(node.node_type, f'["{safe_label}"]')
    
    # Sanitize ID for Mermaid
    def safe_id(id: str) -> str:
        return id.replace(":", "_").replace(".", "_").replace("/", "_")
    
    # Add nodes
    for node in sorted(graph.nodes, key=lambda n: n.id):
        sid = safe_id(node.id)
        lines.append(f'    {sid}{node_shape(node)}')
    
    lines.append('')
    
    # Edge styles
    edge_arrows = {
        "imports": "-.->",
        "references": "-->",
        "defines": "-->",
        "contains": "-.->",
        "calls": "-->",
        "uses": "-.->",
    }
    
    # Add edges
    for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
        src = safe_id(edge.source)
        tgt = safe_id(edge.target)
        arrow = edge_arrows.get(edge.edge_type, "-->")
        if edge.label:
            lines.append(f'    {src} {arrow}|{edge.label}| {tgt}')
        else:
            lines.append(f'    {src} {arrow} {tgt}')
    
    lines.append('```')
    return '\n'.join(lines)


def run_graph(
    file: str,
    format: str = "mermaid",
    output: Optional[str] = None,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Generate dependency graph for a Yuho file.
    
    Args:
        file: Path to the .yh file
        format: Output format (dot or mermaid)
        output: Output file path (stdout if None)
        verbose: Enable verbose output
        color: Use colored output
    """
    path = Path(file)
    
    if not path.exists():
        click.echo(colorize(f"error: File not found: {file}", Colors.RED), err=True)
        sys.exit(1)
    
    # Parse file
    parser = Parser()
    result = parser.parse_file(path)
    
    if result.errors:
        click.echo(colorize(f"error: Parse errors in {file}:", Colors.RED), err=True)
        for err in result.errors[:3]:
            click.echo(f"  {err.message}", err=True)
        sys.exit(1)
    
    # Build AST
    builder = ASTBuilder()
    ast = builder.build(result.tree)
    
    # Extract dependencies
    extractor = DependencyExtractor()
    graph = extractor.extract(ast, path.stem)
    
    if verbose:
        click.echo(f"Extracted {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    # Generate output
    graph_format = GraphFormat(format.lower())
    
    if graph_format == GraphFormat.DOT:
        output_str = generate_dot(graph, title=f"Dependencies: {path.name}")
    else:
        output_str = generate_mermaid(graph, title=f"Dependencies: {path.name}")
    
    # Write output
    if output:
        out_path = Path(output)
        out_path.write_text(output_str)
        if verbose:
            click.echo(f"Wrote graph to {out_path}")
    else:
        print(output_str)
