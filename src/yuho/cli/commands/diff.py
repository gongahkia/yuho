"""
Diff command - compare statute versions and show changes.

Provides semantic diff between two Yuho files or statute versions,
showing:
- Added/removed statutes
- Changed definitions
- Modified elements
- Penalty changes
- Illustration differences
"""

import sys
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum, auto

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.ast.nodes import (
    ModuleNode, StatuteNode, ElementNode, PenaltyNode,
    DefinitionEntry, IllustrationNode, StringLit
)
from yuho.cli.error_formatter import Colors, colorize


class ChangeType(Enum):
    """Type of change detected."""
    ADDED = auto()
    REMOVED = auto()
    MODIFIED = auto()
    UNCHANGED = auto()


@dataclass
class Change:
    """Represents a single change between versions."""
    change_type: ChangeType
    path: str  # e.g., "statute.299.elements.0"
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    description: str = ""


class StatuteDiffer:
    """
    Computes semantic diff between two Yuho ASTs.
    
    Focuses on meaningful changes rather than syntactic differences.
    """

    def __init__(self):
        self.changes: List[Change] = []

    def diff(self, old_ast: ModuleNode, new_ast: ModuleNode) -> List[Change]:
        """
        Compute diff between two ASTs.
        
        Args:
            old_ast: The original/baseline AST
            new_ast: The new/modified AST
            
        Returns:
            List of changes detected
        """
        self.changes = []
        
        # Build lookup maps
        old_statutes = {s.section_number: s for s in old_ast.statutes}
        new_statutes = {s.section_number: s for s in new_ast.statutes}
        
        old_types = {t.name: t for t in old_ast.type_defs}
        new_types = {t.name: t for t in new_ast.type_defs}
        
        old_funcs = {f.name: f for f in old_ast.function_defs}
        new_funcs = {f.name: f for f in new_ast.function_defs}
        
        # Diff statutes
        self._diff_statutes(old_statutes, new_statutes)
        
        # Diff type definitions
        self._diff_types(old_types, new_types)
        
        # Diff functions
        self._diff_functions(old_funcs, new_funcs)
        
        return self.changes

    def _diff_statutes(
        self,
        old: Dict[str, StatuteNode],
        new: Dict[str, StatuteNode]
    ) -> None:
        """Diff statute nodes."""
        all_sections = set(old.keys()) | set(new.keys())
        
        for section in sorted(all_sections):
            if section not in old:
                # Added statute
                title = new[section].title.value if new[section].title else "(untitled)"
                self.changes.append(Change(
                    change_type=ChangeType.ADDED,
                    path=f"statute.{section}",
                    new_value=new[section],
                    description=f"Added statute: Section {section} - {title}"
                ))
            elif section not in new:
                # Removed statute
                title = old[section].title.value if old[section].title else "(untitled)"
                self.changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    path=f"statute.{section}",
                    old_value=old[section],
                    description=f"Removed statute: Section {section} - {title}"
                ))
            else:
                # Compare statutes
                self._diff_single_statute(section, old[section], new[section])

    def _diff_single_statute(
        self,
        section: str,
        old: StatuteNode,
        new: StatuteNode
    ) -> None:
        """Diff a single statute's contents."""
        prefix = f"statute.{section}"
        
        # Title change
        old_title = old.title.value if old.title else ""
        new_title = new.title.value if new.title else ""
        if old_title != new_title:
            self.changes.append(Change(
                change_type=ChangeType.MODIFIED,
                path=f"{prefix}.title",
                old_value=old_title,
                new_value=new_title,
                description=f"Section {section} title: '{old_title}' → '{new_title}'"
            ))
        
        # Definitions
        self._diff_definitions(prefix, old.definitions, new.definitions)
        
        # Elements
        self._diff_elements(prefix, old.elements, new.elements)
        
        # Penalty
        self._diff_penalty(prefix, old.penalty, new.penalty)
        
        # Illustrations
        self._diff_illustrations(prefix, old.illustrations, new.illustrations)

    def _diff_definitions(
        self,
        prefix: str,
        old: Tuple[DefinitionEntry, ...],
        new: Tuple[DefinitionEntry, ...]
    ) -> None:
        """Diff definition entries."""
        old_defs = {d.term: d.definition.value for d in old}
        new_defs = {d.term: d.definition.value for d in new}
        
        all_terms = set(old_defs.keys()) | set(new_defs.keys())
        
        for term in sorted(all_terms):
            if term not in old_defs:
                self.changes.append(Change(
                    change_type=ChangeType.ADDED,
                    path=f"{prefix}.definitions.{term}",
                    new_value=new_defs[term],
                    description=f"Added definition: '{term}'"
                ))
            elif term not in new_defs:
                self.changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    path=f"{prefix}.definitions.{term}",
                    old_value=old_defs[term],
                    description=f"Removed definition: '{term}'"
                ))
            elif old_defs[term] != new_defs[term]:
                self.changes.append(Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.definitions.{term}",
                    old_value=old_defs[term],
                    new_value=new_defs[term],
                    description=f"Modified definition: '{term}'"
                ))

    def _diff_elements(
        self,
        prefix: str,
        old: Tuple[ElementNode, ...],
        new: Tuple[ElementNode, ...]
    ) -> None:
        """Diff element nodes."""
        # Compare by name for matching
        old_elems = {e.name: e for e in old}
        new_elems = {e.name: e for e in new}
        
        all_names = set(old_elems.keys()) | set(new_elems.keys())
        
        for name in sorted(all_names):
            if name not in old_elems:
                self.changes.append(Change(
                    change_type=ChangeType.ADDED,
                    path=f"{prefix}.elements.{name}",
                    new_value=new_elems[name],
                    description=f"Added element: {name} ({new_elems[name].element_type})"
                ))
            elif name not in new_elems:
                self.changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    path=f"{prefix}.elements.{name}",
                    old_value=old_elems[name],
                    description=f"Removed element: {name}"
                ))
            else:
                old_e, new_e = old_elems[name], new_elems[name]
                if old_e.element_type != new_e.element_type:
                    self.changes.append(Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.elements.{name}.type",
                        old_value=old_e.element_type,
                        new_value=new_e.element_type,
                        description=f"Element {name} type: {old_e.element_type} → {new_e.element_type}"
                    ))
                # Note: description comparison would require deeper AST comparison

    def _diff_penalty(
        self,
        prefix: str,
        old: Optional[PenaltyNode],
        new: Optional[PenaltyNode]
    ) -> None:
        """Diff penalty nodes."""
        if old is None and new is None:
            return
        
        if old is None:
            self.changes.append(Change(
                change_type=ChangeType.ADDED,
                path=f"{prefix}.penalty",
                new_value=new,
                description="Added penalty clause"
            ))
            return
        
        if new is None:
            self.changes.append(Change(
                change_type=ChangeType.REMOVED,
                path=f"{prefix}.penalty",
                old_value=old,
                description="Removed penalty clause"
            ))
            return
        
        # Compare imprisonment
        if self._penalty_field_changed(old.imprisonment_max, new.imprisonment_max):
            self.changes.append(Change(
                change_type=ChangeType.MODIFIED,
                path=f"{prefix}.penalty.imprisonment",
                old_value=old.imprisonment_max,
                new_value=new.imprisonment_max,
                description="Modified imprisonment penalty"
            ))
        
        # Compare fine
        if self._penalty_field_changed(old.fine_max, new.fine_max):
            self.changes.append(Change(
                change_type=ChangeType.MODIFIED,
                path=f"{prefix}.penalty.fine",
                old_value=old.fine_max,
                new_value=new.fine_max,
                description="Modified fine penalty"
            ))

    def _penalty_field_changed(self, old: Any, new: Any) -> bool:
        """Check if a penalty field has changed."""
        if old is None and new is None:
            return False
        if old is None or new is None:
            return True
        # Simple comparison - could be enhanced for Duration/Money nodes
        return str(old) != str(new)

    def _diff_illustrations(
        self,
        prefix: str,
        old: Tuple[IllustrationNode, ...],
        new: Tuple[IllustrationNode, ...]
    ) -> None:
        """Diff illustration nodes."""
        old_count = len(old)
        new_count = len(new)
        
        if old_count != new_count:
            if new_count > old_count:
                self.changes.append(Change(
                    change_type=ChangeType.ADDED,
                    path=f"{prefix}.illustrations",
                    description=f"Added {new_count - old_count} illustration(s)"
                ))
            else:
                self.changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    path=f"{prefix}.illustrations",
                    description=f"Removed {old_count - new_count} illustration(s)"
                ))

    def _diff_types(self, old: Dict, new: Dict) -> None:
        """Diff type definitions."""
        all_names = set(old.keys()) | set(new.keys())
        
        for name in sorted(all_names):
            if name not in old:
                self.changes.append(Change(
                    change_type=ChangeType.ADDED,
                    path=f"type.{name}",
                    description=f"Added type: {name}"
                ))
            elif name not in new:
                self.changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    path=f"type.{name}",
                    description=f"Removed type: {name}"
                ))

    def _diff_functions(self, old: Dict, new: Dict) -> None:
        """Diff function definitions."""
        all_names = set(old.keys()) | set(new.keys())
        
        for name in sorted(all_names):
            if name not in old:
                self.changes.append(Change(
                    change_type=ChangeType.ADDED,
                    path=f"function.{name}",
                    description=f"Added function: {name}"
                ))
            elif name not in new:
                self.changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    path=f"function.{name}",
                    description=f"Removed function: {name}"
                ))


