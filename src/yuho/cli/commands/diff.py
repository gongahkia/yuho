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

from yuho.parser import get_parser
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
    from yuho.parser.wrapper import validate_file_path
    try:
        path1 = validate_file_path(file1)
        path2 = validate_file_path(file2)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)
    
    parser = get_parser()
    
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


def run_diff_score(
    model_file: str,
    student_file: str,
    json_output: bool = False,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Score a student file against a model answer.

    Computes element coverage: what fraction of the model's elements,
    definitions, and penalties the student file also contains.
    """
    import json as json_module
    from yuho.parser.wrapper import validate_file_path
    try:
        model_path = validate_file_path(model_file)
        student_path = validate_file_path(student_file)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)
    parser = get_parser()

    def parse_file(path: Path) -> Optional[ModuleNode]:
        result = parser.parse_file(path)
        if result.errors:
            click.echo(colorize(f"error: Parse errors in {path}:", Colors.RED), err=True)
            return None
        builder = ASTBuilder(result.source, result.file)
        return builder.build(result.tree.root_node)

    model_ast = parse_file(model_path)
    student_ast = parse_file(student_path)
    if model_ast is None or student_ast is None:
        sys.exit(1)

    scores = _compute_coverage_score(model_ast, student_ast)
    if json_output:
        print(json_module.dumps(scores, indent=2))
    else:
        c = lambda t, clr: colorize(t, clr) if color else t
        click.echo(f"Model: {model_path}")
        click.echo(f"Student: {student_path}")
        click.echo()
        for statute_score in scores["statutes"]:
            section = statute_score["section"]
            click.echo(c(f"Section {section}:", Colors.BOLD))
            for category, data in statute_score["categories"].items():
                matched = data["matched"]
                total = data["total"]
                pct = (matched / total * 100) if total > 0 else 100
                color_code = Colors.CYAN if pct == 100 else Colors.YELLOW if pct >= 50 else Colors.RED
                click.echo(f"  {category}: {c(f'{matched}/{total}', color_code)} ({pct:.0f}%)")
                for m in data.get("missing", []):
                    click.echo(c(f"    missing: {m}", Colors.RED))
        click.echo()
        overall = scores["overall_percent"]
        overall_color = Colors.CYAN if overall == 100 else Colors.YELLOW if overall >= 50 else Colors.RED
        click.echo(f"Overall: {c(f'{overall:.0f}%', overall_color + Colors.BOLD)}")


def _compute_coverage_score(model: ModuleNode, student: ModuleNode) -> dict:
    """Compute coverage of model elements in student submission."""
    model_statutes = {s.section_number: s for s in model.statutes}
    student_statutes = {s.section_number: s for s in student.statutes}
    total_items = 0
    matched_items = 0
    statute_scores = []
    for section, model_s in model_statutes.items():
        student_s = student_statutes.get(section)
        categories = {}
        # definitions
        model_defs = {d.term for d in model_s.definitions}
        student_defs = {d.term for d in student_s.definitions} if student_s else set()
        matched_defs = model_defs & student_defs
        missing_defs = model_defs - student_defs
        categories["definitions"] = {
            "total": len(model_defs), "matched": len(matched_defs),
            "missing": sorted(missing_defs),
        }
        total_items += len(model_defs)
        matched_items += len(matched_defs)
        # elements
        model_elems = _collect_element_names(model_s.elements)
        student_elems = _collect_element_names(student_s.elements) if student_s else set()
        matched_elems = model_elems & student_elems
        missing_elems = model_elems - student_elems
        categories["elements"] = {
            "total": len(model_elems), "matched": len(matched_elems),
            "missing": sorted(missing_elems),
        }
        total_items += len(model_elems)
        matched_items += len(matched_elems)
        # penalty
        has_model_penalty = model_s.penalty is not None
        has_student_penalty = student_s.penalty is not None if student_s else False
        penalty_match = 1 if has_model_penalty and has_student_penalty else 0
        penalty_total = 1 if has_model_penalty else 0
        categories["penalty"] = {
            "total": penalty_total, "matched": penalty_match,
            "missing": ["penalty block"] if has_model_penalty and not has_student_penalty else [],
        }
        total_items += penalty_total
        matched_items += penalty_match
        # exceptions
        model_exc = {e.label for e in model_s.exceptions if e.label}
        student_exc = {e.label for e in student_s.exceptions if e.label} if student_s else set()
        matched_exc = model_exc & student_exc
        missing_exc = model_exc - student_exc
        categories["exceptions"] = {
            "total": len(model_exc), "matched": len(matched_exc),
            "missing": sorted(missing_exc),
        }
        total_items += len(model_exc)
        matched_items += len(matched_exc)
        statute_scores.append({"section": section, "categories": categories})
    overall = (matched_items / total_items * 100) if total_items > 0 else 100
    return {"statutes": statute_scores, "total_items": total_items, "matched_items": matched_items, "overall_percent": round(overall, 1)}


def _collect_element_names(elements) -> set:
    """Recursively collect element names from elements/groups."""
    from yuho.ast.nodes import ElementNode, ElementGroupNode
    names = set()
    for elem in elements:
        if isinstance(elem, ElementNode):
            names.add(elem.name)
        elif isinstance(elem, ElementGroupNode):
            names.update(_collect_element_names(elem.members))
    return names
