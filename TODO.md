# Yuho TODO

Strict [todo.txt v1](https://github.com/todotxt/todo.txt) syntax inside the code fence below.
Priorities: (A) blocker/out-of-box-broken/cheap, (B) targeted engineering or docs.
Projects: +ci +packaging +docs +lsp +parser +tests +archive.
Contexts: @workflows @pyproject @cli @transpile @lsp @parser @upgrade @docs @tests @archive.

Each item carries the exact paths needed for an independent agent to execute it without re-running the source audit. Audit reference: see git log around 2026-06-22 and docs/retrospective.md for the post-scope-reduction baseline this list patches against.

```todo
(B) 2026-06-22 Surface ModuleResolutionError as LSP diagnostic in src/yuho/lsp/server.py:310-326 (`resolved_dependency_modules`) — replace `except ModuleResolutionError: continue` blocks with collection of the failing import_node/reference with its source location; add a new diagnostic emission path that yields LSP Warning severity at the import/reference span; extend tests/test_lsp_server.py with a fixture having an unresolvable import and assert the diagnostic appears +lsp @lsp effort:M
(B) 2026-06-22 Add bounds check in src/yuho/parser/wrapper.py `_edited_tree()` (~L244-264): before calling `old_tree.edit(...)`, validate `0 <= start_byte <= old_end_byte <= len(old_source)` and `start_byte <= new_end_byte <= len(new_source)`; on violation, log at DEBUG level and return None so the caller falls back to `parse_source()` full reparse; add a test in tests/test_parser_incremental.py exercising the fallback path with deliberately malformed edits +parser @parser effort:S
(B) 2026-06-22 Extend tests/test_grammar_pragma_upgrade.py with two cases: (1) `.yh` source with no `#yuho` pragma at all — assert upgrade either applies default-version migration or raises a clear error message naming the expected pragma; (2) source declaring an obsolete version that skips multiple targets (e.g., `#yuho v4.0` upgrading toward `v5.1`) — assert the rewriter either chains migrations or errors with the missing-step name +tests @upgrade effort:S
(B) 2026-06-22 Create docs/researcher/archive/ subdirectory and move phase-c-gaps.md, phase-d-flag-fix-prompt.md, phase-d-l3-review-prompt.md, phase-d-reencoding-prompt.md into it; update docs/retrospective.md cross-refs (search for `phase-c-gaps`, `phase-d-`) and docs/INDEX.md to add an "Archive" subsection under researcher pointing to the new dir; preserve git history with `git mv` +archive @docs effort:S
```
