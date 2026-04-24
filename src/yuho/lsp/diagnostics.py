"""
Diagnostics publishing for Yuho LSP.

Handles parsing errors and type checker errors conversion to LSP diagnostics.
"""

from typing import List, TYPE_CHECKING

try:
    from lsprotocol import types as lsp
except ImportError:
    raise ImportError("LSP dependencies not installed. Install with: pip install yuho[lsp]")

from yuho.parser.wrapper import ParseError
from yuho.ast.type_inference import TypeInferenceVisitor
from yuho.ast.type_check import TypeCheckVisitor, TypeErrorInfo

if TYPE_CHECKING:
    from yuho.lsp.server import DocumentState
    from yuho.ast import ModuleNode

import logging

logger = logging.getLogger(__name__)


def run_type_checker(ast: "ModuleNode") -> List[TypeErrorInfo]:
    """Run type inference and type checking on AST, return errors."""
    try:
        # First run type inference
        infer_visitor = TypeInferenceVisitor()
        ast.accept(infer_visitor)

        # Then run type checking
        check_visitor = TypeCheckVisitor(infer_visitor.result)
        ast.accept(check_visitor)

        # Return all errors and warnings
        return check_visitor.result.errors + check_visitor.result.warnings
    except Exception as e:
        logger.warning(f"Type checking failed: {e}")
        return []


# Yuho's statute-level reserved words. When a parse error mentions one of
# these near an unknown token, the LSP's did-you-mean shim proposes the
# nearest match. Keeping the list inline so the LSP doesn't re-depend on
# the grammar just for this.
_YUHO_KEYWORDS = (
    "statute", "subsection", "definitions", "elements", "penalty",
    "illustration", "exception", "caselaw", "parties",
    "all_of", "any_of",
    "actus_reus", "mens_rea", "circumstance",
    "obligation", "prohibition", "permission",
    "imprisonment", "fine", "caning", "death", "supplementary", "minimum",
    "cumulative", "alternative", "or_both",
    "concurrent", "consecutive", "when",
    "effective", "repealed", "subsumes", "amends",
    "priority", "defeats", "unless", "fact", "conclusion", "presumed",
    "unlimited", "unspecified", "strokes",
    "referencing", "import",
    "struct", "enum", "fn", "match", "case", "consequence",
    "TRUE", "FALSE",
)


def _suggest_nearest_keyword(token: str) -> str | None:
    """If `token` looks like a typo of a known Yuho keyword, return the
    closest match. Uses Levenshtein-like edit distance via difflib so we
    don't pull in a new dependency.
    """
    if not token or len(token) < 2:
        return None
    import difflib
    matches = difflib.get_close_matches(token, _YUHO_KEYWORDS, n=1, cutoff=0.7)
    if matches and matches[0] != token:
        return matches[0]
    return None


def parse_error_to_diagnostic(error: ParseError) -> lsp.Diagnostic:
    """Convert ParseError to LSP Diagnostic. LDOC-inspired did-you-mean:
    if the error's problematic token looks like a typo of a Yuho keyword,
    append a `(did you mean `…`?)` hint."""
    loc = error.location

    msg = error.message
    # heuristic: many parser errors carry the offending token as a bare word
    # in backticks, quotes, or after "Unexpected token". Pull the first
    # identifier-shaped fragment and run did-you-mean on it.
    import re as _re
    token = None
    for patt in (r"`([A-Za-z_][A-Za-z_0-9]{1,})`",
                 r"\"([A-Za-z_][A-Za-z_0-9]{1,})\"",
                 r"'([A-Za-z_][A-Za-z_0-9]{1,})'",
                 r"Unexpected (?:token|keyword)\s+([A-Za-z_][A-Za-z_0-9]{1,})"):
        m = _re.search(patt, msg)
        if m:
            token = m.group(1)
            break
    suggestion = _suggest_nearest_keyword(token) if token else None
    if suggestion:
        msg = f"{msg} (did you mean `{suggestion}`?)"

    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=loc.line - 1, character=loc.col - 1),
            end=lsp.Position(line=loc.end_line - 1, character=loc.end_col - 1),
        ),
        message=msg,
        severity=lsp.DiagnosticSeverity.Error,
        source="yuho",
    )


def type_error_to_diagnostic(error: TypeErrorInfo) -> lsp.Diagnostic:
    """Convert TypeErrorInfo to LSP Diagnostic."""
    # TypeErrorInfo has 1-based line numbers, LSP uses 0-based
    line = max(0, error.line - 1)
    column = max(0, error.column - 1)

    severity = (
        lsp.DiagnosticSeverity.Error
        if error.severity == "error"
        else lsp.DiagnosticSeverity.Warning
    )

    return lsp.Diagnostic(
        range=lsp.Range(
            start=lsp.Position(line=line, character=column),
            end=lsp.Position(line=line, character=column + 1),
        ),
        message=error.message,
        severity=severity,
        source="yuho-typecheck",
    )


def collect_diagnostics(doc_state: "DocumentState") -> List[lsp.Diagnostic]:
    """Collect all diagnostics for a document."""
    diagnostics: List[lsp.Diagnostic] = []

    # Parser errors
    if doc_state.parse_result and doc_state.parse_result.errors:
        for error in doc_state.parse_result.errors:
            diagnostics.append(parse_error_to_diagnostic(error))

    # Semantic errors from type checker
    if doc_state.ast:
        type_errors = run_type_checker(doc_state.ast)
        for type_error in type_errors:
            diagnostics.append(type_error_to_diagnostic(type_error))

    return diagnostics
