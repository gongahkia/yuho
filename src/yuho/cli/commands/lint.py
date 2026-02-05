"""
Lint command - style checking and best practices.

Analyzes Yuho files for:
- Style violations (naming conventions, formatting)
- Best practice violations (missing elements, incomplete statutes)
- Potential issues (undefined references, unused definitions)
- Documentation quality (missing titles, empty descriptions)
"""

import sys
import re
from pathlib import Path
from typing import Optional, List, Set, Dict
from dataclasses import dataclass
from enum import Enum, auto

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.ast.nodes import (
    ModuleNode, StatuteNode, ElementNode, PenaltyNode,
    DefinitionEntry, IllustrationNode, StructDefNode,
    FunctionDefNode, StringLit
)
from yuho.cli.error_formatter import Colors, colorize


class Severity(Enum):
    """Lint issue severity levels."""
    ERROR = auto()    # Must fix
    WARNING = auto()  # Should fix
    INFO = auto()     # Style suggestion
    HINT = auto()     # Optional improvement


@dataclass
class LintIssue:
    """A single lint issue."""
    rule: str
    severity: Severity
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        loc = f":{self.line}" if self.line else ""
        if self.column:
            loc += f":{self.column}"
        return f"[{self.rule}] {self.message}{loc}"


class LintRule:
    """Base class for lint rules."""
    
    id: str = "base"
    severity: Severity = Severity.WARNING
    description: str = "Base lint rule"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        """Run the lint check. Override in subclasses."""
        return []


class MissingStatuteTitleRule(LintRule):
    """Check for statutes without titles."""
    
    id = "missing-title"
    severity = Severity.WARNING
    description = "Statute should have a descriptive title"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        for statute in ast.statutes:
            if not statute.title or not statute.title.value.strip():
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Statute {statute.section_number} is missing a title",
                    line=loc.line if loc else None,
                    suggestion="Add a descriptive title for the statute"
                ))
        return issues


class MissingElementsRule(LintRule):
    """Check for statutes without elements."""
    
    id = "missing-elements"
    severity = Severity.WARNING
    description = "Statute should define offense elements"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        for statute in ast.statutes:
            if not statute.elements:
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Statute {statute.section_number} has no elements defined",
                    line=loc.line if loc else None,
                    suggestion="Define actus_reus and mens_rea elements"
                ))
        return issues


class MissingActusReusRule(LintRule):
    """Check for statutes without actus reus element."""
    
    id = "missing-actus-reus"
    severity = Severity.INFO
    description = "Statute should have an actus reus element"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        for statute in ast.statutes:
            has_actus = any(e.element_type == "actus_reus" for e in statute.elements)
            if statute.elements and not has_actus:
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Statute {statute.section_number} has no actus_reus element",
                    line=loc.line if loc else None,
                ))
        return issues


class MissingMensReaRule(LintRule):
    """Check for statutes without mens rea element."""
    
    id = "missing-mens-rea"
    severity = Severity.INFO
    description = "Statute should have a mens rea element"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        for statute in ast.statutes:
            has_mens = any(e.element_type == "mens_rea" for e in statute.elements)
            if statute.elements and not has_mens:
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Statute {statute.section_number} has no mens_rea element",
                    line=loc.line if loc else None,
                ))
        return issues


class MissingPenaltyRule(LintRule):
    """Check for statutes without penalty clause."""
    
    id = "missing-penalty"
    severity = Severity.INFO
    description = "Statute should specify a penalty"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        for statute in ast.statutes:
            if not statute.penalty:
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Statute {statute.section_number} has no penalty defined",
                    line=loc.line if loc else None,
                ))
        return issues


class EmptyIllustrationRule(LintRule):
    """Check for empty illustrations."""
    
    id = "empty-illustration"
    severity = Severity.WARNING
    description = "Illustrations should have meaningful content"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        for statute in ast.statutes:
            for illus in statute.illustrations:
                if not illus.description.value.strip():
                    loc = illus.source_location
                    issues.append(LintIssue(
                        rule=self.id,
                        severity=self.severity,
                        message=f"Empty illustration in statute {statute.section_number}",
                        line=loc.line if loc else None,
                    ))
        return issues


