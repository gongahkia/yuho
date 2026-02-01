"""
Source location tracking for AST nodes and error reporting.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """
    Represents a span of source code with file, line, and column information.

    All line and column numbers are 1-indexed for user-facing display.
    Internally, tree-sitter uses 0-indexed positions which are converted
    in the Parser wrapper.

    Attributes:
        file: Path to the source file (or "<string>" for inline parsing)
        line: Starting line number (1-indexed)
        col: Starting column number (1-indexed)
        end_line: Ending line number (1-indexed)
        end_col: Ending column number (1-indexed, exclusive)
        offset: Byte offset from start of file
        end_offset: Byte offset of end position
    """

    file: str
    line: int
    col: int
    end_line: int
    end_col: int
    offset: Optional[int] = None
    end_offset: Optional[int] = None

    def __str__(self) -> str:
        """Format as 'file:line:col' for error messages."""
        if self.line == self.end_line:
            return f"{self.file}:{self.line}:{self.col}"
        return f"{self.file}:{self.line}:{self.col}-{self.end_line}:{self.end_col}"

    def __repr__(self) -> str:
        return (
            f"SourceLocation(file={self.file!r}, "
            f"line={self.line}, col={self.col}, "
            f"end_line={self.end_line}, end_col={self.end_col})"
        )

    @classmethod
    def from_tree_sitter_node(cls, node, file: str = "<string>") -> "SourceLocation":
        """
        Create a SourceLocation from a tree-sitter node.

        Tree-sitter uses 0-indexed rows and columns, so we add 1 for
        user-facing display.
        """
        start_point = node.start_point
        end_point = node.end_point

        return cls(
            file=file,
            line=start_point[0] + 1,
            col=start_point[1] + 1,
            end_line=end_point[0] + 1,
            end_col=end_point[1] + 1,
            offset=node.start_byte,
            end_offset=node.end_byte,
        )

    @classmethod
    def unknown(cls, file: str = "<unknown>") -> "SourceLocation":
        """Create a placeholder location for generated or unknown nodes."""
        return cls(file=file, line=0, col=0, end_line=0, end_col=0)

    def contains(self, other: "SourceLocation") -> bool:
        """Check if this location fully contains another location."""
        if self.file != other.file:
            return False

        if self.offset is not None and other.offset is not None:
            return (
                self.offset <= other.offset
                and self.end_offset >= other.end_offset
            )

        # Fallback to line/col comparison
        start_before = (self.line < other.line) or (
            self.line == other.line and self.col <= other.col
        )
        end_after = (self.end_line > other.end_line) or (
            self.end_line == other.end_line and self.end_col >= other.end_col
        )
        return start_before and end_after

    def merge(self, other: "SourceLocation") -> "SourceLocation":
        """Create a new location spanning from this location to another."""
        if self.file != other.file:
            raise ValueError(f"Cannot merge locations from different files: {self.file} and {other.file}")

        return SourceLocation(
            file=self.file,
            line=min(self.line, other.line),
            col=self.col if self.line <= other.line else other.col,
            end_line=max(self.end_line, other.end_line),
            end_col=self.end_col if self.end_line >= other.end_line else other.end_col,
            offset=min(self.offset, other.offset) if self.offset and other.offset else None,
            end_offset=max(self.end_offset, other.end_offset) if self.end_offset and other.end_offset else None,
        )
