#!/usr/bin/env python3
"""
Build the tree-sitter-yuho grammar.

This script can be run standalone or called during pip install.
"""

import subprocess
import shutil
import sys
from pathlib import Path


def find_tree_sitter_cli():
    """Find the tree-sitter CLI executable."""
    # Check if it's in PATH
    ts_path = shutil.which("tree-sitter")
    if ts_path:
        return ts_path

    # Check common npm global locations
    npm_paths = [
        Path.home() / ".npm-global" / "bin" / "tree-sitter",
        Path.home() / "node_modules" / ".bin" / "tree-sitter",
        Path("/usr/local/bin/tree-sitter"),
    ]
    for p in npm_paths:
        if p.exists():
            return str(p)

    return None


def install_tree_sitter_cli():
    """Attempt to install tree-sitter CLI."""
    print("tree-sitter CLI not found. Attempting to install...")

    # Try npm
    if shutil.which("npm"):
        try:
            subprocess.run(
                ["npm", "install", "-g", "tree-sitter-cli"],
                check=True,
                capture_output=True,
            )
            if find_tree_sitter_cli():
                print("Installed tree-sitter CLI via npm")
                return find_tree_sitter_cli()
        except subprocess.CalledProcessError:
            pass

    # Try pip (tree-sitter-cli package exists)
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "tree-sitter-cli"],
            check=True,
            capture_output=True,
        )
        if find_tree_sitter_cli():
            print("Installed tree-sitter CLI via pip")
            return find_tree_sitter_cli()
    except subprocess.CalledProcessError:
        pass

    return None


def build_grammar(grammar_dir: Path, output_dir: Path = None):
    """Build the tree-sitter grammar."""
    ts_cli = find_tree_sitter_cli()

    if not ts_cli:
        ts_cli = install_tree_sitter_cli()

    if not ts_cli:
        print("ERROR: Could not find or install tree-sitter CLI")
        print("\nPlease install manually:")
        print("  npm install -g tree-sitter-cli")
        print("  # or")
        print("  brew install tree-sitter")
        print("  # or")
        print("  cargo install tree-sitter-cli")
        return False

    print(f"Using tree-sitter CLI: {ts_cli}")

    # Generate parser
    print("Generating parser from grammar.js...")
    result = subprocess.run(
        [ts_cli, "generate"],
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
        [ts_cli, "build"],
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

    # Find and copy the library
    lib_extensions = [".dylib", ".so"]
    copied = False

    for ext in lib_extensions:
        lib_name = f"libtree-sitter-yuho{ext}"
        lib_path = grammar_dir / lib_name
        if lib_path.exists():
            dest = output_dir / lib_name
            shutil.copy2(lib_path, dest)
            print(f"Copied {lib_name} to {output_dir}")
            copied = True

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
