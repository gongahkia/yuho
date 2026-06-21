from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from yuho.services.analysis import analyze_file
from yuho.transpile.akomantoso_transpiler import AkomaNtosoTranspiler
from yuho.transpile.alloy_transpiler import AlloyTranspiler
from yuho.transpile.english_transpiler import EnglishTranspiler
from yuho.transpile.json_transpiler import JSONTranspiler
from yuho.transpile.latex_transpiler import LaTeXTranspiler
from yuho.transpile.legalruleml_transpiler import LegalRuleMLTranspiler
from yuho.transpile.mermaid_mindmap_transpiler import MermaidMindmapTranspiler
from yuho.transpile.mermaid_transpiler import MermaidTranspiler


REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "library" / "penal_code"
SNAPSHOT = Path(__file__).resolve().parent / "snapshots" / "transpile_matrix.json"
ACCEPT_ENV = "YUHO_ACCEPT_SNAPSHOTS"

TARGETS = {
    "json": lambda: JSONTranspiler(include_locations=False),
    "english": EnglishTranspiler,
    "latex": LaTeXTranspiler,
    "mermaid": MermaidTranspiler,
    "mindmap": MermaidMindmapTranspiler,
    "alloy": AlloyTranspiler,
    "akomantoso": AkomaNtosoTranspiler,
    "legalruleml": LegalRuleMLTranspiler,
}


def test_penal_code_transpiler_snapshot_matrix():
    current = _build_matrix()
    if os.environ.get(ACCEPT_ENV) == "1":
        _write_snapshot(current)
        return
    if not SNAPSHOT.exists():
        raise AssertionError(f"missing snapshot; run {ACCEPT_ENV}=1 pytest {__file__}")
    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if current != expected:
        raise AssertionError(
            "transpile snapshot matrix changed; " f"run {ACCEPT_ENV}=1 pytest {__file__} to accept"
        )


def _build_matrix() -> dict:
    statute_paths = sorted(LIBRARY.glob("*/statute.yh"))
    snapshots: dict[str, dict[str, dict[str, int | str]]] = {}
    for statute_path in statute_paths:
        analysis = analyze_file(statute_path, run_semantic=False)
        if not analysis.is_valid or analysis.ast is None:
            raise AssertionError(f"invalid statute fixture: {statute_path}")
        rel = statute_path.relative_to(REPO).as_posix()
        snapshots[rel] = {}
        for target, factory in TARGETS.items():
            output = factory().transpile(analysis.ast).output
            snapshots[rel][target] = _fingerprint(output)
    return {
        "version": 1,
        "statute_count": len(statute_paths),
        "targets": list(TARGETS),
        "snapshots": snapshots,
    }


def _fingerprint(output: str) -> dict[str, int | str]:
    encoded = output.encode("utf-8")
    return {
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bytes": len(encoded),
        "lines": output.count("\n") + (0 if output.endswith("\n") or not output else 1),
    }


def _write_snapshot(payload: dict) -> None:
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
