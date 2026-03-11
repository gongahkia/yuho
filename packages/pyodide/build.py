"""Build script for Pyodide-compatible Yuho wheel.

Produces a pure-Python wheel that can run inside Pyodide (browser Python).
The tree-sitter native lib is excluded; use the WASM parser instead.

Usage:
    python build.py            # produces dist/yuho-*-py3-none-any.whl
    python build.py --install  # also micropip.install() inside Pyodide
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"
DIST = Path(__file__).resolve().parent / "dist"


def build() -> Path:
    """Build a pure-Python wheel excluding native extensions."""
    DIST.mkdir(exist_ok=True)
    subprocess.check_call([
        sys.executable, "-m", "build", str(SRC),
        "--wheel", "--no-isolation",
        "--outdir", str(DIST),
    ])
    wheels = list(DIST.glob("yuho-*.whl"))
    if not wheels:
        raise RuntimeError("No wheel produced")
    return wheels[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Yuho for Pyodide")
    parser.add_argument("--install", action="store_true", help="Print micropip install snippet")
    args = parser.parse_args()
    whl = build()
    print(f"Built: {whl}")
    if args.install:
        print(f"\nIn Pyodide:\n  import micropip\n  await micropip.install('{whl.name}')")


if __name__ == "__main__":
    main()
