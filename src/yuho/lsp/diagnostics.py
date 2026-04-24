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


# ---------------------------------------------------------------------------
# LSP buff-up — fidelity diagnostics
# ---------------------------------------------------------------------------
# These compare the encoded .yh against the canonical _raw/act.json entry
# to catch the classes of fidelity bugs the Phase D L3 review flagged:
#   G4  — encoded illustration count less than canonical.
#   G11 — all_of where the statute text says "or".
#   fabricated fine cap: statute says "with fine" with no numeric amount,
#       encoding uses a numeric fine range instead of `fine := unlimited`.
#   fabricated caning range: statute says "liable to caning" with no
#       stroke count, encoding uses a numeric range or `0 .. 0 strokes`
#       instead of `caning := unspecified`.

_CANONICAL_RAW_CACHE: dict[str, dict] | None = None


def _load_canonical_raw() -> dict[str, dict]:
    """Load _raw/act.json once per LSP process, keyed by section number."""
    global _CANONICAL_RAW_CACHE
    if _CANONICAL_RAW_CACHE is not None:
        return _CANONICAL_RAW_CACHE
    try:
        import json as _j
        from pathlib import Path as _P
        here = _P(__file__).resolve()
        root = here
        for _ in range(6):
            root = root.parent
            if (root / "library" / "penal_code").is_dir():
                break
        raw_path = root / "library" / "penal_code" / "_raw" / "act.json"
        if not raw_path.is_file():
            _CANONICAL_RAW_CACHE = {}
            return _CANONICAL_RAW_CACHE
        d = _j.loads(raw_path.read_text())
        _CANONICAL_RAW_CACHE = {
            s["number"]: s for s in d.get("sections", []) if s.get("number")
        }
    except Exception:
        _CANONICAL_RAW_CACHE = {}
    return _CANONICAL_RAW_CACHE


def _canonical_illustration_count(canonical: dict) -> int:
    """Count canonical illustrations — both top-level illustrations + any
    sub_items that look like alphabetic illustration paragraphs (`(a)`, `(b)`)
    under an 'Illustrations' heading."""
    import re as _re
    count = 0
    for it in canonical.get("sub_items", []):
        kind = it.get("kind")
        if kind == "illustration":
            count += 1
        elif kind == "item" and _re.match(r"^\s*\([a-z]\)", it.get("text", "").strip()):
            count += 1
    return count


