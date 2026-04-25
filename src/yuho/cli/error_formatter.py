"""
Rich error formatting for CLI output.

Provides source line display with carets pointing to error locations,
and Levenshtein-based suggestions for typos.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

from yuho.parser.source_location import SourceLocation
from yuho.parser.wrapper import ParseError


# Global color control - can be set by CLI
# None = auto-detect, True = force on, False = force off
COLOR_ENABLED: Optional[bool] = None


# ANSI color codes
class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def supports_color() -> bool:
    """
    Check if terminal supports color.

    Respects the global COLOR_ENABLED flag if set,
    otherwise auto-detects based on terminal capabilities.
    """
    global COLOR_ENABLED

    # If explicitly set, use that value
    if COLOR_ENABLED is not None:
        return COLOR_ENABLED

    # Auto-detect
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def colorize(text: str, color: str) -> str:
    """Apply color if supported."""
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def format_error(error: ParseError, source: str) -> str:
    """
    Format a parse error with source context.

    Shows the error location with the source line and a caret
    pointing to the exact position.
    """
    lines = source.splitlines()
    loc = error.location

    output: List[str] = []

    # Error header
    header = f"{loc}: {error.message}"
    output.append(colorize(f"error: {header}", Colors.RED + Colors.BOLD))

    # Source context (line before, error line, line after)
    if 1 <= loc.line <= len(lines):
        # Line before
        if loc.line > 1:
            line_before = lines[loc.line - 2]
            output.append(f"  {colorize(str(loc.line - 1).rjust(4), Colors.DIM)} | {line_before}")

        # Error line
        error_line = lines[loc.line - 1]
        output.append(f"  {colorize(str(loc.line).rjust(4), Colors.CYAN)} | {error_line}")

        # Caret line
        caret_padding = " " * (loc.col - 1 + 7)  # 7 = "  XXXX | "
        if loc.end_col > loc.col:
            caret = "^" * (loc.end_col - loc.col)
        else:
            caret = "^"
        output.append(colorize(f"{caret_padding}{caret}", Colors.RED))

        # Line after
        if loc.line < len(lines):
            line_after = lines[loc.line]
            output.append(f"  {colorize(str(loc.line + 1).rjust(4), Colors.DIM)} | {line_after}")

    return "\n".join(output)


def format_errors(errors: List[ParseError], source: str, file: str) -> str:
    """Format multiple errors."""
    if not errors:
        return ""

    output: List[str] = []
    output.append(colorize(f"Found {len(errors)} error(s) in {file}:", Colors.BOLD))
    output.append("")

    for error in errors:
        output.append(format_error(error, source))
        output.append("")

    return "\n".join(output)


# =============================================================================
# Levenshtein distance for typo suggestions
# =============================================================================


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein (edit) distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def find_similar(word: str, candidates: List[str], max_distance: int = 2) -> List[str]:
    """Find candidates similar to word within max_distance."""
    similar = []
    for candidate in candidates:
        dist = levenshtein_distance(word.lower(), candidate.lower())
        if dist <= max_distance:
            similar.append((dist, candidate))

    # Sort by distance
    similar.sort(key=lambda x: x[0])
    return [s[1] for s in similar]


# Known keywords and types for suggestions.
# Kept exhaustive so a typo on any first-class primitive resolves to a hint.
YUHO_KEYWORDS = [
    # top-level constructs
    "struct", "fn", "enum", "match", "case", "consequence", "pass", "return",
    "import", "from", "if", "else", "while", "for",
    # statute shape
    "statute", "subsection", "definitions", "elements", "penalty",
    "illustration", "exception", "caselaw", "parties", "metadata",
    # element kinds (G1, G11)
    "actus_reus", "mens_rea", "circumstance",
    "obligation", "prohibition", "permission",
    "all_of", "any_of",
    # element qualifiers (Phase 12)
    "burden", "prosecution", "defence",
    "beyond_reasonable_doubt", "balance_of_probabilities", "prima_facie",
    "causedBy", "actor", "patient", "precedes", "during", "after",
    # penalty primitives + combinators (G8, G9, G12, G14)
    "imprisonment", "fine", "caning", "death_penalty", "supplementary",
    "cumulative", "alternative", "or_both", "when",
    "unlimited", "unspecified", "life", "mandatory_min",
    "concurrent", "consecutive",
    # statute-level lifecycle (G3, G6, G10)
    "effective", "repealed", "subsumes", "amends", "referencing",
    "priority", "defeats", "guard", "presumed", "unless",
    # literals
    "TRUE", "FALSE", "true", "false",
]

YUHO_TYPES = [
    "int", "float", "bool", "string",
    "money", "percent", "date", "duration", "void",
    "list", "set", "map", "option",
]


def suggest_keyword(typo: str, k: int = 3, max_distance: int = 2) -> List[str]:
    """Return up to ``k`` closest keyword/type candidates for a typo.

    Empty list if nothing within ``max_distance`` is found.
    """
    candidates = YUHO_KEYWORDS + YUHO_TYPES
    return find_similar(typo, candidates, max_distance=max_distance)[:k]


# =============================================================================
# Structured fix-it patterns
# =============================================================================
#
# Each fix-it is a check (regex on the error context) plus a hint string.
# Order matters: the first match wins, so most-specific patterns first.

import re as _re


def _extract_first_identifier(text: str) -> Optional[str]:
    """Pull the first bareword identifier out of an error blob."""
    if not text:
        return None
    m = _re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", text)
    return m.group(1) if m else None


def _line_at(source: str, line_no: int) -> str:
    lines = source.splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1]
    return ""


_FIXITS = [
    # ---- assignment operator ---------------------------------------------
    (
        lambda err, src: (
            "Unexpected" in err.message
            and _re.search(r"=(?!=|>)\s", _line_at(src, err.location.line) or "")
            and ":=" not in (_line_at(src, err.location.line) or "")
        ),
        "Yuho uses `:=` for assignment, not `=`. Replace `=` with `:=`.",
    ),
    # ---- missing semicolon -----------------------------------------------
    (
        lambda err, src: err.message.startswith("Missing semicolon"),
        "Add a `;` at the end of the previous statement. Yuho terminates each "
        "field declaration (e.g. `fine := unlimited;`) with a semicolon.",
    ),
    # ---- missing close brace ---------------------------------------------
    (
        lambda err, src: "closing brace" in err.message.lower(),
        "An open `{` was never closed. Check that every `statute`, `elements`, "
        "`penalty`, or `subsection` block has a matching `}`.",
    ),
    # ---- fabricated penalty cap ------------------------------------------
    (
        lambda err, src: _re.search(r"fine\s*:=\s*\$0", _line_at(src, err.location.line) or "")
                       and "with fine" not in src.lower(),
        "If the canonical statute says `with fine` without a number, use "
        "`fine := unlimited;` (G8 sentinel). Numeric ranges should match a "
        "stated maximum in the source text.",
    ),
    # ---- caning fabrication ----------------------------------------------
    (
        lambda err, src: _re.search(r"caning\s*:=\s*\d+\s*\.\.\s*\d+", _line_at(src, err.location.line) or ""),
        "If the canonical statute says `liable to caning` without a stroke "
        "count, use `caning := unspecified;` (G14 sentinel). Avoid invented "
        "stroke ranges.",
    ),
    # ---- `or_both` outside `penalty or_both` block ----------------------
    (
        lambda err, src: "or_both" in err.message and "penalty or_both" not in src,
        "Use `penalty or_both { ... }` as the block header. The bare keyword "
        "`or_both;` is not valid; it must follow `penalty`.",
    ),
]


def _structural_hint(error: ParseError, source: str) -> Optional[str]:
    """Run the fix-it patterns and return the first hit, if any."""
    for predicate, hint in _FIXITS:
        try:
            if predicate(error, source):
                return hint
        except Exception:
            continue
    return None


def format_suggestions(error: ParseError, source: str) -> List[str]:
    """Generate every applicable fix-it hint for a parse error.

    Returns hints in priority order:
    1. Structured pattern matches (operator typos, sentinel use, missing braces).
    2. Levenshtein "did you mean" against the full keyword/type set, where
       the unexpected token's first identifier is short enough to be a typo.

    May return an empty list if nothing applies.
    """
    out: List[str] = []

    # 1. Structural pattern matches (may produce 0..N hints).
    structural = _structural_hint(error, source)
    if structural:
        out.append(structural)

    # 2. Levenshtein fallback for unexpected-token errors.
    if "Unexpected" in error.message:
        match = _re.search(r"Unexpected syntax: ['\"]?(.+?)['\"]?(?:$|\.\.\.)", error.message)
        if match:
            raw = match.group(1).strip()
            candidate = _extract_first_identifier(raw)
            if candidate and len(candidate) >= 3:
                suggestions = suggest_keyword(candidate, k=3)
                if suggestions:
                    if len(suggestions) == 1:
                        out.append(f"Did you mean `{suggestions[0]}`?")
                    else:
                        head = suggestions[0]
                        rest = ", ".join(f"`{s}`" for s in suggestions[1:])
                        out.append(f"Did you mean `{head}`? (also: {rest})")

    # Dedupe while preserving order.
    seen = set()
    deduped: List[str] = []
    for h in out:
        if h not in seen:
            seen.add(h)
            deduped.append(h)
    return deduped


def format_suggestion(error: ParseError, source: str) -> Optional[str]:
    """Backward-compatible single-hint API. Returns the first applicable hint."""
    hints = format_suggestions(error, source)
    return hints[0] if hints else None
