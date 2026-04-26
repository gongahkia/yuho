# Cookbook: Compliance SaaS

Build a compliance checker that validates fact patterns against encoded
statutes. The recipe end-to-end: ingest a statute, evaluate user-supplied
facts, return a structured pass/fail report with the satisfied and
unsatisfied elements named so the consumer can act on them.

## Why Yuho fits this shape

`yuho.services.analysis.analyze_file` parses a `.yh` source and yields
an AST with elements, exceptions, and penalty already structured. The
:class:`StatuteEvaluator` then reduces (statute, facts) to a binding
map — which is exactly what a compliance back-end needs to surface to a
caller.

## End-to-end skeleton

```python
from pathlib import Path

from yuho.services.analysis import analyze_file
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator


def evaluate_compliance(statute_path: str, facts: dict[str, bool]) -> dict:
    """Return {overall_satisfied, bindings, missing_elements} for a fact pattern."""
    result = analyze_file(Path(statute_path), run_semantic=False)
    if result.ast is None or not result.ast.statutes:
        raise ValueError(f"no statute parsed from {statute_path}")
    statute = result.ast.statutes[0]

    fact_struct = StructInstance(
        type_name="Facts",
        fields={k: Value(raw=v, type_tag="bool") for k, v in facts.items()},
    )

    eval_result = StatuteEvaluator().evaluate(statute, fact_struct)
    bindings = eval_result.bindings()
    missing = [name for name, sat in bindings.items() if not sat]
    return {
        "section": statute.section_number,
        "overall_satisfied": eval_result.overall_satisfied,
        "bindings": bindings,
        "missing_elements": missing,
    }


if __name__ == "__main__":
    print(evaluate_compliance(
        "library/penal_code/s378_theft/statute.yh",
        {"taking": True, "movable_property": True, "without_consent": False},
    ))
```

The output reports `overall_satisfied=False` plus the named element
(`without_consent`) that broke the chain — actionable, not opaque.

## Wiring into a web service

Wrap the function above in any framework. With FastAPI:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class CheckRequest(BaseModel):
    statute_path: str
    facts: dict[str, bool]


@app.post("/v1/check")
def check(req: CheckRequest):
    try:
        return evaluate_compliance(req.statute_path, req.facts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
```

Run with `uvicorn app:app --port 8080`. POST a JSON body, get
`{section, overall_satisfied, bindings, missing_elements}` back.

## CI integration: pin encoded statutes

The `yuho check` CLI is the right gate before any deploy:

```yaml
# .github/workflows/yuho-check.yml
- run: pip install -e .[verify]
- run: yuho check statutes/*.yh
- run: yuho lint  statutes/*.yh
- run: yuho ci-report --json > coverage.json
```

`yuho ci-report --json` returns a per-section pass/fail row; surface
that as a build artefact so a regression in fidelity blocks the
deploy.

## Pulling structural metadata for dashboards

For tagging or admin UIs, the JSON transpiler is the canonical
machine-readable form:

```python
from yuho.transpile import TranspileTarget, get_transpiler

transpiler = get_transpiler(TranspileTarget.JSON)
print(transpiler.transpile(result.ast))
```

The shape includes `definitions`, `elements` (with their
`element_type` ∈ {actus_reus, mens_rea, circumstance}), `penalty`,
`exceptions` (with priority), and `case_law`. Schema is locked by
`yuho schema` and pinned in `tests/test_json_transpiler.py`.

## Performance notes

`analyze_file` parses each call. For a hot path, cache the AST per
statute path + mtime; re-parse only when the source changes. The
evaluator itself is memoryless and cheap (~µs per fact pattern).

## See also

- `yuho recommend simulator/fixtures/<scenario>.yaml` — ranks
  Penal Code sections by structural fit for a given fact pattern.
- `yuho explore <statute.yh> <section>` — enumerates satisfying /
  borderline scenarios; useful when a customer asks "what would
  trip s415 here?"
- `docs/researcher/syntax.md` — the Yuho grammar reference.
