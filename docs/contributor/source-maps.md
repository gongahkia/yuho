# Source Maps

Every built-in transpiler returns a `TranspileResult` through
`TranspilerBase.result()` in `src/yuho/transpile/base.py`. When the
transpiler passes `source_ast`, that helper calls `build_source_map()` in
`src/yuho/transpile/source_map.py` and attaches a Source Map V3-shaped
payload to `TranspileResult.source_map`.

## Sidecar files

The CLI writes a sidecar only when output is written to a file. For an
output path `<output>`, the sidecar path is `<output>.map`.

Examples:

```text
out/s415.json
out/s415.json.map
out/s415.als
out/s415.als.map
```

The CLI sets the map `file` field to the output file name before writing
the sidecar.

## Format

The payload follows Source Map V3 field names and adds Yuho spans:

| Field | Meaning |
|---|---|
| `version` | Always `3`. |
| `file` | Generated output file name. Empty in memory until the CLI writes a sidecar. |
| `sourceRoot` | Empty string. |
| `sources` | Source `.yh` file paths found in AST source locations. |
| `names` | Node names used in mappings. |
| `mappings` | VLQ-encoded generated-to-source mapping string. |
| `x_yuho_spans` | Yuho extension with generated and original span objects per mapped AST node. |

Each `x_yuho_spans` entry includes:

- `name`, `node`, and AST `path`.
- `generated` line, column, end line, end column, offset, and end offset.
- `original` zero-based source coordinates.
- `source_location` with the original one-based Yuho location.

## Programmatic use

Use the result object directly when embedding Yuho:

```python
from yuho.transpile import TranspileTarget, get_transpiler

result = get_transpiler(TranspileTarget.JSON).transpile(ast)
source_map = result.source_map
payload = result.to_dict()
```

`result.source_map` is `None` only if a transpiler constructs a result
without source-map metadata. Built-in transpilers currently pass the AST
through `TranspilerBase.result()`.
