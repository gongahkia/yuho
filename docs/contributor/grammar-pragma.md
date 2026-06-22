# Grammar Pragma

Yuho source can declare the intended grammar version on the first line:

```yuho
#yuho v5.1
```

The pragma must be the first line. The parser recognizes the line with
`GRAMMAR_PRAGMA_RE` in `src/yuho/parser/wrapper.py`.

## Parser behavior

Supported versions are defined in `SUPPORTED_GRAMMAR_VERSIONS`. The
current version is `CURRENT_GRAMMAR_VERSION`, currently `5.1`.

Parse behavior:

- No pragma: parse normally and leave `ParseResult.grammar_version` as
  `None`.
- `#yuho v5.1` or `#yuho v5.1.0`: parse normally and set
  `ParseResult.grammar_version`.
- Invalid pragma syntax: emit a `GRAMMAR_PRAGMA` parse error on line 1.
- Unsupported version, such as `#yuho v4.0`: emit a `GRAMMAR_PRAGMA`
  parse error telling the user to run `yuho upgrade`.

Before tree-sitter sees the file, `_normalize_grammar_pragma()` rewrites
the pragma prefix into a comment-shaped line so the grammar does not need
a dedicated top-level pragma production.

## Upgrade command

`yuho upgrade` is implemented in `src/yuho/cli/commands/upgrade.py`.

Current behavior is intentionally narrow:

- Insert `#yuho v5.1` when the file has no pragma.
- Replace an existing first-line `#yuho v...` pragma with the target
  version.
- Honor `--from` only as a guard when a file already declares a version.
- Support `--check` and `--in-place`.

It does not currently perform AST-aware syntax migrations between old
grammar families. If future grammar changes need source rewrites, add
explicit migration steps and tests before broadening the command text.

## Tests

Examples live in `tests/test_grammar_pragma_upgrade.py`. They cover:

- accepted top-level `#yuho v5.1`;
- rejected unsupported versions;
- inserting a current pragma;
- replacing an existing pragma;
- CLI `--check` and `--in-place` behavior.