def format_diff(changes: List[Change], color: bool = True) -> str:
    """
    Format diff output for terminal display.
    
    Args:
        changes: List of changes to format
        color: Whether to use colors
        
    Returns:
        Formatted diff string
    """
    if not changes:
        return "No changes detected."
    
    lines: List[str] = []
    
    # Group by change type
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
    modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]
    
    def c(text: str, col: str) -> str:
        return colorize(text, col) if color else text
    
    # Summary
    summary_parts = []
    if added:
        summary_parts.append(c(f"+{len(added)} added", Colors.GREEN))
    if removed:
        summary_parts.append(c(f"-{len(removed)} removed", Colors.RED))
    if modified:
        summary_parts.append(c(f"~{len(modified)} modified", Colors.YELLOW))
    
    lines.append(f"Changes: {', '.join(summary_parts)}")
    lines.append("")
    
    # Details
    if added:
        lines.append(c("Added:", Colors.GREEN))
        for change in added:
            lines.append(f"  + {change.description}")
        lines.append("")
    
    if removed:
        lines.append(c("Removed:", Colors.RED))
        for change in removed:
            lines.append(f"  - {change.description}")
        lines.append("")
    
    if modified:
        lines.append(c("Modified:", Colors.YELLOW))
        for change in modified:
            lines.append(f"  ~ {change.description}")
        lines.append("")
    
    return "\n".join(lines)


