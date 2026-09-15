"""Check links and basic structure in active kernel-fragment documentation."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS = [
    ROOT / "docs/rewrite/TYPED-BOOLEAN-FACTS-V1.md",
    ROOT / "docs/rewrite/GUARDED-PENALTY-SELECTION-V1.md",
    ROOT / "docs/rewrite/PENALTY-TERMS-V1.md",
    ROOT / "docs/rewrite/SUPPLIED-PROOF-STATUS-V1.md",
    ROOT / "docs/rewrite/REGISTERED-PRESUMPTION-DERIVATIONS-V1.md",
    ROOT / "docs/rewrite/MODEL-BUNDLE-V1.md",
    ROOT / "docs/rewrite/MODEL-BUNDLE-CHANGE-IMPACT-PROVISIONAL-SPEC.md",
    ROOT / "docs/rewrite/LEGAL-SOURCE-REGISTRATION-DECISION-REPORT.md",
    ROOT / "docs/rewrite/MODEL-SCOPE-AND-PROVENANCE-THREAT-MODEL.md",
    ROOT / "docs/rewrite/YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md",
    ROOT / "docs/rewrite/YUHO-REWRITE-DECISION-REPORT.md",
    ROOT / "docs/rewrite/MIGRATION-CONTRACT.md",
    ROOT / "docs/rewrite/HASKELL-YUHO-DSL-GUIDE.md",
    ROOT / "research/singapore/CORPUS-INDEX.md",
    ROOT / "research/singapore/offence-corpus-pilot/README.md",
    ROOT / "rewrite/haskell/README.md",
    ROOT / "rewrite/haskell/schema/README.md",
    ROOT / "rewrite/haskell/TEST-RESULTS.md",
]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> None:
    count = 0
    for document in DOCUMENTS:
        content = document.read_text(encoding="utf-8")
        assert content.startswith("# "), document
        for target in LINK.findall(content):
            if "://" in target or target.startswith("#"):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            assert (document.parent / path).exists(), (document, target)
            count += 1
    print(f"kernel documentation: {len(DOCUMENTS)} structured files, "
          f"{count} relative links resolve")


if __name__ == "__main__":
    main()