class UnusedDefinitionRule(LintRule):
    """Check for definitions that are never referenced."""
    
    id = "unused-definition"
    severity = Severity.HINT
    description = "Definition is never referenced"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        
        for statute in ast.statutes:
            defined_terms = {d.term.lower() for d in statute.definitions}
            
            # Collect all text content to search for term usage
            text_content = ""
            for elem in statute.elements:
                if isinstance(elem.description, StringLit):
                    text_content += " " + elem.description.value
            for illus in statute.illustrations:
                text_content += " " + illus.description.value
            
            text_lower = text_content.lower()
            
            for defn in statute.definitions:
                term = defn.term
                # Check if term is used in element descriptions or illustrations
                if term.lower() not in text_lower:
                    loc = defn.source_location
                    issues.append(LintIssue(
                        rule=self.id,
                        severity=self.severity,
                        message=f"Definition '{term}' is never referenced in statute {statute.section_number}",
                        line=loc.line if loc else None,
                    ))
        
        return issues


class NamingConventionRule(LintRule):
    """Check naming conventions."""
    
    id = "naming-convention"
    severity = Severity.INFO
    description = "Follow naming conventions"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        
        # Check struct names (should be PascalCase)
        for struct in ast.type_defs:
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', struct.name):
                loc = struct.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Type '{struct.name}' should use PascalCase",
                    line=loc.line if loc else None,
                    suggestion=f"Rename to '{struct.name.title().replace('_', '')}'"
                ))
        
        # Check function names (should be snake_case)
        for func in ast.function_defs:
            if not re.match(r'^[a-z][a-z0-9_]*$', func.name):
                loc = func.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Function '{func.name}' should use snake_case",
                    line=loc.line if loc else None,
                ))
        
        return issues


class SectionNumberFormatRule(LintRule):
    """Check section number format."""
    
    id = "section-format"
    severity = Severity.WARNING
    description = "Section numbers should follow standard format"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        
        for statute in ast.statutes:
            # Allow digits with optional letter suffix (e.g., "299", "300A")
            if not re.match(r'^\d+[A-Za-z]?$', statute.section_number):
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Non-standard section number format: '{statute.section_number}'",
                    line=loc.line if loc else None,
                    suggestion="Use numeric format with optional letter suffix (e.g., '299', '300A')"
                ))
        
        return issues


class DuplicateSectionRule(LintRule):
    """Check for duplicate section numbers."""
    
    id = "duplicate-section"
    severity = Severity.ERROR
    description = "Section numbers must be unique"
    
    def check(self, ast: ModuleNode, source: str) -> List[LintIssue]:
        issues = []
        seen: Dict[str, int] = {}
        
        for statute in ast.statutes:
            section = statute.section_number
            if section in seen:
                loc = statute.source_location
                issues.append(LintIssue(
                    rule=self.id,
                    severity=self.severity,
                    message=f"Duplicate section number: '{section}'",
                    line=loc.line if loc else None,
                ))
            seen[section] = seen.get(section, 0) + 1
        
        return issues


# All available lint rules
ALL_RULES: List[LintRule] = [
    MissingStatuteTitleRule(),
    MissingElementsRule(),
    MissingActusReusRule(),
    MissingMensReaRule(),
    MissingPenaltyRule(),
    EmptyIllustrationRule(),
    UnusedDefinitionRule(),
    NamingConventionRule(),
    SectionNumberFormatRule(),
    DuplicateSectionRule(),
]


def format_issues(
    issues: List[LintIssue],
    filename: str,
    color: bool = True
) -> str:
    """Format lint issues for display."""
    if not issues:
        return ""
    
    lines = []
    
    # Group by severity
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]
    hints = [i for i in issues if i.severity == Severity.HINT]
    
    def c(text: str, col: str) -> str:
        return colorize(text, col) if color else text
    
    def format_issue(issue: LintIssue, prefix: str, col: str) -> str:
        loc = f":{issue.line}" if issue.line else ""
        msg = f"{filename}{loc}: {c(prefix, col)} [{issue.rule}] {issue.message}"
        if issue.suggestion:
            msg += f"\n  → {issue.suggestion}"
        return msg
    
    for issue in errors:
        lines.append(format_issue(issue, "error", Colors.RED))
    
    for issue in warnings:
        lines.append(format_issue(issue, "warning", Colors.YELLOW))
    
    for issue in infos:
        lines.append(format_issue(issue, "info", Colors.CYAN))
    
    for issue in hints:
        lines.append(format_issue(issue, "hint", Colors.DIM))
    
    return "\n".join(lines)