def run_diff(
    file1: str,
    file2: str,
    json_output: bool = False,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Compare two Yuho files and show differences.
    
    Args:
        file1: Path to the first (old) file
        file2: Path to the second (new) file
        json_output: Output as JSON
        verbose: Enable verbose output
        color: Use colored output
    """
    import json as json_module
    
    path1, path2 = Path(file1), Path(file2)
    
    # Validate files exist
    for path in [path1, path2]:
        if not path.exists():
            click.echo(colorize(f"error: File not found: {path}", Colors.RED), err=True)
            sys.exit(1)
    
    parser = Parser()
    
    # Parse both files
    def parse_file(path: Path) -> Optional[ModuleNode]:
        result = parser.parse_file(path)
        if result.errors:
            click.echo(colorize(f"error: Parse errors in {path}:", Colors.RED), err=True)
            for err in result.errors[:3]:
                click.echo(f"  {err.message}", err=True)
            return None
        builder = ASTBuilder(result.source, result.file)
        return builder.build(result.tree.root_node)
    
    ast1 = parse_file(path1)
    ast2 = parse_file(path2)
    
    if ast1 is None or ast2 is None:
        sys.exit(1)
    
    # Compute diff
    differ = StatuteDiffer()
    changes = differ.diff(ast1, ast2)
    
    if json_output:
        output = {
            "file1": str(path1),
            "file2": str(path2),
            "changes": [
                {
                    "type": c.change_type.name.lower(),
                    "path": c.path,
                    "description": c.description,
                }
                for c in changes
            ],
            "summary": {
                "added": len([c for c in changes if c.change_type == ChangeType.ADDED]),
                "removed": len([c for c in changes if c.change_type == ChangeType.REMOVED]),
                "modified": len([c for c in changes if c.change_type == ChangeType.MODIFIED]),
            }
        }
        print(json_module.dumps(output, indent=2))
    else:
        if verbose:
            click.echo(f"Comparing: {path1} ↔ {path2}")
            click.echo("")
        
        output = format_diff(changes, color=color)
        click.echo(output)
    
    # Exit with code 1 if there are changes (useful for CI)
    if changes:
        sys.exit(1)
