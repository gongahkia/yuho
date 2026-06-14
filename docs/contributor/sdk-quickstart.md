# SDK Quickstart

Yuho currently ships a Python package, CLI, LSP, and MCP server. It does
not ship TypeScript, Go, Java, REST, or GraphQL SDKs.

## Python

```python
from yuho.services.analysis import analyze_source
from yuho.transpile import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry

source = 'statute 1 "Test" { elements { actus_reus act := "Did something"; } }'
result = analyze_source(source)

transpiler = TranspilerRegistry.instance().get(TranspileTarget.ENGLISH)
print(transpiler.transpile(result.ast))
```

For automation outside Python, call the CLI:

```bash
yuho check statute.yh
yuho transpile -t json statute.yh
yuho refs --scc --json
```

For AI-client integration, use the MCP server:

```bash
yuho serve --stdio
```
