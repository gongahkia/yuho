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
from typing import Optional, List, Tuple, Dict, Any, Sequence
from dataclasses import dataclass
from enum import Enum, auto

import click

from yuho.parser import get_parser
from yuho.ast import ASTBuilder
from yuho.ast.nodes import (
    CaseLawNode,
    DefinitionEntry,
    ElementGroupNode,
    ElementNode,
    ExceptionNode,
    IllustrationNode,
    ModuleNode,
    PenaltyNode,
    StatuteNode,
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

        # Diff statutes. If each file contains a single different section,
        # treat it as a sibling-offence comparison instead of a pure add/remove.
        if (
            len(old_statutes) == 1
            and len(new_statutes) == 1
            and not (set(old_statutes.keys()) & set(new_statutes.keys()))
        ):
            old_section, old_statute = next(iter(old_statutes.items()))
            new_section, new_statute = next(iter(new_statutes.items()))
            self._diff_sibling_statutes(old_section, old_statute, new_section, new_statute)
        else:
            self._diff_statutes(old_statutes, new_statutes)

        # Diff type definitions
        self._diff_types(old_types, new_types)

        # Diff functions
        self._diff_functions(old_funcs, new_funcs)

        return self.changes

    def _diff_sibling_statutes(
        self,
        old_section: str,
        old_statute: StatuteNode,
        new_section: str,
        new_statute: StatuteNode,
    ) -> None:
        """Compare neighboring offences section-to-section for study workflows."""
        prefix = f"statute.{old_section}_vs_{new_section}"
        old_title = old_statute.title.value if old_statute.title else "(untitled)"
        new_title = new_statute.title.value if new_statute.title else "(untitled)"
        self.changes.append(
            Change(
                change_type=ChangeType.MODIFIED,
                path=f"{prefix}.overview",
                old_value=old_statute,
                new_value=new_statute,
                description=(
                    f"Sibling offence comparison: Section {old_section} ({old_title}) "
                    f"vs Section {new_section} ({new_title})"
                ),
            )
        )
        self._diff_single_statute(
            old_section,
            old_statute,
            new_statute,
            prefix=prefix,
            section_label=f"Sections {old_section} and {new_section}",
        )

    def _diff_statutes(self, old: Dict[str, StatuteNode], new: Dict[str, StatuteNode]) -> None:
        """Diff statute nodes."""
        all_sections = set(old.keys()) | set(new.keys())

        for section in sorted(all_sections):
            if section not in old:
                # Added statute
                title = new[section].title.value if new[section].title else "(untitled)"
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"statute.{section}",
                        new_value=new[section],
                        description=f"Added statute: Section {section} - {title}",
                    )
                )
            elif section not in new:
                # Removed statute
                title = old[section].title.value if old[section].title else "(untitled)"
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"statute.{section}",
                        old_value=old[section],
                        description=f"Removed statute: Section {section} - {title}",
                    )
                )
            else:
                # Compare statutes
                self._diff_single_statute(section, old[section], new[section])

    def _diff_single_statute(
        self,
        section: str,
        old: StatuteNode,
        new: StatuteNode,
        *,
        prefix: Optional[str] = None,
        section_label: Optional[str] = None,
    ) -> None:
        """Diff a single statute's contents."""
        prefix = prefix or f"statute.{section}"
        section_label = section_label or f"Section {section}"

        # Title change
        old_title = old.title.value if old.title else ""
        new_title = new.title.value if new.title else ""
        if old_title != new_title:
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.title",
                    old_value=old_title,
                    new_value=new_title,
                    description=f"{section_label} title: '{old_title}' → '{new_title}'",
                )
            )

        if getattr(old, "subsumes", None) != getattr(new, "subsumes", None):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.subsumes",
                    old_value=getattr(old, "subsumes", None),
                    new_value=getattr(new, "subsumes", None),
                    description=(
                        f"{section_label} subsumption target: "
                        f"{getattr(old, 'subsumes', None) or 'none'} → "
                        f"{getattr(new, 'subsumes', None) or 'none'}"
                    ),
                )
            )

        if getattr(old, "amends", None) != getattr(new, "amends", None):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.amends",
                    old_value=getattr(old, "amends", None),
                    new_value=getattr(new, "amends", None),
                    description=(
                        f"{section_label} amendment target: "
                        f"{getattr(old, 'amends', None) or 'none'} → "
                        f"{getattr(new, 'amends', None) or 'none'}"
                    ),
                )
            )

        # Definitions
        self._diff_definitions(prefix, old.definitions, new.definitions)

        # Elements
        self._diff_elements(prefix, old.elements, new.elements)

        # Penalty
        self._diff_penalty(prefix, old.penalty, new.penalty)

        # Exceptions
        self._diff_exceptions(prefix, old.exceptions, new.exceptions)

        # Illustrations
        self._diff_illustrations(prefix, old.illustrations, new.illustrations)

        # Case law
        self._diff_case_law(prefix, old.case_law, new.case_law)

    def _diff_definitions(
        self, prefix: str, old: Tuple[DefinitionEntry, ...], new: Tuple[DefinitionEntry, ...]
    ) -> None:
        """Diff definition entries."""
        old_defs = {d.term: d.definition.value for d in old}
        new_defs = {d.term: d.definition.value for d in new}

        all_terms = set(old_defs.keys()) | set(new_defs.keys())

        for term in sorted(all_terms):
            if term not in old_defs:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"{prefix}.definitions.{term}",
                        new_value=new_defs[term],
                        description=f"Added definition: '{term}'",
                    )
                )
            elif term not in new_defs:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"{prefix}.definitions.{term}",
                        old_value=old_defs[term],
                        description=f"Removed definition: '{term}'",
                    )
                )
            elif old_defs[term] != new_defs[term]:
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.definitions.{term}",
                        old_value=old_defs[term],
                        new_value=new_defs[term],
                        description=f"Modified definition: '{term}'",
                    )
                )

    def _diff_elements(
        self,
        prefix: str,
        old: Tuple[ElementNode | ElementGroupNode, ...],
        new: Tuple[ElementNode | ElementGroupNode, ...],
    ) -> None:
        """Diff element nodes."""
        # Compare by name for matching
        old_elems = {e.name: e for e in self._flatten_element_members(old)}
        new_elems = {e.name: e for e in self._flatten_element_members(new)}

        all_names = set(old_elems.keys()) | set(new_elems.keys())

        for name in sorted(all_names):
            if name not in old_elems:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"{prefix}.elements.{name}",
                        new_value=new_elems[name],
                        description=f"Added element: {name} ({new_elems[name].element_type})",
                    )
                )
            elif name not in new_elems:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"{prefix}.elements.{name}",
                        old_value=old_elems[name],
                        description=f"Removed element: {name}",
                    )
                )
            else:
                old_e, new_e = old_elems[name], new_elems[name]
                if old_e.element_type != new_e.element_type:
                    self.changes.append(
                        Change(
                            change_type=ChangeType.MODIFIED,
                            path=f"{prefix}.elements.{name}.type",
                            old_value=old_e.element_type,
                            new_value=new_e.element_type,
                            description=f"Element {name} type: {old_e.element_type} → {new_e.element_type}",
                        )
                    )
                # Note: description comparison would require deeper AST comparison

    def _flatten_element_members(
        self, elements: Tuple[ElementNode | ElementGroupNode, ...]
    ) -> List[ElementNode]:
        """Flatten nested element groups for comparison by element name."""
        flattened: List[ElementNode] = []
        for elem in elements:
            if isinstance(elem, ElementNode):
                flattened.append(elem)
            else:
                flattened.extend(self._flatten_element_members(elem.members))
        return flattened

    def _diff_penalty(
        self, prefix: str, old: Optional[PenaltyNode], new: Optional[PenaltyNode]
    ) -> None:
        """Diff penalty nodes."""
        if old is None and new is None:
            return

        if old is None:
            self.changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    path=f"{prefix}.penalty",
                    new_value=new,
                    description="Added penalty clause",
                )
            )
            return

        if new is None:
            self.changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    path=f"{prefix}.penalty",
                    old_value=old,
                    description="Removed penalty clause",
                )
            )
            return

        # Compare imprisonment
        if self._penalty_field_changed(old.imprisonment_max, new.imprisonment_max):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.penalty.imprisonment",
                    old_value=old.imprisonment_max,
                    new_value=new.imprisonment_max,
                    description="Modified imprisonment penalty",
                )
            )

        # Compare fine
        if self._penalty_field_changed(old.fine_max, new.fine_max):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.penalty.fine",
                    old_value=old.fine_max,
                    new_value=new.fine_max,
                    description="Modified fine penalty",
                )
            )

        if self._penalty_field_changed(old.death_penalty, new.death_penalty):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.penalty.death_penalty",
                    old_value=old.death_penalty,
                    new_value=new.death_penalty,
                    description="Modified death-penalty exposure",
                )
            )

        if self._penalty_field_changed(old.supplementary, new.supplementary):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.penalty.supplementary",
                    old_value=old.supplementary,
                    new_value=new.supplementary,
                    description="Modified supplementary sentencing language",
                )
            )

        if self._penalty_field_changed(old.sentencing, new.sentencing):
            self.changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=f"{prefix}.penalty.sentencing",
                    old_value=old.sentencing,
                    new_value=new.sentencing,
                    description="Modified sentencing mode",
                )
            )

    def _penalty_field_changed(self, old: Any, new: Any) -> bool:
        """Check if a penalty field has changed."""
        if old is None and new is None:
            return False
        if old is None or new is None:
            return True
        # Simple comparison - could be enhanced for Duration/Money nodes
        return str(old) != str(new)

    def _diff_illustrations(
        self, prefix: str, old: Tuple[IllustrationNode, ...], new: Tuple[IllustrationNode, ...]
    ) -> None:
        """Diff illustration nodes."""
        old_illustrations = self._illustration_map(old)
        new_illustrations = self._illustration_map(new)

        all_labels = set(old_illustrations.keys()) | set(new_illustrations.keys())
        for label in sorted(all_labels):
            if label not in old_illustrations:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"{prefix}.illustrations.{label}",
                        new_value=new_illustrations[label].description.value,
                        description=f"Added illustration: {label}",
                    )
                )
            elif label not in new_illustrations:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"{prefix}.illustrations.{label}",
                        old_value=old_illustrations[label].description.value,
                        description=f"Removed illustration: {label}",
                    )
                )
            elif (
                old_illustrations[label].description.value
                != new_illustrations[label].description.value
            ):
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.illustrations.{label}",
                        old_value=old_illustrations[label].description.value,
                        new_value=new_illustrations[label].description.value,
                        description=f"Modified illustration: {label}",
                    )
                )

    def _illustration_map(
        self, illustrations: Tuple[IllustrationNode, ...]
    ) -> Dict[str, IllustrationNode]:
        """Index illustrations by label, falling back to stable positional keys."""
        return {
            (illustration.label or f"illustration_{index}"): illustration
            for index, illustration in enumerate(illustrations, start=1)
        }

    def _diff_exceptions(
        self,
        prefix: str,
        old: Tuple[ExceptionNode, ...],
        new: Tuple[ExceptionNode, ...],
    ) -> None:
        """Diff exception labels, effects, and defeasibility metadata."""
        old_exceptions = self._exception_map(old)
        new_exceptions = self._exception_map(new)
        all_labels = set(old_exceptions.keys()) | set(new_exceptions.keys())

        for label in sorted(all_labels):
            if label not in old_exceptions:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"{prefix}.exceptions.{label}",
                        new_value=new_exceptions[label].condition.value,
                        description=f"Added exception: {label}",
                    )
                )
                continue
            if label not in new_exceptions:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"{prefix}.exceptions.{label}",
                        old_value=old_exceptions[label].condition.value,
                        description=f"Removed exception: {label}",
                    )
                )
                continue

            old_exception = old_exceptions[label]
            new_exception = new_exceptions[label]
            if old_exception.condition.value != new_exception.condition.value:
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.exceptions.{label}.condition",
                        old_value=old_exception.condition.value,
                        new_value=new_exception.condition.value,
                        description=f"Modified exception trigger: {label}",
                    )
                )
            if self._optional_string(old_exception.effect) != self._optional_string(
                new_exception.effect
            ):
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.exceptions.{label}.effect",
                        old_value=self._optional_string(old_exception.effect),
                        new_value=self._optional_string(new_exception.effect),
                        description=f"Modified exception effect: {label}",
                    )
                )
            if old_exception.priority != new_exception.priority:
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.exceptions.{label}.priority",
                        old_value=old_exception.priority,
                        new_value=new_exception.priority,
                        description=f"Modified exception priority: {label}",
                    )
                )
            if old_exception.defeats != new_exception.defeats:
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.exceptions.{label}.defeats",
                        old_value=old_exception.defeats,
                        new_value=new_exception.defeats,
                        description=f"Modified exception defeat target: {label}",
                    )
                )

    def _exception_map(self, exceptions: Tuple[ExceptionNode, ...]) -> Dict[str, ExceptionNode]:
        """Index exceptions by student-facing label."""
        return {
            (exception.label or f"exception_{index}"): exception
            for index, exception in enumerate(exceptions, start=1)
        }

    def _diff_case_law(
        self,
        prefix: str,
        old: Tuple[CaseLawNode, ...],
        new: Tuple[CaseLawNode, ...],
    ) -> None:
        """Diff case-law authorities and holdings."""
        old_cases = self._case_law_map(old)
        new_cases = self._case_law_map(new)
        all_cases = set(old_cases.keys()) | set(new_cases.keys())

        for case_name in sorted(all_cases):
            if case_name not in old_cases:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"{prefix}.case_law.{case_name}",
                        new_value=new_cases[case_name].holding.value,
                        description=f"Added case law authority: {case_name}",
                    )
                )
                continue
            if case_name not in new_cases:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"{prefix}.case_law.{case_name}",
                        old_value=old_cases[case_name].holding.value,
                        description=f"Removed case law authority: {case_name}",
                    )
                )
                continue

            old_case = old_cases[case_name]
            new_case = new_cases[case_name]
            if old_case.holding.value != new_case.holding.value:
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.case_law.{case_name}.holding",
                        old_value=old_case.holding.value,
                        new_value=new_case.holding.value,
                        description=f"Modified case law holding: {case_name}",
                    )
                )
            if self._optional_string(old_case.citation) != self._optional_string(new_case.citation):
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.case_law.{case_name}.citation",
                        old_value=self._optional_string(old_case.citation),
                        new_value=self._optional_string(new_case.citation),
                        description=f"Modified case law citation: {case_name}",
                    )
                )
            if old_case.element_ref != new_case.element_ref:
                self.changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path=f"{prefix}.case_law.{case_name}.element_ref",
                        old_value=old_case.element_ref,
                        new_value=new_case.element_ref,
                        description=f"Modified case law element link: {case_name}",
                    )
                )

    def _case_law_map(self, cases: Tuple[CaseLawNode, ...]) -> Dict[str, CaseLawNode]:
        """Index case-law references by case name."""
        return {case.case_name.value: case for case in cases}

    def _optional_string(self, value: Optional[object]) -> Optional[str]:
        """Normalize optional AST/string fields for diff output."""
        if value is None:
            return None
        return getattr(value, "value", str(value))

    def _diff_types(self, old: Dict, new: Dict) -> None:
        """Diff type definitions."""
        all_names = set(old.keys()) | set(new.keys())

        for name in sorted(all_names):
            if name not in old:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"type.{name}",
                        description=f"Added type: {name}",
                    )
                )
            elif name not in new:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"type.{name}",
                        description=f"Removed type: {name}",
                    )
                )

    def _diff_functions(self, old: Dict, new: Dict) -> None:
        """Diff function definitions."""
        all_names = set(old.keys()) | set(new.keys())

        for name in sorted(all_names):
            if name not in old:
                self.changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        path=f"function.{name}",
                        description=f"Added function: {name}",
                    )
                )
            elif name not in new:
                self.changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        path=f"function.{name}",
                        description=f"Removed function: {name}",
                    )
                )


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
            },
        }
        print(json_module.dumps(output, indent=2))
    else:
        if verbose:
            click.echo(f"Comparing: {path1} ↔ {path2}")
            click.echo("")

        formatted_output = format_diff(changes, color=color)
        click.echo(formatted_output)

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
                color_code = (
                    Colors.CYAN if pct == 100 else Colors.YELLOW if pct >= 50 else Colors.RED
                )
                click.echo(f"  {category}: {c(f'{matched}/{total}', color_code)} ({pct:.0f}%)")
                for m in data.get("missing", []):
                    click.echo(c(f"    missing: {m}", Colors.RED))
        click.echo()
        overall = scores["overall_percent"]
        overall_color = (
            Colors.CYAN if overall == 100 else Colors.YELLOW if overall >= 50 else Colors.RED
        )
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
            "total": len(model_defs),
            "matched": len(matched_defs),
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
            "total": len(model_elems),
            "matched": len(matched_elems),
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
            "total": penalty_total,
            "matched": penalty_match,
            "missing": ["penalty block"] if has_model_penalty and not has_student_penalty else [],
        }
        total_items += penalty_total
        matched_items += penalty_match

        model_penalty_signature = _penalty_signature(model_s.penalty)
        student_penalty_signature = _penalty_signature(student_s.penalty) if student_s else None
        penalty_detail_total = 1 if model_penalty_signature else 0
        penalty_detail_matched = int(
            bool(model_penalty_signature) and model_penalty_signature == student_penalty_signature
        )
        categories["penalty_detail"] = {
            "total": penalty_detail_total,
            "matched": penalty_detail_matched,
            "missing": (
                ["penalty details differ"]
                if model_penalty_signature and model_penalty_signature != student_penalty_signature
                else []
            ),
        }
        total_items += penalty_detail_total
        matched_items += penalty_detail_matched

        # exceptions
        model_exc = {e.label for e in model_s.exceptions if e.label}
        student_exc = {e.label for e in student_s.exceptions if e.label} if student_s else set()
        matched_exc = model_exc & student_exc
        missing_exc = model_exc - student_exc
        categories["exceptions"] = {
            "total": len(model_exc),
            "matched": len(matched_exc),
            "missing": sorted(missing_exc),
        }
        total_items += len(model_exc)
        matched_items += len(matched_exc)

        model_cases = {case.case_name.value for case in model_s.case_law}
        student_cases = (
            {case.case_name.value for case in student_s.case_law} if student_s else set()
        )
        matched_cases = model_cases & student_cases
        missing_cases = model_cases - student_cases
        categories["case_law"] = {
            "total": len(model_cases),
            "matched": len(matched_cases),
            "missing": sorted(missing_cases),
        }
        total_items += len(model_cases)
        matched_items += len(matched_cases)

        model_related = {
            relation
            for relation in (getattr(model_s, "subsumes", None), getattr(model_s, "amends", None))
            if relation
        }
        student_related = (
            {
                relation
                for relation in (
                    getattr(student_s, "subsumes", None),
                    getattr(student_s, "amends", None),
                )
                if relation
            }
            if student_s
            else set()
        )
        matched_related = model_related & student_related
        missing_related = model_related - student_related
        categories["related_sections"] = {
            "total": len(model_related),
            "matched": len(matched_related),
            "missing": sorted(missing_related),
        }
        total_items += len(model_related)
        matched_items += len(matched_related)

        statute_scores.append({"section": section, "categories": categories})
    overall = (matched_items / total_items * 100) if total_items > 0 else 100
    return {
        "statutes": statute_scores,
        "total_items": total_items,
        "matched_items": matched_items,
        "overall_percent": round(overall, 1),
    }


def _collect_element_names(elements: Sequence[ElementNode | ElementGroupNode]) -> set[str]:
    """Recursively collect element names from elements/groups."""
    names: set[str] = set()
    for elem in elements:
        if isinstance(elem, ElementNode):
            names.add(elem.name)
        elif isinstance(elem, ElementGroupNode):
            names.update(_collect_element_names(elem.members))
    return names


def _penalty_signature(penalty: Optional[PenaltyNode]) -> Optional[Tuple[str, ...]]:
    """Reduce penalties to a comparable doctrinal signature."""
    if penalty is None:
        return None
    return (
        str(penalty.imprisonment_min),
        str(penalty.imprisonment_max),
        str(penalty.fine_min),
        str(penalty.fine_max),
        str(penalty.death_penalty),
        str(penalty.supplementary.value if penalty.supplementary else None),
        str(penalty.sentencing),
    )