def run_lint(
    files: List[str],
    rules: Optional[List[str]] = None,
    exclude_rules: Optional[List[str]] = None,
    json_output: bool = False,
    verbose: bool = False,
    color: bool = True,
    fix: bool = False,
) -> None:
    """
    Run lint checks on Yuho files.
    
    Args:
        files: List of file paths to lint
        rules: Specific rules to run (None = all)
        exclude_rules: Rules to exclude
        json_output: Output as JSON
        verbose: Enable verbose output
        color: Use colored output
        fix: Attempt to auto-fix issues (not yet implemented)
    """
    import json as json_module
    
    # Select rules to run
    active_rules = ALL_RULES
    
    if rules:
        active_rules = [r for r in ALL_RULES if r.id in rules]
    
    if exclude_rules:
        active_rules = [r for r in active_rules if r.id not in exclude_rules]
    
    if verbose:
        click.echo(f"Running {len(active_rules)} lint rules")
    
    all_issues: Dict[str, List[LintIssue]] = {}
    parser = Parser()
    
    for file_path in files:
        path = Path(file_path)
        
        if not path.exists():
            click.echo(colorize(f"error: File not found: {file_path}", Colors.RED), err=True)
            continue
        
        # Parse file
        try:
            source = path.read_text(encoding="utf-8")
            result = parser.parse_file(path)
            
            if result.errors:
                # Skip files with parse errors
                if verbose:
                    click.echo(f"Skipping {path} (parse errors)")
                continue
            
            builder = ASTBuilder(source, str(path))
            ast = builder.build(result.tree.root_node)
            
            # Run all rules
            file_issues: List[LintIssue] = []
            for rule in active_rules:
                file_issues.extend(rule.check(ast, source))
            
            if file_issues:
                all_issues[str(path)] = file_issues
                
        except Exception as e:
            if verbose:
                click.echo(f"Error processing {path}: {e}", err=True)
    
    # Output results
    if json_output:
        output = {
            "files": len(files),
            "issues": {
                path: [
                    {
                        "rule": i.rule,
                        "severity": i.severity.name.lower(),
                        "message": i.message,
                        "line": i.line,
                        "suggestion": i.suggestion,
                    }
                    for i in issues
                ]
                for path, issues in all_issues.items()
            },
            "summary": {
                "errors": sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.ERROR),
                "warnings": sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.WARNING),
                "infos": sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.INFO),
                "hints": sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.HINT),
            }
        }
        print(json_module.dumps(output, indent=2))
    else:
        if not all_issues:
            click.echo(colorize("✓ No issues found", Colors.GREEN))
            return
        
        for filename, issues in all_issues.items():
            output = format_issues(issues, filename, color=color)
            click.echo(output)
            click.echo()
        
        # Summary
        total_errors = sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.ERROR)
        total_warnings = sum(1 for issues in all_issues.values() for i in issues if i.severity == Severity.WARNING)
        total_other = sum(1 for issues in all_issues.values() for i in issues if i.severity not in (Severity.ERROR, Severity.WARNING))
        
        summary_parts = []
        if total_errors:
            summary_parts.append(colorize(f"{total_errors} error(s)", Colors.RED) if color else f"{total_errors} error(s)")
        if total_warnings:
            summary_parts.append(colorize(f"{total_warnings} warning(s)", Colors.YELLOW) if color else f"{total_warnings} warning(s)")
        if total_other:
            summary_parts.append(f"{total_other} info/hint(s)")
        
        click.echo(f"Found {', '.join(summary_parts)}")
    
    # Exit with error if there are errors
    if any(i.severity == Severity.ERROR for issues in all_issues.values() for i in issues):
        sys.exit(1)
