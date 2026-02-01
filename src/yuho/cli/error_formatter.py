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


# ANSI color codes
class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def supports_color() -> bool:
    """Check if terminal supports color."""
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

    previous_row = range(len(s2) + 1)
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


# Known keywords and types for suggestions
YUHO_KEYWORDS = [
    "struct", "fn", "match", "case", "consequence", "pass", "return",
    "statute", "definitions", "elements", "penalty", "illustration",
    "import", "from", "actus_reus", "mens_rea", "circumstance",
    "imprisonment", "fine", "supplementary", "TRUE", "FALSE",
]

YUHO_TYPES = [
    "int", "float", "bool", "string", "money", "percent", "date", "duration", "void",
]


def suggest_keyword(typo: str) -> Optional[str]:
    """Suggest a correct keyword for a typo."""
    candidates = YUHO_KEYWORDS + YUHO_TYPES
    similar = find_similar(typo, candidates, max_distance=2)
    return similar[0] if similar else None


def format_suggestion(error: ParseError, source: str) -> Optional[str]:
    """Generate a suggestion for fixing an error."""
    # Try to extract the problematic token from the error
    if "Unexpected" in error.message:
        # Extract the token text
        import re
        match = re.search(r"Unexpected syntax: ['\"]?([^'\"]+)['\"]?", error.message)
        if match:
            token = match.group(1).strip()
            suggestion = suggest_keyword(token)
            if suggestion:
                return f"Did you mean '{suggestion}'?"

    return None
