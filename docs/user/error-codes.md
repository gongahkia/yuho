# Error Codes

Yuho analysis diagnostics expose a stable `error_code` field. New analysis
codes use the `Y0001`-`Y9999` format; older snake_case labels are retained only
as documentation aliases.

## Analysis Stages

Returned in validation and check results under `error.stage`:

| Stage | Description | Common causes |
|---|---|---|
| `parse` | tree-sitter parse or input loading failure | Missing files, invalid syntax, oversized or binary input |
| `ast` | AST construction failure | Unsupported or malformed parse tree nodes |
| `scope` | Scope analysis failure | Undefined variables, duplicate declarations |
| `type` | Type checking failure | Type mismatches, unknown type names |
| `lint` | Lint rule violation or lint engine failure | Naming, fidelity, or structural issues |
| `semantic` | Scope/type/jurisdiction semantic issue | Unknown references, type errors, failed semantic pass |
| `transpile` | Transpilation failure | Unsupported AST pattern for a target |

## Code Index

| Code | Legacy alias | Stage | Meaning |
|---|---|---|---|
| [`Y0001`](#y0001-file-not-found) | `file_not_found` | `parse` | Input path does not exist |
| [`Y0002`](#y0002-not-a-file) | `not_a_file` | `parse` | Input path is not a regular file |
| [`Y0003`](#y0003-file-too-large) | `file_too_large` | `parse` | File exceeds the configured byte limit |
| [`Y0004`](#y0004-encoding-error) | `encoding_error` | `parse` | File cannot be decoded as the requested encoding |
| [`Y0005`](#y0005-file-read-failed) | `file_read_failed` | `parse` | OS-level file read failure |
| [`Y0006`](#y0006-null-bytes) | `null_bytes` | `parse` | Source contains null bytes |
| [`Y0007`](#y0007-source-too-large) | `source_too_large` | `parse` | Source string exceeds the configured character limit |
| [`Y0100`](#y0100-parse-error) | `parse_error` | `parse` | Generic parser diagnostic |
| [`Y0101`](#y0101-parse-missing-node) | `parse_missing_node` | `parse` | Parser inserted a missing node |
| [`Y0102`](#y0102-parse-unexpected-syntax) | `parse_unexpected_syntax` | `parse` | Parser found unexpected syntax |
| [`Y0199`](#y0199-parser-failed) | `parser_failed` | `parse` | Parser boundary raised unexpectedly |
| [`Y0200`](#y0200-ast-build-failed) | `ast_build_failed` | `ast` | AST builder boundary raised unexpectedly |
| [`Y0300`](#y0300-lint-analysis-failed) | `lint_analysis_failed` | `lint` | Lint pass raised unexpectedly |
| [`Y0400`](#y0400-semantic-issue) | `semantic_issue` | `semantic` | Scope, type, or jurisdiction semantic diagnostic |
| [`Y0499`](#y0499-semantic-analysis-failed) | `semantic_analysis_failed` | `semantic` | Semantic analysis boundary raised unexpectedly |

## Y0001 File Not Found

The path passed to `analyze_file` or a CLI command does not exist. Check the
path, current working directory, and any generated-file step that should have
created it.

## Y0002 Not A File

The input path exists but points to a directory, socket, device, or another
non-file object. Pass a `.yh` file path instead.

## Y0003 File Too Large

The file exceeds Yuho's configured maximum input size. Split the source or pass
a smaller generated artifact.

## Y0004 Encoding Error

The file cannot be decoded with the selected encoding, normally UTF-8. Re-save
the file as UTF-8 or call `analyze_file(..., encoding=...)` with the correct
encoding.

## Y0005 File Read Failed

The OS reported a read error after the path was accepted. Check permissions,
locks, transient filesystem failures, or removed files.

## Y0006 Null Bytes

The source contains `\x00`, which usually means a binary file was passed as
Yuho source. Regenerate or select the intended `.yh` file.

## Y0007 Source Too Large

The source string passed to `analyze_source` exceeds Yuho's configured character
limit. Use a file-level workflow or split the generated input.

## Y0100 Parse Error

The parser returned a generic syntax diagnostic. Inspect `line`, `column`,
`message`, and `node_type` for the exact location and expected shape.

## Y0101 Parse Missing Node

The parser recovered by inserting a missing node. This usually means a delimiter,
identifier, type, expression, or block was omitted before the reported position.

## Y0102 Parse Unexpected Syntax

The parser found a token sequence that does not fit the grammar. Check for
misordered clauses, invalid keywords, or syntax from another Yuho grammar
version.

## Y0199 Parser Failed

The parser boundary raised instead of returning structured diagnostics. Treat
this as a bug or hard input-boundary failure and preserve the source that
triggered it.

## Y0200 AST Build Failed

Parsing completed, but the AST builder could not construct Yuho nodes. This is
usually an unsupported parse-tree shape or a builder bug.

## Y0300 Lint Analysis Failed

The lint pass raised unexpectedly. Parse and AST phases succeeded; inspect the
message for the lint rule or structure that crashed.

## Y0400 Semantic Issue

Scope, type, or jurisdiction analysis reported a normal semantic diagnostic.
Use the diagnostic message and source location to fix the referenced symbol,
type, jurisdiction, or module relationship.

## Y0499 Semantic Analysis Failed

The semantic-analysis boundary raised instead of returning structured issues.
This is distinct from `Y0400`: it indicates the pass itself failed.

## CLI Exit Codes

See [CLI exit codes](cli-exit-codes.md).
