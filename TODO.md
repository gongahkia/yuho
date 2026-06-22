# Yuho TODO

Strict [todo.txt v1](https://github.com/todotxt/todo.txt) syntax inside the code fence below.
Priorities: (A) blocker/out-of-box-broken/cheap, (B) targeted engineering or docs.
Projects: +ci +packaging +docs +lsp +parser +tests +archive.
Contexts: @workflows @pyproject @cli @transpile @lsp @parser @upgrade @docs @tests @archive.

Each item carries the exact paths needed for an independent agent to execute it without re-running the source audit. Audit reference: see git log around 2026-06-22 and docs/retrospective.md for the post-scope-reduction baseline this list patches against.

```todo
(B) 2026-06-22 Create docs/researcher/archive/ subdirectory and move phase-c-gaps.md, phase-d-flag-fix-prompt.md, phase-d-l3-review-prompt.md, phase-d-reencoding-prompt.md into it; update docs/retrospective.md cross-refs (search for `phase-c-gaps`, `phase-d-`) and docs/INDEX.md to add an "Archive" subsection under researcher pointing to the new dir; preserve git history with `git mv` +archive @docs effort:S
```
