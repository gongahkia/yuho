"""
Custom Exceptions for Yuho

Provides specific exception types with helpful error messages for better
debugging and user experience.
"""

from typing import Optional, List, Any
from dataclasses import dataclass


@dataclass
class SourceLocation:
    """Represents a location in source code"""
    line: int
    column: int
    filename: Optional[str] = None

    def __str__(self) -> str:
        if self.filename:
            return f"{self.filename}:{self.line}:{self.column}"
        return f"line {self.line}, column {self.column}"


class YuhoError(Exception):
    """Base exception for all Yuho errors"""

    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        suggestion: Optional[str] = None
    ):
        self.message = message
        self.location = location
        self.suggestion = suggestion
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with location and suggestion"""
        parts = []

        if self.location:
            parts.append(f"Error at {self.location}")

        parts.append(self.message)

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        return "\n".join(parts)


class YuhoSyntaxError(YuhoError):
    """Syntax error in Yuho source code"""

    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        source_line: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.source_line = source_line
        super().__init__(message, location, suggestion)

    def format_message(self) -> str:
        """Format syntax error with source line"""
        parts = []

        if self.location:
            parts.append(f"Syntax Error at {self.location}")
        else:
            parts.append("Syntax Error")

        parts.append(self.message)

        if self.source_line:
            parts.append("\nSource:")
            parts.append(f"  {self.source_line}")
            if self.location:
                # Add pointer to error location
                pointer = " " * (self.location.column + 2) + "^"
                parts.append(pointer)

        if self.suggestion:
            parts.append(f"\n💡 Suggestion: {self.suggestion}")

        return "\n".join(parts)


class YuhoSemanticError(YuhoError):
    """Semantic error in Yuho code"""

    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        related_locations: Optional[List[SourceLocation]] = None,
        suggestion: Optional[str] = None
    ):
        self.related_locations = related_locations or []
        super().__init__(message, location, suggestion)

    def format_message(self) -> str:
        """Format semantic error with related locations"""
        parts = []

        if self.location:
            parts.append(f"Semantic Error at {self.location}")
        else:
            parts.append("Semantic Error")

        parts.append(self.message)

        if self.related_locations:
            parts.append("\nRelated locations:")
            for loc in self.related_locations:
                parts.append(f"  - {loc}")

        if self.suggestion:
            parts.append(f"\n💡 Suggestion: {self.suggestion}")

        return "\n".join(parts)


class YuhoTypeError(YuhoSemanticError):
    """Type mismatch or type-related error"""

    def __init__(
        self,
        message: str,
        expected_type: Optional[str] = None,
        actual_type: Optional[str] = None,
        location: Optional[SourceLocation] = None,
        suggestion: Optional[str] = None
    ):
        self.expected_type = expected_type
        self.actual_type = actual_type

        full_message = message
        if expected_type and actual_type:
            full_message += f"\n  Expected: {expected_type}\n  Got: {actual_type}"

        super().__init__(full_message, location, suggestion=suggestion)


class YuhoNameError(YuhoSemanticError):
    """Undefined or duplicate name error"""

    def __init__(
        self,
        name: str,
        message: str,
        location: Optional[SourceLocation] = None,
        available_names: Optional[List[str]] = None,
        suggestion: Optional[str] = None
    ):
        self.name = name
        self.available_names = available_names or []

        full_message = message

        # Suggest similar names
        if available_names and not suggestion:
            similar = self._find_similar_names(name, available_names)
            if similar:
                suggestion = f"Did you mean: {', '.join(similar)}?"

        super().__init__(full_message, location, suggestion=suggestion)

    @staticmethod
    def _find_similar_names(name: str, available: List[str], max_suggestions: int = 3) -> List[str]:
        """Find similar names using simple string similarity"""
        def similarity(a: str, b: str) -> float:
            """Calculate similarity between two strings"""
            if a == b:
                return 1.0
            # Simple Levenshtein-inspired similarity
            longer = max(len(a), len(b))
            if longer == 0:
                return 1.0
            same = sum(c1 == c2 for c1, c2 in zip(a, b))
            return same / longer

        scored = [(n, similarity(name.lower(), n.lower())) for n in available]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return names with similarity > 0.6
        return [n for n, score in scored[:max_suggestions] if score > 0.6]


class YuhoImportError(YuhoError):
    """Error importing or referencing other modules"""

    def __init__(
        self,
        module_name: str,
        message: str,
        location: Optional[SourceLocation] = None,
        suggestion: Optional[str] = None
    ):
        self.module_name = module_name
        full_message = f"Import error for module '{module_name}': {message}"
        super().__init__(full_message, location, suggestion)


class YuhoTranspilerError(YuhoError):
    """Error during transpilation to target format"""

    def __init__(
        self,
        target_format: str,
        message: str,
        location: Optional[SourceLocation] = None,
        suggestion: Optional[str] = None
    ):
        self.target_format = target_format
        full_message = f"Transpiler error ({target_format}): {message}"
        super().__init__(full_message, location, suggestion)


class YuhoFileError(YuhoError):
    """File-related error (not found, permission, etc.)"""

    def __init__(
        self,
        filename: str,
        message: str,
        suggestion: Optional[str] = None
    ):
        self.filename = filename
        full_message = f"File error for '{filename}': {message}"
        super().__init__(full_message, suggestion=suggestion)


class YuhoInternalError(YuhoError):
    """Internal compiler error (bug in Yuho itself)"""

    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        context: Optional[dict] = None
    ):
        self.context = context or {}
        full_message = (
            f"Internal error: {message}\n\n"
            "This is likely a bug in Yuho. Please report it at:\n"
            "https://github.com/gongahkia/yuho/issues"
        )
        super().__init__(full_message, location)


def format_error_list(errors: List[Exception]) -> str:
    """Format multiple errors into a readable list"""
    if not errors:
        return "No errors"

    if len(errors) == 1:
        return str(errors[0])

    parts = [f"Found {len(errors)} error(s):\n"]
    for i, error in enumerate(errors, 1):
        parts.append(f"\n{i}. {error}")

    return "\n".join(parts)


def suggest_fix_for_syntax_error(error_message: str) -> Optional[str]:
    """Suggest fixes for common syntax errors"""
    suggestions = {
        "expected ':'": "Check if you're missing a colon (:) in type annotations or match cases",
        "expected ';'": "Add a semicolon (;) at the end of the statement",
        "expected ':='": "Use := for assignment, not =",
        "unexpected '='": "Use := for assignment instead of =",
        "expected '{'": "Check if you're missing an opening brace {",
        "expected '}'": "Check if you're missing a closing brace }",
        "unexpected token": "Check your syntax - you might have a typo or wrong operator",
    }

    for pattern, suggestion in suggestions.items():
        if pattern in error_message.lower():
            return suggestion

    return None

