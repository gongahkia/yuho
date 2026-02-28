"""
Shared analysis service for parser, AST, and semantic summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

from yuho.ast import ASTBuilder
from yuho.ast.nodes import ASTNode, ModuleNode
from yuho.parser import get_parser
from yuho.parser.source_location import SourceLocation
from yuho.parser.wrapper import ParseError


@dataclass(frozen=True)
class AnalysisError:
    """Structured analysis error across parse, AST, and semantic phases."""

    stage: str
    message: str
    error_code: str
    location: Optional[SourceLocation] = None
    node_type: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert error to a serializable dictionary."""
        payload: dict[str, Any] = {
            "stage": self.stage,
            "message": self.message,
            "error_code": self.error_code,
        }
        if self.location:
            payload["location"] = {
                "file": self.location.file,
                "line": self.location.line,
                "col": self.location.col,
                "end_line": self.location.end_line,
                "end_col": self.location.end_col,
            }
        if self.node_type:
            payload["node_type"] = self.node_type
        return payload


@dataclass(frozen=True)
class ASTSummary:
    """High-level structural summary of a parsed Yuho module."""

    imports: int
    structs: int
    functions: int
    statutes: int
    variables: int
    references: int
    assertions: int
    definitions: int
    elements: int
    penalties: int
    illustrations: int
    total_nodes: int

    @classmethod
    def from_module(cls, ast: ModuleNode) -> "ASTSummary":
        """Create an AST summary from a module node."""
        definitions = sum(len(s.definitions) for s in ast.statutes)
        elements = sum(len(s.elements) for s in ast.statutes)
        penalties = sum(1 for s in ast.statutes if s.penalty is not None)
        illustrations = sum(len(s.illustrations) for s in ast.statutes)

        return cls(
            imports=len(ast.imports),
            structs=len(ast.type_defs),
            functions=len(ast.function_defs),
            statutes=len(ast.statutes),
            variables=len(ast.variables),
            references=len(ast.references),
            assertions=len(ast.assertions),
            definitions=definitions,
            elements=elements,
            penalties=penalties,
            illustrations=illustrations,
            total_nodes=_count_nodes(ast),
        )

    def to_dict(self) -> dict[str, int]:
        """Convert summary to dictionary."""
        return {
            "imports": self.imports,
            "structs": self.structs,
            "functions": self.functions,
            "statutes": self.statutes,
            "variables": self.variables,
            "references": self.references,
            "assertions": self.assertions,
            "definitions": self.definitions,
            "elements": self.elements,
            "penalties": self.penalties,
            "illustrations": self.illustrations,
            "total_nodes": self.total_nodes,
        }


@dataclass(frozen=True)
class SemanticIssue:
    """Single semantic issue emitted by type analysis."""

    severity: str
    message: str
    line: int
    column: int

    def to_dict(self) -> dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "severity": self.severity,
            "message": self.message,
            "line": self.line,
            "column": self.column,
        }


@dataclass(frozen=True)
class SemanticSummary:
    """Summary of semantic analysis output."""

    issues: tuple[SemanticIssue, ...] = ()
    errors: int = 0
    warnings: int = 0

    @property
    def has_errors(self) -> bool:
        """Return True if semantic analysis produced errors."""
        return self.errors > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert semantic summary to dictionary."""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class AnalysisResult:
    """End-to-end parse/AST/semantic analysis output."""

    file: str
    source: str
    tree: Optional[Any] = None
    ast: Optional[ModuleNode] = None
    parse_errors: list[ParseError] = field(default_factory=list)
    errors: list[AnalysisError] = field(default_factory=list)
    ast_summary: Optional[ASTSummary] = None
    semantic_summary: Optional[SemanticSummary] = None
    parse_duration_ms: float = 0.0
    ast_duration_ms: float = 0.0
    semantic_duration_ms: float = 0.0
    total_duration_ms: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Return True if parse, AST, and semantic checks pass."""
        if self.parse_errors or self.errors:
            return False
        if self.semantic_summary is None:
            return self.ast is not None
        return not self.semantic_summary.has_errors


