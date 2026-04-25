# Cookbook: Contract Analysis

Map contract clauses to statutory elements for gap analysis.

## Approach

1. Model the relevant statutes in `.yh` format
2. Transpile to JSON to get structured element lists
3. Match contract text against element descriptions
4. Report coverage gaps

## Example

```python
from yuho.services.analysis import analyze_file
from yuho.transpile.registry import TranspilerRegistry
from yuho.transpile.base import TranspileTarget
import json

# parse the statute
result = analyze_file("library/penal_code/s378_theft/statute.yh")
transpiler = TranspilerRegistry.instance().get(TranspileTarget.JSON)
structured = json.loads(transpiler.transpile(result.ast))

# extract required elements
elements = []
for statute in structured.get("statutes", []):
    for elem in statute.get("elements", []):
        elements.append({
            "type": elem["element_type"],
            "name": elem["name"],
            "description": elem["description"],
        })

# compare against contract clauses
for elem in elements:
    # your matching logic here
    print(f"  {elem['type']}: {elem['description']}")
```
