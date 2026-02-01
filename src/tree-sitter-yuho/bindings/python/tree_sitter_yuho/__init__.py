"""
tree-sitter-yuho Python bindings

Provides tree-sitter parser for the Yuho legal statute DSL.
"""

from pathlib import Path

__version__ = "0.1.0"

def language():
    """
    Return the tree-sitter Language object for Yuho.

    Usage:
        from tree_sitter import Parser
        from tree_sitter_yuho import language

        parser = Parser()
        parser.set_language(language())
        tree = parser.parse(b"struct Foo { int x, }")
    """
    from tree_sitter import Language

    # Try to load the compiled shared library
    lib_paths = [
        Path(__file__).parent / "libtree-sitter-yuho.so",
        Path(__file__).parent / "libtree-sitter-yuho.dylib",
        Path(__file__).parent.parent.parent.parent / "build" / "libtree-sitter-yuho.so",
        Path(__file__).parent.parent.parent.parent / "build" / "libtree-sitter-yuho.dylib",
    ]

    for lib_path in lib_paths:
        if lib_path.exists():
            return Language(str(lib_path), "yuho")

    raise RuntimeError(
        "Could not find compiled tree-sitter-yuho library. "
        "Run 'tree-sitter generate && tree-sitter build' first."
    )


def get_language_path():
    """Return the path to the grammar.js file for building."""
    return Path(__file__).parent.parent.parent.parent


__all__ = ["language", "get_language_path", "__version__"]
