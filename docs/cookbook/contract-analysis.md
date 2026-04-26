# Cookbook: Contract Analysis

Map contract clauses to statutory elements for gap analysis. The
recipe: encode the relevant statute as a Yuho `.yh` source, extract
the structured element list (`actus_reus` / `mens_rea` /
`circumstance`), match contract text against each element, and
report unsatisfied or unaddressed elements as gaps.

## Motivating shape

Where a static legal review reads a contract front-to-back and asks
"is everything covered?", the structured form lets you pivot: take
each statutory element, ask whether the contract addresses it, and
flag gaps. Yuho's encoded library gives you that element-level shape
for the entire Singapore Penal Code; bring your own contract corpus.

## Extract the element list

```python
import json
from pathlib import Path

from yuho.services.analysis import analyze_file
from yuho.transpile import TranspileTarget, get_transpiler


def statute_elements(yh_path: Path) -> list[dict]:
    """Return [{type, name, description}, …] for a statute file."""
    result = analyze_file(yh_path, run_semantic=False)
    if result.ast is None:
        raise ValueError(f"parse failed: {result.parse_errors}")
    transpiler = get_transpiler(TranspileTarget.JSON)
    structured = json.loads(transpiler.transpile(result.ast))
    out = []
    for st in structured.get("statutes", []):
        for el in st.get("elements", []):
            out.append({
                "section": st["section_number"],
                "type": el.get("element_type"),
                "name": el.get("name"),
                "description": el.get("description"),
            })
    return out


elements = statute_elements(Path("library/penal_code/s378_theft/statute.yh"))
for e in elements:
    print(f"  [{e['type']:13s}] {e['name']:25s}  {e['description']}")
```

The JSON shape is the canonical machine-readable form — see
`tests/test_json_transpiler.py` for the locked-down schema.

## Match contract text against elements

The simplest baseline is keyword overlap on the element description.
A stronger match uses sentence embeddings; the API stays the same:

```python
def coverage_report(elements: list[dict], contract_text: str) -> list[dict]:
    text = contract_text.lower()
    rows = []
    for el in elements:
        keywords = el["description"].lower().split()
        hits = sum(1 for k in keywords if k in text)
        rows.append({
            "name": el["name"],
            "type": el["type"],
            "covered": hits >= 2,  # crude — replace with embedding sim
            "evidence_count": hits,
        })
    return rows


report = coverage_report(elements, open("contract.txt").read())
gaps = [r for r in report if not r["covered"]]
print(f"{len(gaps)} unaddressed elements:")
for g in gaps:
    print(f"  - {g['type']} '{g['name']}'")
```

For production, swap the keyword baseline for sentence embeddings
(e.g. `sentence-transformers`) and threshold on cosine similarity.

## Fact-pattern check via the evaluator

If the contract carries explicit boolean assertions (`taking=True`,
`without_consent=False`), the evaluator gives you a single overall
yes/no plus per-element bindings:

```python
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator


facts = StructInstance(type_name="Facts", fields={
    "taking": Value(raw=True, type_tag="bool"),
    "movable_property": Value(raw=True, type_tag="bool"),
    "without_consent": Value(raw=False, type_tag="bool"),
})
result = StatuteEvaluator().evaluate(elements_module.statutes[0], facts)
print(result.overall_satisfied, result.bindings())
```

This is the same path the **Compliance SaaS** cookbook uses; the
distinction is contract analysis treats elements as a *checklist*
rather than a runtime predicate.

## Surfacing exceptions

The contract may include a clause that fits a Penal Code exception
(e.g. private defence). Pull exceptions out of the structured JSON
by the same path:

```python
for st in structured["statutes"]:
    for exc in st.get("exceptions", []):
        print(f"  exception '{exc['label']}' (priority={exc.get('priority')})")
```

Then you can match contract clauses against named exceptions, not
just against required elements.

## See also

- `yuho explore <statute.yh> <section>` — enumerates the structural
  shapes the section accepts; useful for spotting "what would
  satisfy this from the contract side?"
- `yuho recommend simulator/fixtures/<scenario>.yaml` — ranks
  candidate sections by structural fit.
- `docs/cookbook/legal-ai-assistant.md` — combines the above with
  an LLM front-end via the MCP server.
