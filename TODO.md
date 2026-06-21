# Yuho TODO

Strict [todo.txt v1](https://github.com/todotxt/todo.txt) syntax inside the code fence below.
Priorities: (A) cheap/blocker, (B) medium, (C) large/experimental.
Projects: +language +tooling +corpus +housekeeping +education +jurisdiction +positioning +compiler.
Contexts: @grammar @ast @lint @lean @verify @transpile @cli @lsp @resolver @library @repo @memory @typecheck @docs @scrape @viz @parser @analysis @interpreter @tests.

```todo
(A) 2026-06-21 Update MEMORY.md key paths after fossil deletion +housekeeping @memory effort:XS
(A) 2026-06-21 Wire eval/debugger.py to new `yuho debug --break-on element FACTS.yh STATUTE.yh` CLI subcommand +compiler @cli effort:M
(A) 2026-06-21 Tighten src/tree-sitter-yuho/grammar.js conflicts list: replace explicit conflicts entries with prec.left/prec.right/prec.dynamic where possible +compiler @grammar effort:M
(B) 2026-06-21 Incremental reparse via tree-sitter Tree.edit() in parser/wrapper.py to support per-keystroke LSP reparse +compiler @parser effort:M
(B) 2026-06-21 Query-based incremental compilation keyed on (file_hash, stage) memoising parse + AST + analysis between yuho invocations +compiler @analysis effort:L
(B) 2026-06-21 Extend TranspilerBase contract: return TranspileResult(output, warnings, manifest) instead of bare str; update all 8 transpilers +compiler @transpile effort:M
(B) 2026-06-21 Per-transpiler conformance matrix: golden snapshots for 524 statutes × 8 transpilers under tests/snapshots/ with insta-style accept/reject +compiler @tests effort:L
(B) 2026-06-21 Atheris fuzz harness on Parser.parse + ASTBuilder.build to surface crashes on malformed input +compiler @parser effort:M
(B) 2026-06-21 Z3 ↔ Alloy differential test in verify/combined.py logging per-fixture disagreements as machine-readable JSON +compiler @verify effort:M
(B) 2026-06-21 Source-map provenance in transpilers: JSON sidecar mapping output spans to AST source_locations (V3 source-map shape) +compiler @transpile effort:L
(C) 2026-06-21 Watch mode `yuho check --watch FILE` re-running on .yh file change via watchdog +compiler @cli effort:S
(C) 2026-06-21 Grammar version pragma `#yuho v5.1` at top of .yh files + `yuho upgrade` mechanical rewriter between grammar versions +compiler @grammar effort:L
```