def _fidelity_diagnostics_for_statute(
    source: str, statute, canonical: dict
) -> List[lsp.Diagnostic]:
    """Inspect a single encoded statute against its canonical entry.
    Returns a list of LSP Diagnostics for fidelity-class issues."""
    import re as _re
    out: List[lsp.Diagnostic] = []
    loc = statute.source_location
    if not loc:
        return out
    head_range = lsp.Range(
        start=lsp.Position(line=loc.line - 1, character=0),
        end=lsp.Position(line=loc.line - 1, character=max(1, loc.col)),
    )

    # G4: illustration count mismatch
    canonical_ills = _canonical_illustration_count(canonical)
    encoded_ills = len(statute.illustrations)
    if canonical_ills and encoded_ills < canonical_ills:
        out.append(
            lsp.Diagnostic(
                range=head_range,
                message=(
                    f"fidelity: s{statute.section_number} has {encoded_ills} "
                    f"illustration(s) encoded but canonical has {canonical_ills}. "
                    "Missing illustrations lose statutory authority."
                ),
                severity=lsp.DiagnosticSeverity.Warning,
                source="yuho-fidelity",
            )
        )

    # Fabricated fine cap: canonical mentions fine with no dollar amount,
    # encoding uses numeric fine range.
    canonical_text = canonical.get("text", "")
    canonical_mentions_fine = "fine" in canonical_text.lower()
    canonical_has_fine_number = bool(
        _re.search(r"\$[\d,]+", canonical_text)
        or _re.search(r"(extend to|not less than|up to)\s+\$?[0-9][0-9,]*", canonical_text)
    )
    if canonical_mentions_fine and not canonical_has_fine_number:
        # does the encoding invent a cap?
        # look for fine := <money> .. <money>, inside this statute's text span
        if statute.penalty and statute.penalty.fine_max and not statute.penalty.fine_unlimited:
            out.append(
                lsp.Diagnostic(
                    range=head_range,
                    message=(
                        f"fidelity: canonical says only 'with fine' for s{statute.section_number} "
                        "(no dollar amount), but encoding has a numeric fine cap. "
                        "Use `fine := unlimited` (G8)."
                    ),
                    severity=lsp.DiagnosticSeverity.Warning,
                    source="yuho-fidelity",
                )
            )

    # Fabricated caning stroke count
    canonical_has_caning = "caning" in canonical_text.lower()
    canonical_has_stroke_num = bool(
        _re.search(r"(\d+)\s*strokes?", canonical_text)
        or _re.search(r"(not less than|at least|up to|extend to)\s+\d+", canonical_text)
    )
    if canonical_has_caning and not canonical_has_stroke_num:
        if (
            statute.penalty
            and (statute.penalty.caning_max is not None or statute.penalty.caning_min is not None)
            and not statute.penalty.caning_unspecified
        ):
            out.append(
                lsp.Diagnostic(
                    range=head_range,
                    message=(
                        f"fidelity: canonical says 'liable to caning' for s{statute.section_number} "
                        "with no stroke count, but encoding has a numeric range. "
                        "Use `caning := unspecified` (G14)."
                    ),
                    severity=lsp.DiagnosticSeverity.Warning,
                    source="yuho-fidelity",
                )
            )

    # G11: all_of where canonical uses "or" as the top-level connective
    # between elements. Heuristic: if canonical text has "with intent ... , or ..." /
    # "any one of" / " or " within the offence-definition sentence, and the
    # top-level elements block uses all_of with ≥2 mens_rea entries, flag.
    # Very conservative — only flag when the pattern is strong enough to
    # avoid false positives.
    if statute.elements:
        first = statute.elements[0] if statute.elements else None
        is_all_of_group = (
            hasattr(first, "combinator") and getattr(first, "combinator", None) == "all_of"
        )
        if is_all_of_group:
            mens_count = sum(
                1 for m in getattr(first, "members", ())
                if hasattr(m, "element_type") and m.element_type == "mens_rea"
            )
            if mens_count >= 2:
                t = canonical_text.lower()
                disjunctive_signal = (
                    " or with intent " in t
                    or " or knowing " in t
                    or " or believing " in t
                    or " or intending " in t
                    or "any one of " in t
                    or "; or " in t
                )
                if disjunctive_signal:
                    out.append(
                        lsp.Diagnostic(
                            range=head_range,
                            message=(
                                f"fidelity: canonical text for s{statute.section_number} uses disjunctive "
                                "connectives but the top-level elements block uses `all_of` with "
                                "multiple mens_rea. Review whether this should be `any_of`. (G11)"
                            ),
                            severity=lsp.DiagnosticSeverity.Information,
                            source="yuho-fidelity",
                        )
                    )

    return out


def collect_fidelity_diagnostics(doc_state: "DocumentState") -> List[lsp.Diagnostic]:
    """Per-statute fidelity diagnostics against canonical _raw/act.json."""
    if not doc_state.ast: return []
    canonical_index = _load_canonical_raw()
    if not canonical_index: return []
    source = getattr(doc_state, "source", None) or getattr(doc_state, "text", "") or ""
    out: List[lsp.Diagnostic] = []
    for statute in doc_state.ast.statutes:
        canonical = canonical_index.get(statute.section_number)
        if not canonical:
            continue
        out.extend(_fidelity_diagnostics_for_statute(source, statute, canonical))
    return out


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

    # Fidelity diagnostics (G4, G11, fabricated fine/caning) comparing
    # the encoded statute against the canonical _raw/act.json entry.
    diagnostics.extend(collect_fidelity_diagnostics(doc_state))

    return diagnostics
