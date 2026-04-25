"""``yuho recommend`` — surface candidate Penal Code sections for a fact pattern.

Reads a YAML/JSON fact pattern (same shape as ``simulator/`` fixtures, but
without the ``section`` field), runs the ChargeRecommender over the
encoded corpus, and prints the top-k structurally fitting sections with
the simulator's per-element trace attached.

Every output carries the ``LEGAL_DISCLAIMER`` and ``not_legal_advice``
flag — surfacing the disclaimer is a hard contract, not a polite hint.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any, Dict

import click


def _load_facts(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise click.ClickException(f"facts file not found: {path}")
    raw = p.read_text(encoding="utf-8")
    if raw.lstrip().startswith("{") or path.endswith(".json"):
        return _json.loads(raw)
    # Reuse the simulator's mini-YAML parser to avoid a hard PyYAML dep.
    sim_dir = Path(__file__).resolve().parents[4] / "simulator"
    if str(sim_dir) not in sys.path:
        sys.path.insert(0, str(sim_dir))
    try:
        import simulator as sim_mod  # type: ignore
    except Exception:
        try:
            import yaml  # type: ignore
            return yaml.safe_load(raw)
        except Exception:
            raise click.ClickException(
                "could not parse YAML; install PyYAML or use a JSON fact file"
            )
    return sim_mod._load_yaml_or_json(p)


def run_recommend(
    facts_path: str,
    *,
    top_k: int = 5,
    max_candidates: int = 60,
    min_coverage: float = 0.0,
    json_output: bool = False,
) -> None:
    facts = _load_facts(facts_path)
    from yuho.recommend.charge_recommender import (
        ChargeRecommender, render_recommendation_text,
    )
    rec = ChargeRecommender().recommend(
        facts,
        top_k=top_k,
        max_candidates=max_candidates,
        min_coverage=min_coverage,
    )
    if json_output:
        click.echo(_json.dumps(rec.to_dict(), indent=2, ensure_ascii=False))
    else:
        click.echo(render_recommendation_text(rec))
    sys.exit(0)
