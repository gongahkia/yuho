# Error Codes

## Analysis Stages

Returned in validation and check results under `error.stage`:

| Stage | Description | Common causes |
|---|---|---|
| `parse` | tree-sitter parse failure | Syntax errors, unclosed braces, invalid tokens |
| `ast` | AST construction failure | Unsupported or malformed parse tree nodes |
| `scope` | Scope analysis failure | Undefined variables, duplicate declarations |
| `type` | Type checking failure | Type mismatches, unknown type names |
| `lint` | Lint rule violation | Naming, fidelity, or structural issues |
| `transpile` | Transpilation failure | Unsupported AST pattern for a target |

## CLI Exit Codes

See [CLI exit codes](cli-exit-codes.md).
