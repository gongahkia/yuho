"""
Shared analysis service for parser, AST, and semantic summaries.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import re
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

from yuho.ast import ASTBuilder
from yuho.ast.nodes import ASTNode, ModuleNode
from yuho.parser import get_parser
from yuho.parser.source_location import SourceLocation
from yuho.parser.wrapper import ParseError, MAX_FILE_SIZE, MAX_SOURCE_LENGTH
from yuho.ast.statute_lint import LintWarning, lint_module
from yuho.services.errors import (
    ASTBoundaryError,
    ParserBoundaryError,
    run_ast_boundary,
    run_parser_boundary,
)


ANALYSIS_ERROR_CODES: dict[str, str] = {
    "file_not_found": "Y0001",
    "not_a_file": "Y0002",
    "file_too_large": "Y0003",
    "encoding_error": "Y0004",
    "file_read_failed": "Y0005",
    "null_bytes": "Y0006",
    "source_too_large": "Y0007",
    "parse_error": "Y0100",
    "parse_missing_node": "Y0101",
    "parse_unexpected_syntax": "Y0102",
    "parser_failed": "Y0199",
    "ast_build_failed": "Y0200",
    "lint_analysis_failed": "Y0300",
    "semantic_issue": "Y0400",
    "semantic_analysis_failed": "Y0499",
}
CACHE_VERSION = "yuho-analysis-cache-v1"
CACHE_ENV = "YUHO_ANALYSIS_CACHE"
CACHE_DIR_ENV = "YUHO_CACHE_DIR"


def _code(name: str) -> str:
    return ANALYSIS_ERROR_CODES[name]


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
class CodeScale:
    """Code complexity scale derived from parsed source and AST."""

    source_loc: int
    ast_nodes: int
    statute_count: int
    definition_count: int

    def to_dict(self) -> dict[str, int]:
        """Convert code scale to dictionary."""
        return {
            "source_loc": self.source_loc,
            "ast_nodes": self.ast_nodes,
            "statute_count": self.statute_count,
            "definition_count": self.definition_count,
        }


@dataclass
class ClockLoadScale:
    """Timing scale for analysis pipeline stages."""

    parse_ms: float
    ast_build_ms: float
    total_ms: float

    def to_dict(self) -> dict[str, float]:
        """Convert timing scale to dictionary."""
        return {
            "parse_ms": self.parse_ms,
            "ast_build_ms": self.ast_build_ms,
            "total_ms": self.total_ms,
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
    code_scale: Optional[CodeScale] = None
    clock_load_scale: Optional[ClockLoadScale] = None
    lint_warnings: list[LintWarning] = field(default_factory=list)
    semantic_checked: bool = False
    lint_checked: bool = False
    parse_duration_ms: float = 0.0
    ast_duration_ms: float = 0.0
    semantic_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    cache_hit: bool = False

    @property
    def is_valid(self) -> bool:
        """Return True if parse, AST, and semantic checks pass."""
        if self.parse_errors or self.errors:
            return False
        if self.semantic_summary is None:
            return self.ast is not None
        return not self.semantic_summary.has_errors

    @property
    def parse_valid(self) -> bool:
        """Return True when the parse phase completed without diagnostics."""
        return not self.parse_errors and not self._stage_errors("parse")

    @property
    def ast_valid(self) -> bool:
        """Return True when AST building succeeded."""
        return self.parse_valid and self.ast is not None and not self._stage_errors("ast")

    @property
    def semantic_valid(self) -> Optional[bool]:
        """Return semantic validity, or None when semantic checks were skipped."""
        if not self.semantic_checked:
            return None
        if self._stage_errors("semantic"):
            return False
        if self.semantic_summary is None:
            return False
        return not self.semantic_summary.has_errors

    @property
    def lint_valid(self) -> Optional[bool]:
        """Return lint validity, or None when lint did not run."""
        if not self.lint_checked:
            return None
        if self._stage_errors("lint"):
            return False
        return len(self.lint_warnings) == 0

    def _stage_errors(self, stage: str) -> list[AnalysisError]:
        """Return normalized errors for a specific analysis stage."""
        return [error for error in self.errors if error.stage == stage]

    def _parse_diagnostics(self) -> list[dict[str, Any]]:
        """Return parse diagnostics without duplicating normalized parse errors."""
        if self.parse_errors:
            return [
                {
                    "stage": "parse",
                    "severity": "error",
                    "message": err.message,
                    "error_code": _parse_error_code(err),
                    "node_type": err.node_type,
                    "line": err.location.line,
                    "column": err.location.col,
                    "end_line": err.location.end_line,
                    "end_column": err.location.end_col,
                }
                for err in self.parse_errors
            ]
        return [
            {
                "stage": error.stage,
                "severity": "error",
                "message": error.message,
                "error_code": error.error_code,
                "node_type": error.node_type,
                "line": error.location.line if error.location else None,
                "column": error.location.col if error.location else None,
                "end_line": error.location.end_line if error.location else None,
                "end_column": error.location.end_col if error.location else None,
            }
            for error in self._stage_errors("parse")
        ]

    def diagnostics(self) -> list[dict[str, Any]]:
        """Return unified diagnostics across parse, AST, and semantic phases."""
        diagnostics = self._parse_diagnostics()
        for stage in ("ast", "lint"):
            diagnostics.extend(
                {
                    "stage": error.stage,
                    "severity": "error",
                    "message": error.message,
                    "error_code": error.error_code,
                    "node_type": error.node_type,
                    "line": error.location.line if error.location else None,
                    "column": error.location.col if error.location else None,
                    "end_line": error.location.end_line if error.location else None,
                    "end_column": error.location.end_col if error.location else None,
                }
                for error in self._stage_errors(stage)
            )

        if self.semantic_summary is not None:
            diagnostics.extend(
                {
                    "stage": "semantic",
                    "severity": issue.severity,
                    "message": issue.message,
                    "error_code": _code("semantic_issue"),
                    "node_type": None,
                    "line": issue.line,
                    "column": issue.column,
                    "end_line": None,
                    "end_column": None,
                }
                for issue in self.semantic_summary.issues
            )

        diagnostics.extend(
            {
                "stage": error.stage,
                "severity": "error",
                "message": error.message,
                "error_code": error.error_code,
                "node_type": error.node_type,
                "line": error.location.line if error.location else None,
                "column": error.location.col if error.location else None,
                "end_line": error.location.end_line if error.location else None,
                "end_column": error.location.end_col if error.location else None,
            }
            for error in self._stage_errors("semantic")
        )
        return diagnostics

    def lint_warning_payload(self) -> list[dict[str, Any]]:
        """Return lint warnings as serializable dictionaries."""
        return [
            {
                "stage": "lint",
                "severity": warning.severity,
                "message": warning.message,
                "statute_section": warning.statute_section,
            }
            for warning in self.lint_warnings
        ]

    def phase_status(self) -> dict[str, dict[str, Any]]:
        """Return status for parse, AST, semantic, and lint phases."""
        semantic_error_count = len(self._stage_errors("semantic"))
        semantic_warning_count = 0
        if self.semantic_summary is not None:
            semantic_error_count += self.semantic_summary.errors
            semantic_warning_count = self.semantic_summary.warnings

        return {
            "parse": {
                "ran": True,
                "valid": self.parse_valid,
                "error_count": len(self._parse_diagnostics()),
                "warning_count": 0,
            },
            "ast": {
                "ran": self.parse_valid,
                "valid": self.ast_valid if self.parse_valid else None,
                "error_count": len(self._stage_errors("ast")),
                "warning_count": 0,
            },
            "semantic": {
                "ran": self.semantic_checked,
                "valid": self.semantic_valid,
                "error_count": semantic_error_count if self.semantic_checked else 0,
                "warning_count": semantic_warning_count if self.semantic_checked else 0,
            },
            "lint": {
                "ran": self.lint_checked,
                "valid": self.lint_valid,
                "error_count": len(self._stage_errors("lint")) if self.lint_checked else 0,
                "warning_count": len(self.lint_warnings) if self.lint_checked else 0,
            },
        }

    def validation_payload(
        self,
        *,
        include_metrics: bool = False,
        include_stats: bool = True,
    ) -> dict[str, Any]:
        """Return a reusable machine-readable validation contract."""
        diagnostics = self.diagnostics()
        payload: dict[str, Any] = {
            "valid": self.is_valid,
            "file": self.file,
            "cache_hit": self.cache_hit,
            "parse_valid": self.parse_valid,
            "ast_valid": self.ast_valid,
            "semantic_checked": self.semantic_checked,
            "semantic_valid": self.semantic_valid,
            "lint_checked": self.lint_checked,
            "lint_valid": self.lint_valid,
            "phases": self.phase_status(),
            "errors": [item for item in diagnostics if item["severity"] == "error"],
            "warnings": [item for item in diagnostics if item["severity"] != "error"],
            "lint_warnings": self.lint_warning_payload(),
        }
        if include_stats and self.ast_summary is not None:
            payload["stats"] = self.ast_summary.to_dict()
        if include_metrics:
            payload["code_scale"] = self.code_scale.to_dict() if self.code_scale else None
            payload["clock_load_scale"] = (
                self.clock_load_scale.to_dict() if self.clock_load_scale else None
            )
        return payload


def _source_hash(source: str) -> str:
    digest = hashlib.sha256()
    digest.update(CACHE_VERSION.encode("utf-8"))
    digest.update(b"\0")
    digest.update(source.encode("utf-8"))
    return digest.hexdigest()


def _analysis_stage(*, run_semantic: bool, features: Optional[set[str]]) -> str:
    enabled = ",".join(sorted(features or ())) or "none"
    semantic = "semantic" if run_semantic else "syntax"
    return f"analysis:{semantic}:features={enabled}"


def _cache_root() -> Optional[Path]:
    if os.environ.get(CACHE_ENV, "1") in {"0", "false", "False", "no"}:
        return None
    if CACHE_DIR_ENV in os.environ:
        return Path(os.environ[CACHE_DIR_ENV]).expanduser() / "analysis"
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg).expanduser() / "yuho" / "analysis"
    return Path.home() / ".cache" / "yuho" / "analysis"


def _cache_path(file_hash: str, stage: str) -> Optional[Path]:
    root = _cache_root()
    if root is None:
        return None
    safe_stage = re.sub(r"[^A-Za-z0-9_.=-]+", "_", stage)
    return root / file_hash / f"{safe_stage}.pickle"


def _load_cached_analysis(
    file: str,
    source: str,
    file_hash: str,
    stage: str,
) -> Optional[AnalysisResult]:
    path = _cache_path(file_hash, stage)
    if path is None or not path.exists():
        return None
    try:
        with path.open("rb") as fh:
            payload = pickle.load(fh)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("version") != CACHE_VERSION:
        return None
    if payload.get("file_hash") != file_hash or payload.get("stage") != stage:
        return None
    if payload.get("file") != file:
        return None
    result = payload.get("result")
    if not isinstance(result, AnalysisResult):
        return None
    result.file = file
    result.source = source
    result.tree = None
    result.cache_hit = True
    return result


def _store_cached_analysis(result: AnalysisResult, file_hash: str, stage: str) -> None:
    path = _cache_path(file_hash, stage)
    if path is None:
        return
    cached = copy(result)
    cached.tree = None
    cached.cache_hit = False
    payload = {
        "version": CACHE_VERSION,
        "file": result.file,
        "file_hash": file_hash,
        "stage": stage,
        "result": cached,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_path.replace(path)
    except Exception:
        return


def analyze_file(
    path: str | Path,
    *,
    run_semantic: bool = True,
    encoding: str = "utf-8",
    features: Optional[set[str]] = None,
) -> AnalysisResult:
    """
    Analyze source from a file path.

    Returns a structured result instead of raising for common failures.
    """
    file_path = Path(path).resolve()
    if not file_path.exists():
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"File not found: {file_path}",
                    error_code=_code("file_not_found"),
                )
            ],
        )
    if not file_path.is_file():
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"Not a regular file: {file_path}",
                    error_code=_code("not_a_file"),
                )
            ],
        )
    try:
        fsize = file_path.stat().st_size
    except OSError:
        fsize = 0
    if fsize > MAX_FILE_SIZE:
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"File exceeds maximum size ({MAX_FILE_SIZE} bytes): {file_path}",
                    error_code=_code("file_too_large"),
                )
            ],
        )

    try:
        source = file_path.read_text(encoding=encoding)
    except UnicodeDecodeError as exc:
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"File is not valid {encoding}: {file_path} ({exc.reason})",
                    error_code=_code("encoding_error"),
                )
            ],
        )
    except OSError as exc:
        return AnalysisResult(
            file=str(file_path),
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"Failed to read file: {exc}",
                    error_code=_code("file_read_failed"),
                )
            ],
        )

    file_label = str(file_path)
    normalized_source = source[1:] if source.startswith("\ufeff") else source
    file_hash = _source_hash(normalized_source)
    stage = _analysis_stage(run_semantic=run_semantic, features=features)
    cached = _load_cached_analysis(file_label, normalized_source, file_hash, stage)
    if cached is not None:
        return cached

    result = analyze_source(
        source,
        file=file_label,
        run_semantic=run_semantic,
        features=features,
    )
    _store_cached_analysis(result, file_hash, stage)
    return result


def analyze_source(
    source: str,
    *,
    file: str = "<string>",
    run_semantic: bool = True,
    features: Optional[set[str]] = None,
) -> AnalysisResult:
    """
    Analyze source text through parse, AST build, and semantic checks.
    """
    start_total = perf_counter()
    if "\x00" in source:
        return AnalysisResult(
            file=file,
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message="Source contains null bytes (possible binary file)",
                    error_code=_code("null_bytes"),
                )
            ],
        )
    if len(source) > MAX_SOURCE_LENGTH:
        return AnalysisResult(
            file=file,
            source="",
            errors=[
                AnalysisError(
                    stage="parse",
                    message=f"Source exceeds maximum length ({MAX_SOURCE_LENGTH} chars)",
                    error_code=_code("source_too_large"),
                )
            ],
        )
    if source.startswith("\ufeff"):
        source = source[1:]
    result = AnalysisResult(file=file, source=source)

    parser = get_parser()

    start_parse = perf_counter()
    try:
        parse_result = run_parser_boundary(
            parser.parse,
            source,
            file=file,
            features=features,
            message="Failed to parse source",
        )
    except ParserBoundaryError as exc:
        result.parse_duration_ms = (perf_counter() - start_parse) * 1000.0
        result.errors.append(
            AnalysisError(
                stage="parse",
                message=str(exc),
                error_code=_code("parser_failed"),
            )
        )
        result.total_duration_ms = (perf_counter() - start_total) * 1000.0
        result.clock_load_scale = _build_clock_load_scale(result)
        return result
    result.parse_duration_ms = (perf_counter() - start_parse) * 1000.0

    result.tree = parse_result.tree
    result.parse_errors = list(parse_result.errors)

    if result.parse_errors:
        result.errors.extend(_parse_errors_to_analysis_errors(result.parse_errors))
        result.total_duration_ms = (perf_counter() - start_total) * 1000.0
        result.clock_load_scale = _build_clock_load_scale(result)
        return result

    start_ast = perf_counter()
    try:
        builder = ASTBuilder(source, file)
        result.ast = run_ast_boundary(
            builder.build,
            parse_result.root_node,
            message="Failed to build AST",
        )
    except ASTBoundaryError as exc:
        result.ast_duration_ms = (perf_counter() - start_ast) * 1000.0
        result.errors.append(
            AnalysisError(
                stage="ast",
                message=str(exc),
                error_code=_code("ast_build_failed"),
            )
        )
        result.total_duration_ms = (perf_counter() - start_total) * 1000.0
        result.clock_load_scale = _build_clock_load_scale(result)
        return result
    result.ast_duration_ms = (perf_counter() - start_ast) * 1000.0

    result.ast_summary = ASTSummary.from_module(result.ast)
    result.code_scale = CodeScale(
        source_loc=_count_source_loc(source),
        ast_nodes=result.ast_summary.total_nodes,
        statute_count=result.ast_summary.statutes,
        definition_count=result.ast_summary.definitions,
    )

    try:
        result.lint_checked = True
        result.lint_warnings = lint_module(result.ast)
    except Exception as exc:
        result.errors.append(
            AnalysisError(
                stage="lint",
                message=f"Lint analysis failed: {exc}",
                error_code=_code("lint_analysis_failed"),
            )
        )

    if run_semantic:
        result.semantic_checked = True
        start_semantic = perf_counter()
        try:
            result.semantic_summary = _run_semantic_checks(result.ast, file=file)
        except (TypeError, ValueError, AttributeError, RuntimeError) as exc:
            result.errors.append(
                AnalysisError(
                    stage="semantic",
                    message=f"Semantic analysis failed: {exc}",
                    error_code=_code("semantic_analysis_failed"),
                )
            )
        result.semantic_duration_ms = (perf_counter() - start_semantic) * 1000.0

    result.total_duration_ms = (perf_counter() - start_total) * 1000.0
    result.clock_load_scale = _build_clock_load_scale(result)
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


def _count_source_loc(source: str) -> int:
    """Count source lines for code-scale reporting."""
    return len(source.splitlines())


def _build_clock_load_scale(result: AnalysisResult) -> ClockLoadScale:
    """Create a timing scale payload from analysis durations."""
    return ClockLoadScale(
        parse_ms=result.parse_duration_ms,
        ast_build_ms=result.ast_duration_ms,
        total_ms=result.total_duration_ms,
    )


def _parse_error_code(error: ParseError) -> str:
    if error.node_type and error.node_type.startswith("MISSING:"):
        return _code("parse_missing_node")
    if "Unexpected syntax" in error.message:
        return _code("parse_unexpected_syntax")
    return _code("parse_error")


def _parse_errors_to_analysis_errors(parse_errors: list[ParseError]) -> list[AnalysisError]:
    """Convert parser errors to normalized analysis errors."""
    normalized: list[AnalysisError] = []
    for error in parse_errors:
        normalized.append(
            AnalysisError(
                stage="parse",
                message=error.message,
                error_code=_parse_error_code(error),
                location=error.location,
                node_type=error.node_type,
            )
        )
    return normalized


def _run_semantic_checks(
    ast: ModuleNode,
    file: str = "<string>",
) -> SemanticSummary:
    """Run scope analysis, type inference, and type checking."""
    from yuho.ast.scope_analysis import ScopeAnalysisVisitor
    from yuho.ast.type_check import TypeCheckVisitor
    from yuho.ast.type_inference import TypeInferenceVisitor
    from yuho.resolver import ModuleResolver

    source_path = Path(file) if file != "<string>" else None
    resolver = None
    if source_path and source_path.exists():
        search_paths = [source_path.parent, Path.cwd()]
        lib_path = Path.cwd() / "library"
        if lib_path.is_dir():
            search_paths.append(lib_path)
        resolver = ModuleResolver(search_paths=search_paths)

    scope_visitor = ScopeAnalysisVisitor(
        resolver=resolver,
        source_file=source_path,
    )
    ast.accept(scope_visitor)

    infer_visitor = TypeInferenceVisitor()
    ast.accept(infer_visitor)

    check_visitor = TypeCheckVisitor(
        infer_visitor.result,
        resolver=resolver,
        source_file=source_path,
    )
    ast.accept(check_visitor)

    issues: list[SemanticIssue] = []
    error_count = 0
    warning_count = 0

    for item in _check_jurisdiction_references(ast, resolver, source_path):
        if item.severity == "warning":
            warning_count += 1
        else:
            error_count += 1
        issues.append(item)

    for scope_err in scope_visitor.result.errors:
        severity = getattr(scope_err, "severity", "error")
        line = getattr(scope_err, "line", 0)
        column = getattr(scope_err, "column", 0)
        msg = scope_err.message if hasattr(scope_err, "message") else str(scope_err)
        if severity == "warning":
            warning_count += 1
        else:
            error_count += 1
        issues.append(SemanticIssue(severity=severity, message=msg, line=line, column=column))

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


def _check_jurisdiction_references(
    ast: ModuleNode,
    resolver,
    source_path: Optional[Path],
) -> list[SemanticIssue]:
    if resolver is None or source_path is None:
        return []
    source_jurisdictions = _module_jurisdictions(ast)
    if not source_jurisdictions:
        return []

    issues: list[SemanticIssue] = []
    for ref in ast.references:
        try:
            target = resolver.resolve_reference(ref, source_path)
        except Exception:
            continue
        target_jurisdictions = _module_jurisdictions(target)
        if not target_jurisdictions:
            continue
        if source_jurisdictions & target_jurisdictions:
            continue
        if ref.cross_jurisdiction:
            continue
        line, column = _node_line_col(ref)
        issues.append(
            SemanticIssue(
                severity="error",
                message=(
                    f"cross-jurisdiction reference '{ref.path}' from "
                    f"{', '.join(sorted(source_jurisdictions))} to "
                    f"{', '.join(sorted(target_jurisdictions))} requires "
                    "/// @cross_jurisdiction"
                ),
                line=line,
                column=column,
            )
        )
    return issues


def _module_jurisdictions(ast: ModuleNode) -> set[str]:
    return {
        statute.jurisdiction
        for statute in ast.statutes
        if statute.jurisdiction
    }


def _node_line_col(node: ASTNode) -> tuple[int, int]:
    if node.source_location:
        return node.source_location.line, node.source_location.col
    return 0, 0
