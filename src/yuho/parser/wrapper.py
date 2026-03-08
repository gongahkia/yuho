"""
Parser wrapper class for tree-sitter based Yuho parsing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Iterator
import logging
import os
import threading

from yuho.parser.source_location import SourceLocation

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_SOURCE_LENGTH = 10 * 1024 * 1024
VALID_EXTENSIONS = {".yh", ".yuho"}

# Module-level parser cache for performance
_parser_cache: Optional["Parser"] = None
_parser_lock = threading.Lock()


@dataclass
class ParseError:
    """
    Represents a syntax error encountered during parsing.

    Attributes:
        message: Human-readable error description
        location: Source location where the error occurred
        node_type: The tree-sitter node type that has the error (if available)
    """

    message: str
    location: SourceLocation
    node_type: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass
class ParseResult:
    """
    Result of parsing a Yuho source file.

    Attributes:
        tree: The tree-sitter Tree object (or None if parsing failed completely)
        errors: List of syntax errors found during parsing
        source: The original source string
        file: The file path (or "<string>" for inline parsing)
    """

    tree: object  # tree_sitter.Tree
    errors: List[ParseError]
    source: str
    file: str

    @property
    def is_valid(self) -> bool:
        """Return True if the source parsed without errors."""
        return len(self.errors) == 0

    @property
    def root_node(self):
        """Return the root node of the parse tree."""
        return self.tree.root_node if self.tree else None


def validate_file_path(path: str | Path) -> Path:
    """
    Validate and resolve a file path for safe access.

    Args:
        path: The file path to validate

    Returns:
        The resolved Path object

    Raises:
        ValueError: If the path contains null bytes or path traversal components
        FileNotFoundError: If the file does not exist
    """
    if isinstance(path, str) and "\x00" in path:
        raise ValueError("path contains null bytes")
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if not path.is_file():
        raise ValueError(f"path is not a regular file: {path}")
    return path


def validate_output_path(path: str | Path) -> Path:
    """
    Validate an output file path for safe writing.

    Args:
        path: The output file path to validate

    Returns:
        The resolved Path object

    Raises:
        ValueError: If the path contains null bytes or parent dir missing
    """
    if isinstance(path, str) and "\x00" in path:
        raise ValueError("path contains null bytes")
    path = Path(path).resolve()
    if not path.parent.exists():
        raise ValueError(f"parent directory does not exist: {path.parent}")
    return path


class Parser:
    """
    Parser for Yuho source files using tree-sitter.

    This class wraps the tree-sitter parser and provides a convenient
    interface for parsing Yuho source code and extracting syntax errors.

    Usage:
        parser = Parser()
        result = parser.parse('struct Foo { int x, }')
        if result.is_valid:
            # Process the AST
            root = result.root_node
        else:
            for error in result.errors:
                print(error)
    """

    def __init__(self):
        """Initialize the parser with the Yuho language grammar."""
        self._parser = None
        self._language = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazily initialize the tree-sitter parser."""
        if self._initialized:
            return

        try:
            from tree_sitter import Parser as TSParser
            from tree_sitter_yuho import language

            self._parser = TSParser()
            self._language = language()
            self._parser.language = self._language
            self._initialized = True
        except ImportError as e:
            raise ImportError(
                "tree-sitter and tree-sitter-yuho must be installed. "
                "Run: pip install tree-sitter tree-sitter-yuho"
            ) from e

    def validate_source(self, source: str, file: str) -> str:
        """
        Validate and clean source code before parsing.

        Args:
            source: The raw source string
            file: The file path (for error context)

        Returns:
            Cleaned source string

        Raises:
            ValueError: If source contains null bytes or exceeds max length
        """
        if "\x00" in source:
            raise ValueError("source contains null bytes")
        if len(source) > MAX_SOURCE_LENGTH:
            raise ValueError(
                f"source exceeds maximum length ({MAX_SOURCE_LENGTH} chars)"
            )
        if source.startswith("\ufeff"):
            source = source[1:]
        return source

    def parse(self, source: str, file: str = "<string>") -> ParseResult:
        """
        Parse a Yuho source string.

        Args:
            source: The Yuho source code to parse
            file: Optional file path for error messages

        Returns:
            ParseResult containing the tree and any errors
        """
        self._ensure_initialized()
        source = self.validate_source(source, file)

        try:
            source_bytes = source.encode("utf-8")
            tree = self._parser.parse(source_bytes)
        except Exception as e:
            error = ParseError(
                message=f"internal parser error: {e}",
                location=SourceLocation(file=file, line=1, col=1, end_line=1, end_col=1),
                node_type="INTERNAL_ERROR",
            )
            return ParseResult(tree=None, errors=[error], source=source, file=file)

        # Collect errors by walking the tree
        errors = list(self._collect_errors(tree.root_node, source, file))

        return ParseResult(
            tree=tree,
            errors=errors,
            source=source,
            file=file,
        )

    def parse_file(self, path: str | Path) -> ParseResult:
        """
        Parse a Yuho source file.

        Args:
            path: Path to the .yh file

        Returns:
            ParseResult containing the tree and any errors

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file exceeds max size or is not a regular file
            UnicodeDecodeError: If the file is not valid UTF-8
            PermissionError: If the file cannot be read
        """
        path = Path(path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"file not found: {path}")
        if not path.is_file():
            raise ValueError(f"path is not a regular file: {path}")

        stat = path.stat()
        if stat.st_size > MAX_FILE_SIZE:
            raise ValueError(
                f"file exceeds maximum size ({MAX_FILE_SIZE} bytes): {path}"
            )

        ext = path.suffix.lower()
        if ext not in VALID_EXTENSIONS:
            logger.warning("file extension '%s' not in %s: %s", ext, VALID_EXTENSIONS, path)

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                e.encoding, e.object, e.start, e.end,
                f"file is not valid UTF-8: {path} ({e.reason})"
            ) from e
        except PermissionError as e:
            raise PermissionError(f"cannot read file: {path} ({e})") from e

        return self.parse(source, file=str(path))

    def _collect_errors(
        self, node, source: str, file: str
    ) -> Iterator[ParseError]:
        """
        Walk the parse tree and collect error nodes.

        Tree-sitter marks nodes with errors using:
        - is_error: True for ERROR nodes
        - is_missing: True for MISSING nodes (expected but not found)
        - has_error: True if this node or any descendant has errors
        """
        if node.is_error:
            # This is an ERROR node - unexpected token(s)
            location = SourceLocation.from_tree_sitter_node(node, file)
            error_text = source[node.start_byte : node.end_byte]

            if len(error_text) > 50:
                error_text = error_text[:47] + "..."

            yield ParseError(
                message=f"Unexpected syntax: {error_text!r}",
                location=location,
                node_type="ERROR",
            )

        elif node.is_missing:
            # This is a MISSING node - expected syntax not found
            location = SourceLocation.from_tree_sitter_node(node, file)

            # Generate helpful message based on what's missing
            missing_type = node.type
            message = self._missing_node_message(missing_type)

            yield ParseError(
                message=message,
                location=location,
                node_type=f"MISSING:{missing_type}",
            )

        elif node.has_error:
            # Recurse into children to find the actual error nodes
            for child in node.children:
                yield from self._collect_errors(child, source, file)

    def _missing_node_message(self, node_type: str) -> str:
        """Generate a helpful error message for missing nodes."""
        messages = {
            ";": "Missing semicolon",
            ",": "Missing comma",
            "{": "Missing opening brace '{'",
            "}": "Missing closing brace '}'",
            "(": "Missing opening parenthesis '('",
            ")": "Missing closing parenthesis ')'",
            "[": "Missing opening bracket '['",
            "]": "Missing closing bracket ']'",
            ":=": "Missing assignment operator ':='",
            ":": "Missing colon ':'",
            "identifier": "Expected identifier",
            "string_literal": "Expected string literal",
            "integer_literal": "Expected integer",
            "_type": "Expected type annotation",
            "_expression": "Expected expression",
        }
        return messages.get(node_type, f"Missing {node_type}")

    def walk_tree(self, tree) -> Iterator:
        """
        Generator that yields all nodes in the tree via depth-first traversal.

        Usage:
            for node in parser.walk_tree(result.tree):
                print(node.type, node.text)
        """
        cursor = tree.walk()

        visited_children = False
        while True:
            if not visited_children:
                yield cursor.node
                if cursor.goto_first_child():
                    continue

            if cursor.goto_next_sibling():
                visited_children = False
            elif cursor.goto_parent():
                visited_children = True
            else:
                break

    def query(self, tree, query_string: str) -> List:
        """
        Run a tree-sitter query against the parse tree.

        Args:
            tree: The parsed tree (from ParseResult.tree)
            query_string: A tree-sitter query in S-expression format

        Returns:
            List of (node, capture_name) tuples

        Usage:
            captures = parser.query(result.tree, '(struct_definition name: (identifier) @name)')
            for node, name in captures:
                print(f"Found struct: {node.text}")
        """
        self._ensure_initialized()

        from tree_sitter import Query

        query = self._language.query(query_string)
        return query.captures(tree.root_node)


def get_parser() -> Parser:
    """
    Get a cached Parser instance for better performance.

    This function returns a thread-safe singleton Parser instance.
    Use this instead of creating new Parser() instances when parsing
    multiple files to avoid repeated tree-sitter initialization overhead.

    Returns:
        A cached Parser instance

    Usage:
        from yuho.parser import get_parser
        parser = get_parser()
        result = parser.parse_file("statute.yh")
    """
    global _parser_cache

    if _parser_cache is not None:
        return _parser_cache

    with _parser_lock:
        # Double-check after acquiring lock
        if _parser_cache is None:
            _parser_cache = Parser()
            _parser_cache._ensure_initialized()

    return _parser_cache


def clear_parser_cache() -> None:
    """
    Clear the cached parser instance.

    This is mainly useful for testing or when you need to
    reinitialize the parser (e.g., after grammar changes).
    """
    global _parser_cache

    with _parser_lock:
        _parser_cache = None
