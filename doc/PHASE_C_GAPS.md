# Phase C — Expressiveness Gaps

Surfaced during bulk encoding of the Singapore Penal Code. Each gap is a
concrete input to Phase D (AST/grammar refactor).

## G1 — element_group rejects preceding doc comments

`all_of { ... }` and `any_of { ... }` blocks cannot be preceded by a
`///` doc comment. Agents had to omit group-level rationale.

**Workaround:** attach doc comments only to `element_entry` siblings.

**Fix:** extend the grammar to allow `doc_comment*` before
`element_group`.

## G2 — colons break /// doc comments

A `:` anywhere inside a `///` doc comment causes a parse error.

**Workaround:** use `--` (em-dash) or commas instead.

**Fix:** lex `///` as opaque-until-EOL, or escape `:` inside doc
comments explicitly.

## G3 — section_number token only accepts single trailing letter

Grammar rule `section_number = \d+[A-Z]?` rejects multi-letter suffixes
like `376AA`, `377BA..377BO`, `377CA`, `377CB`. Affected ~25 real PC
sections.

**Workaround:** encode as `statute <num>.<n> "<title>"` with
`/// @section <original>` doc comment for traceability.

**Fix:** change token to `\d+[A-Z]*`. Also audit downstream consumers
(LSP, transpilers, CLI) that may assume single-letter suffix.

## Further findings to add as you review

- (blank for now; add as you find them during L3 review)
