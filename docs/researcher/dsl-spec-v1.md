# Yuho DSL Spec v1

This file defines the executable Yuho DSL conformance surface for v1. The
machine-readable fixture is `tests/fixtures/conformance/dsl_spec_v1.json`; run
`make verify-dsl-spec` before changing parser, AST, semantic, or JSON output
behavior.

## Normative Rules

| ID | Contract |
| --- | --- |
| YH-LEX-001 | Comments and doc comments are accepted as trivia without invalidating enclosing declarations. |
| YH-STATUTE-001 | A statute has a section number, title, and element block that builds a `StatuteNode`. |
| YH-ELEMENT-001 | Element burden and proof-standard metadata parse and survive AST construction. |
| YH-GROUP-001 | Nested `all_of` and `any_of` groups preserve conjunctive/disjunctive structure. |
| YH-EXCEPTION-001 | Exception blocks preserve condition/effect text and optional labels. |
| YH-CASELAW-001 | Case-law blocks preserve targeted holding metadata and doc-comment annotations. |
| YH-CROSS-001 | `is_infringed` and `apply_scope` cross-section predicates type-check when the target exists. |
| YH-TYPE-NEG-001 | Returning a string from an `int` function is a semantic error. |
| YH-PARSE-NEG-001 | An unclosed statute block is a parse error. |

## Versioning

- `spec_version` is `1.0.0`.
- Compatible additions append new rule IDs and fixtures.
- Incompatible changes require a new spec file and fixture version.
- JSON output fixtures must emit the current AST JSON schema version.