def analyze_file(
    path: str | Path,
    *,
    run_semantic: bool = True,
    encoding: str = "utf-8",
) -> AnalysisResult:
    """
    Analyze source from a file path.

    Returns a structured result instead of raising for common failures.
    """
    file_path = Path(path)
    if not file_path.exists():
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"File not found: {file_path}",
                    error_code="file_not_found",
                )
            ],
        )

    try:
        source = file_path.read_text(encoding=encoding)
    except Exception as exc:
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"Failed to read file: {exc}",
                    error_code="file_read_failed",
                )
            ],
        )

    return analyze_source(source, file=str(file_path), run_semantic=run_semantic)


def analyze_source(
    source: str,
    *,
    file: str = "<string>",
    run_semantic: bool = True,
) -> AnalysisResult:
    """
    Analyze source text through parse, AST build, and semantic checks.
    """
    start_total = perf_counter()
    result = AnalysisResult(file=file, source=source)

    parser = get_parser()

    start_parse = perf_counter()
    parse_result = parser.parse(source, file=file)
    result.parse_duration_ms = (perf_counter() - start_parse) * 1000.0

    result.tree = parse_result.tree
    result.parse_errors = list(parse_result.errors)

    if result.parse_errors:
        result.errors.extend(_parse_errors_to_analysis_errors(result.parse_errors))
        result.total_duration_ms = (perf_counter() - start_total) * 1000.0
        return result

    start_ast = perf_counter()
    try:
        builder = ASTBuilder(source, file)
        result.ast = builder.build(parse_result.root_node)
    except Exception as exc:
        result.ast_duration_ms = (perf_counter() - start_ast) * 1000.0
        result.errors.append(
            AnalysisError(
                stage="ast",
                message=f"Failed to build AST: {exc}",
                error_code="ast_build_failed",
            )
        )
        result.total_duration_ms = (perf_counter() - start_total) * 1000.0
        return result
    result.ast_duration_ms = (perf_counter() - start_ast) * 1000.0

    result.ast_summary = ASTSummary.from_module(result.ast)

    if run_semantic:
        start_semantic = perf_counter()
        try:
            result.semantic_summary = _run_semantic_checks(result.ast)
        except Exception as exc:
            result.errors.append(
                AnalysisError(
                    stage="semantic",
                    message=f"Semantic analysis failed: {exc}",
                    error_code="semantic_analysis_failed",
                )
            )
        result.semantic_duration_ms = (perf_counter() - start_semantic) * 1000.0

    result.total_duration_ms = (perf_counter() - start_total) * 1000.0
    return result


def _count_nodes(root: ASTNode) -> int:
    """Count all reachable nodes in an AST."""
    count = 0
    stack = [root]
    while stack:
        node = stack.pop()
        count += 1
        stack.extend(node.children())
    return count


def _parse_errors_to_analysis_errors(parse_errors: list[ParseError]) -> list[AnalysisError]:
    """Convert parser errors to normalized analysis errors."""
    return [
        AnalysisError(
            stage="parse",
            message=error.message,
            error_code="parse_error",
            location=error.location,
            node_type=error.node_type,
        )
        for error in parse_errors
    ]


def _run_semantic_checks(ast: ModuleNode) -> SemanticSummary:
    """Run type inference and type checking and return a semantic summary."""
    from yuho.ast.type_check import TypeCheckVisitor
    from yuho.ast.type_inference import TypeInferenceVisitor

    infer_visitor = TypeInferenceVisitor()
    ast.accept(infer_visitor)

    check_visitor = TypeCheckVisitor(infer_visitor.result)
    ast.accept(check_visitor)

    issues: list[SemanticIssue] = []
    error_count = 0
    warning_count = 0

    for item in check_visitor.result.errors + check_visitor.result.warnings:
        severity = getattr(item, "severity", "error")
        if severity == "warning":
            warning_count += 1
        else:
            error_count += 1
        issues.append(
            SemanticIssue(
                severity=severity,
                message=item.message,
                line=item.line,
                column=item.column,
            )
        )

    return SemanticSummary(
        issues=tuple(issues),
        errors=error_count,
        warnings=warning_count,
    )
