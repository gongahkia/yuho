"""Summarize backend parity coverage and unsupported feature boundaries."""

from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yuho.cli.commands.verify import BACKEND_METADATA


PARITY_LINKS = (
    ("runtime-z3", "scripts/verify_runtime_tests.py"),
    ("z3-lean", "scripts/verify_structural_diff.py"),
    ("alloy", "explicit unsupported-feature failures"),
)


def build_summary() -> str:
    lines = ["=== backend parity ==="]
    for name, evidence in PARITY_LINKS:
        lines.append(f"{name}: {evidence}")
    lines.append("")
    lines.append("Unsupported feature boundaries:")
    for backend in ("alloy", "z3", "lean", "combined"):
        metadata = BACKEND_METADATA[backend]
        unsupported = ", ".join(metadata["unsupported_features"])
        lines.append(f"- {backend} ({metadata['status']}): {unsupported}")
    lines.append(
        "Backend parity: runtime-z3=runtime-tests; z3-lean=structural-diff; "
        "alloy=explicit-unsupported"
    )
    return "\n".join(lines)


def main() -> int:
    print(build_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
