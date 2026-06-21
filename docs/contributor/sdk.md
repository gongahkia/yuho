# Yuho Python SDK

Use Yuho programmatically from Python for parsing, analysis,
transpilation, verification, and corpus graph checks.

## Installation

```bash
pip install yuho
```

For repository work:

```bash
uv pip install -e '.[dev]'
```

## Quick Start

```python
from yuho.services.analysis import analyze_file, analyze_source
from yuho.transpile import TranspileTarget, get_transpiler

source = 'statute 1 "Test" { elements { actus_reus act := "doing"; } }'
result = analyze_source(source)

assert result.is_valid
assert result.ast is not None

english = get_transpiler(TranspileTarget.ENGLISH)
print(english.transpile(result.ast))

file_result = analyze_file("library/penal_code/s415_cheating/statute.yh")
```

## Parsing And Analysis

```python
from yuho.services.analysis import analyze_file, analyze_source

result = analyze_source(source_code)
result.is_valid       # bool
result.ast            # ModuleNode or None
result.errors         # list[AnalysisError]
result.parse_errors   # parse-only diagnostics

result = analyze_file("statute.yh")
```

## AST Nodes

```python
from yuho.ast.nodes import (
    ModuleNode,
    StatuteNode,
    ElementNode,
    ElementGroupNode,
    PenaltyNode,
    DefinitionEntry,
    IllustrationNode,
    ExceptionNode,
    CaseLawNode,
)

for statute in result.ast.statutes:
    print(statute.section_number, statute.title.value if statute.title else "")
```

## Transpilation

```python
from yuho.transpile import TranspileTarget, get_transpiler

targets = [
    TranspileTarget.JSON,
    TranspileTarget.ENGLISH,
    TranspileTarget.MERMAID,
    TranspileTarget.MERMAID_MINDMAP,
    TranspileTarget.LATEX,
    TranspileTarget.ALLOY,
    TranspileTarget.DOCX,
    TranspileTarget.AKOMANTOSO,
]

transpiler = get_transpiler(TranspileTarget.MERMAID)
output = transpiler.transpile(ast)
transpiler.transpile_to_file(ast, "output.mmd")
```

## Reference Graphs

```python
from pathlib import Path
from yuho.library.reference_graph import build_reference_graph

graph = build_reference_graph(Path("library/penal_code"))
print(graph.outgoing("415"))
print(graph.find_sccs())
```

## Module Resolution

```python
from yuho.resolver import ModuleResolver

resolver = ModuleResolver(search_paths=["./library", "."])
module = resolver.resolve("penal_code/s415_cheating/statute")
```

## JSON Schema

```python
from yuho.transpile.json_schema import AST_SCHEMA_VERSION, generate_json_schema

schema = generate_json_schema()
print(AST_SCHEMA_VERSION)
```
