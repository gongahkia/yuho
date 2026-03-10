# Writing a Yuho Transpiler

Yuho's transpiler architecture is plugin-friendly. This guide walks through adding a new transpilation target.

## Architecture

```
TranspilerBase (ABC)        TranspileTarget (Enum)
     │                            │
     ├── JSONTranspiler           ├── JSON
     ├── EnglishTranspiler        ├── ENGLISH
     ├── MermaidTranspiler        ├── MERMAID
     ├── LaTeXTranspiler          ├── LATEX
     ├── AlloyTranspiler          ├── ALLOY
     ├── ...                      └── ...
     └── YourTranspiler           └── YOUR_TARGET
```

All transpilers are managed by the `TranspilerRegistry` singleton, which provides lazy instantiation and thread-safe access.

## Step-by-step

### 1. Add a target enum variant

In `src/yuho/transpile/base.py`:

```python
class TranspileTarget(Enum):
    ...
    YOUR_TARGET = auto()
```

Add string mappings in `from_string()` and a file extension in `file_extension`.

### 2. Implement the transpiler

Create `src/yuho/transpile/your_transpiler.py`:

```python
from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase

class YourTranspiler(TranspilerBase):
    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.YOUR_TARGET

    def transpile(self, ast: nodes.ModuleNode) -> str:
        # ast.statutes  -- list of StatuteNode
        # ast.type_defs -- list of StructDefNode
        # ast.function_defs -- list of FunctionDefNode
        # ast.variables -- list of VariableDecl
        lines = []
        for statute in ast.statutes:
            lines.append(f"Section {statute.section_number}")
            for elem in statute.elements:
                lines.append(f"  {elem.element_type}: {elem.name}")
        return "\n".join(lines)
```

Key AST nodes you'll likely traverse:

| Node | Description |
|:-----|:-----------|
| `ModuleNode` | Root: imports, type_defs, function_defs, statutes, variables |
| `StatuteNode` | A statute block with definitions, elements, penalty, exceptions, illustrations, caselaw |
| `ElementNode` | An element entry (actus_reus / mens_rea / circumstance) |
| `ElementGroupNode` | A combinator group (all_of / any_of) |
| `PenaltyNode` | Imprisonment/fine/caning ranges |
| `MatchExprNode` | A match expression with arms |
| `FunctionDefNode` | A function with params, return type, body |
| `StructDefNode` | A struct with typed fields |

### 3. Register the transpiler

In `src/yuho/transpile/registry.py`, add to `_register_builtins()`:

```python
from yuho.transpile.your_transpiler import YourTranspiler
self._registry[TranspileTarget.YOUR_TARGET] = YourTranspiler
```

### 4. Export from `__init__.py`

In `src/yuho/transpile/__init__.py`, add the import and `__all__` entry.

### 5. Add to CLI choices

In `src/yuho/cli/main.py`, add your target string to the transpile `--target` Choice list. Also update `src/yuho/cli/commands_registry.py` for the batch transpile command.

### 6. Test

```bash
yuho transpile library/penal_code/s415_cheating/statute.yh -t your_target
```

## Using the Visitor pattern

For complex transpilers, extend `Visitor` alongside `TranspilerBase`:

```python
from yuho.ast.visitor import Visitor

class YourTranspiler(TranspilerBase, Visitor):
    def transpile(self, ast: nodes.ModuleNode) -> str:
        ast.accept(self)
        return self._result

    def visit_statute(self, node: nodes.StatuteNode):
        ...

    def visit_element(self, node: nodes.ElementNode):
        ...
```

See `mermaid_transpiler.py` or `english_transpiler.py` for full examples.

## Advanced: factory registration

For transpilers needing constructor arguments:

```python
registry = TranspilerRegistry.instance()
registry.register_factory(
    TranspileTarget.YOUR_TARGET,
    lambda: YourTranspiler(option="value"),
)
```

Or register a pre-configured instance:

```python
registry.register_instance(
    TranspileTarget.YOUR_TARGET,
    YourTranspiler(option="value"),
)
```
