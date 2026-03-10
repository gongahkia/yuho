"""
Mermaid renderer - convert Mermaid text to SVG/PNG via mmdc (mermaid-cli).

Requires @mermaid-js/mermaid-cli (npx mmdc) to be available on PATH.
Falls back to a helpful error if mmdc is not installed.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def render_mermaid(
    mermaid_text: str,
    output_path: str,
    *,
    output_format: str = "svg",
    width: int = 1200,
    height: int = 800,
    theme: str = "default",
    background: str = "white",
) -> str:
    """
    Render Mermaid diagram text to SVG or PNG.

    Args:
        mermaid_text: Raw Mermaid diagram source.
        output_path: Destination file path.
        output_format: "svg" or "png".
        width: Pixel width (PNG only).
        height: Pixel height (PNG only).
        theme: Mermaid theme (default, dark, forest, neutral).
        background: Background color.

    Returns:
        The output_path on success.

    Raises:
        RuntimeError: If mmdc is not installed or rendering fails.
    """
    mmdc = _find_mmdc()
    if not mmdc:
        raise RuntimeError(
            "mermaid-cli (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli"
        )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as tmp:
        tmp.write(mermaid_text)
        tmp_path = tmp.name
    try:
        cmd = [
            mmdc,
            "-i", tmp_path,
            "-o", output_path,
            "-t", theme,
            "-b", background,
        ]
        if output_format == "png":
            cmd.extend(["-w", str(width), "-H", str(height)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"mmdc failed: {result.stderr.strip()}")
        return output_path
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _find_mmdc() -> Optional[str]:
    """Find mmdc executable on PATH or via npx."""
    mmdc = shutil.which("mmdc")
    if mmdc:
        return mmdc
    npx = shutil.which("npx")
    if npx:
        try:
            result = subprocess.run(
                [npx, "--yes", "mmdc", "--version"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return f"{npx} --yes mmdc"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return None


def is_mmdc_available() -> bool:
    """Check if mmdc is available for rendering."""
    return _find_mmdc() is not None
