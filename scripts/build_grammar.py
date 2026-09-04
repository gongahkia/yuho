#!/usr/bin/env python3
"""
Build the tree-sitter-yuho grammar.

This script uses only the lockfile-pinned local Node CLI. It never installs a
global or unpinned Tree-sitter toolchain.
"""

import subprocess
import sys
from pathlib import Path


def find_tree_sitter_cli(grammar_dir: Path) -> Path | None:
    """Return the lockfile-pinned repository-local Tree-sitter CLI."""
    candidate = grammar_dir / "node_modules" / ".bin" / "tree-sitter"
    return candidate if candidate.is_file() else None


def build_grammar(grammar_dir: Path, output_dir: Path | None = None) -> bool:
    """Build the tree-sitter grammar."""
    ts_cli = find_tree_sitter_cli(grammar_dir)
    if not ts_cli:
        print("ERROR: Missing repository-local Tree-sitter CLI")
        print(f"Run `npm ci` in {grammar_dir} and retry.")
        return False

    print(f"Using tree-sitter CLI: {ts_cli}")

    # Generate parser
    print("Generating parser from grammar.js...")
    result = subprocess.run(
        [str(ts_cli), "generate"],
        cwd=grammar_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Failed to generate parser:\n{result.stderr}")
        return False

    # Build shared library
    print("Building shared library...")
    result = subprocess.run(
        [str(ts_cli), "build"],
        cwd=grammar_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Failed to build library:\n{result.stderr}")
        return False

    # Copy to output directory
    if output_dir is None:
        output_dir = grammar_dir / "bindings" / "python" / "tree_sitter_yuho"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find and copy the library.
    # Tree-sitter CLI 0.22+ emits yuho.dylib; older emitted libtree-sitter-yuho.dylib.
    # Copy whichever exists under both names so the Python binding finds it.
    # Destinations: the in-tree binding dir AND the installed package dir
    # (both are needed for different import paths).
    lib_extensions = [".dylib", ".so"]
    copied = False

    installed_pkg_dir = grammar_dir.parent / "tree_sitter_yuho"
    for ext in lib_extensions:
        for src_name in (f"yuho{ext}", f"libtree-sitter-yuho{ext}"):
            lib_path = grammar_dir / src_name
            if lib_path.exists():
                for dest_name in (f"yuho{ext}", f"libtree-sitter-yuho{ext}"):
                    shutil.copy2(lib_path, output_dir / dest_name)
                    if installed_pkg_dir.exists():
                        shutil.copy2(lib_path, installed_pkg_dir / dest_name)
                print(f"Copied {src_name} → {output_dir} and {installed_pkg_dir}")
                copied = True
                break
        if copied:
            break

    if not copied:
        # Check build directory
        build_dir = grammar_dir / "build"
        if build_dir.exists():
            for ext in lib_extensions:
                lib_name = f"libtree-sitter-yuho{ext}"
                lib_path = build_dir / lib_name
                if lib_path.exists():
                    dest = output_dir / lib_name
                    shutil.copy2(lib_path, dest)
                    print(f"Copied {lib_name} to {output_dir}")
                    copied = True

    if not copied:
        print("WARNING: Could not find built library to copy")

    print("Grammar build complete!")
    return True


def main():
    """Main entry point."""
    # Find the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    grammar_dir = project_root / "src" / "tree-sitter-yuho"

    if not grammar_dir.exists():
        print(f"ERROR: Grammar directory not found: {grammar_dir}")
        sys.exit(1)

    if not (grammar_dir / "grammar.js").exists():
        print(f"ERROR: grammar.js not found in {grammar_dir}")
        sys.exit(1)

    success = build_grammar(grammar_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
