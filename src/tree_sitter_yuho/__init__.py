"""
tree-sitter-yuho Python bindings

Provides tree-sitter parser for the Yuho legal statute DSL.
"""

import ctypes
from pathlib import Path

__version__ = "0.1.0"

# Cache the language object
_language = None


def language():
    """
    Return the tree-sitter Language object for Yuho.

    Usage:
        from tree_sitter import Parser
        from tree_sitter_yuho import language

        parser = Parser()
        parser.language = language()
        tree = parser.parse(b"struct Foo { int x, }")
    """
    global _language
    if _language is not None:
        return _language

    from tree_sitter import Language

    # Try to load the compiled shared library
    lib_paths = [
        Path(__file__).parent / "yuho.so",
        Path(__file__).parent / "yuho.dylib",
        Path(__file__).parent / "libtree-sitter-yuho.so",
        Path(__file__).parent / "libtree-sitter-yuho.dylib",
        Path(__file__).parent.parent.parent.parent / "yuho.so",
        Path(__file__).parent.parent.parent.parent / "yuho.dylib",
    ]

    for lib_path in lib_paths:
        if lib_path.exists():
            try:
                # tree-sitter 0.21+ API: Load via ctypes
                lib = ctypes.CDLL(str(lib_path))
                lib.tree_sitter_yuho.restype = ctypes.c_void_p
                lang_ptr = lib.tree_sitter_yuho()
                _language = Language(lang_ptr)
                return _language
            except (OSError, AttributeError) as e:
                continue

    raise RuntimeError(
        "Could not find compiled tree-sitter-yuho library. "
        "Run './setup.sh' or 'make grammar' to build it."
    )


def get_language_path():
    """Return the path to the grammar directory for building."""
    return Path(__file__).parent.parent.parent.parent


__all__ = ["language", "get_language_path", "__version__"]
