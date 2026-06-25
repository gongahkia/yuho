"""Summarize backend parity coverage and unsupported feature boundaries."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yuho.cli.commands.verify import BACKEND_METADATA


PARITY_CLAIMS_REL = Path("tests/fixtures/backend_parity/claims.json")
PARITY_CLAIMS = REPO / PARITY_CLAIMS_REL


def load_claims(path: Path = PARITY_CLAIMS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary() -> str:
    claims = load_claims()
    lines = ["=== backend parity ==="]
    for link in claims["parity_links"]:
        lines.append(f"{link['name']}: {link['evidence']}")
    lines.append("")
    lines.append("Feature coverage:")
    for row in claims["feature_coverage"]:
        lines.append(f"- {row['feature']}: {row['status']}")
    lines.append("")
    lines.append("Unsupported feature boundaries:")
    for backend in ("alloy", "z3", "lean", "combined"):
        metadata = BACKEND_METADATA[backend]
        unsupported = ", ".join(metadata["unsupported_features"])
        lines.append(f"- {backend} ({metadata['status']}): {unsupported}")
    lines.append(
        "Backend parity: runtime-z3=runtime-tests; penalty-verdicts=z3-model; "
        "z3-lean=structural-diff; "
        "lean-verdicts=expected-verdicts; lean-penalty-footprints=z3-footprint; "
        "alloy=explicit-unsupported"
    )
    return "\n".join(lines)


def main() -> int:
    print(build_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
