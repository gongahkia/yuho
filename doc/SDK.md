# Yuho Python SDK

Use Yuho programmatically in your Python applications.

## Installation

```bash
pip install yuho
```

## Quick Start

```python
from yuho.services.analysis import analyze_source, analyze_file
from yuho.transpile import TranspileTarget, get_transpiler

# Parse and analyze a string
result = analyze_source('statute 1 "Test" { elements { actus_reus act := "doing"; } }')
print(result.is_valid)       # True
print(len(result.ast.statutes))  # 1

# Parse a file
result = analyze_file("library/penal_code/s415_cheating/statute.yh")

# Transpile to English
english = get_transpiler(TranspileTarget.ENGLISH)
print(english.transpile(result.ast))

# Transpile to JSON
json_t = get_transpiler(TranspileTarget.JSON)
print(json_t.transpile(result.ast))
```

## Core API

### Parsing & Analysis

```python
from yuho.services.analysis import analyze_source, analyze_file

# analyze_source(source, file="<string>", run_semantic=True) -> AnalysisResult
result = analyze_source(source_code)
result.is_valid       # bool
result.ast            # ModuleNode or None
result.errors         # list of AnalysisError
result.parse_errors   # list of AnalysisError (parse-only)

# analyze_file(path, run_semantic=True) -> AnalysisResult
result = analyze_file("statute.yh")
```

### AST Nodes

```python
from yuho.ast.nodes import (
    ModuleNode,      # root: imports, type_defs, function_defs, statutes, variables
    StatuteNode,     # statute block
    ElementNode,     # actus_reus/mens_rea/circumstance
    PenaltyNode,     # imprisonment/fine/caning ranges
    DefinitionEntry, # term := "definition"
    IllustrationNode,# illustration examples
    ExceptionNode,   # exception/defence blocks
    CaseLawNode,     # case law references
)

for statute in result.ast.statutes:
    print(statute.section_number, statute.title.value)
    for elem in statute.elements:
        print(f"  {elem.element_type}: {elem.name}")
```

### Transpilation

```python
from yuho.transpile import TranspileTarget, get_transpiler

# Available targets
targets = [
    TranspileTarget.JSON,
    TranspileTarget.ENGLISH,
    TranspileTarget.MERMAID,
    TranspileTarget.LATEX,
    TranspileTarget.ALLOY,
    TranspileTarget.BIBTEX,
    TranspileTarget.COMPARATIVE,
    TranspileTarget.GRAPHQL,
    TranspileTarget.BLOCKS,
]

# Get transpiler and generate output
transpiler = get_transpiler(TranspileTarget.MERMAID)
output = transpiler.transpile(ast)

# Write to file
transpiler.transpile_to_file(ast, "output.mmd")
```

### Interpreter & Evaluation

```python
from yuho.eval.interpreter import Interpreter
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.eval.defeasible import DefeasibleReasoner

# Interpret a module
interp = Interpreter()
env = interp.interpret(ast)

# Evaluate a statute against facts
evaluator = StatuteEvaluator(interp)
result = evaluator.evaluate(statute, facts_struct, env)
print(result.satisfied)  # bool
print(result.summary())  # human-readable

# Defeasible reasoning with exceptions
reasoner = DefeasibleReasoner()
defeasible = reasoner.evaluate_with_exceptions(statute, facts_dict, env)
print(defeasible.final_verdict)  # "convicted" | "exception_applied" | "not_satisfied"
for step in defeasible.reasoning_chain:
    print(f"  {step.description}: {step.result}")
```

### Module Resolution

```python
from yuho.resolver import ModuleResolver

resolver = ModuleResolver(search_paths=["./library", "."])
module = resolver.resolve("penal_code/s415_cheating/statute")
```

### Custom Transpilers

```python
from yuho.transpile.base import TranspileTarget, TranspilerBase
from yuho.transpile.registry import TranspilerRegistry

class MyTranspiler(TranspilerBase):
    @property
    def target(self):
        return TranspileTarget.JSON  # or your custom target

    def transpile(self, ast):
        return "custom output"

# Register
registry = TranspilerRegistry.instance()
registry.register_instance(TranspileTarget.JSON, MyTranspiler())
```

## JSON Schema

Validate JSON transpiler output:

```python
from yuho.transpile.json_schema import generate_json_schema, AST_SCHEMA_VERSION

schema = generate_json_schema()  # returns JSON string
print(AST_SCHEMA_VERSION)  # "1.0.0"
```
