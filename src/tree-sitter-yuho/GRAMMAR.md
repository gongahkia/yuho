# Yuho Grammar Development Guide

## Overview

Yuho uses [tree-sitter](https://tree-sitter.github.io/) for parsing. The grammar is defined in `grammar.js` and compiled to C (`src/parser.c`).

## Regenerating the Parser

After any change to `grammar.js`:

```bash
cd src/tree-sitter-yuho
npx tree-sitter generate
```

This produces:
- `src/parser.c` -- the C parser
- `src/tree_sitter/parser.h` -- header
- `src/node-types.json` -- node type metadata

## Testing Grammar Changes

```bash
# parse a sample file
npx tree-sitter parse ../../library/penal_code/s415_cheating/statute.yh

# run tree-sitter's built-in test corpus
npx tree-sitter test
```

Then verify end-to-end:

```bash
yuho check library/penal_code/s415_cheating/statute.yh
```

## Key Grammar Concepts

| Concept | Grammar rule | Example |
|:--------|:------------|:--------|
| Statute block | `statute_block` | `statute 415 "Cheating" { ... }` |
| Element | `element_entry` | `actus_reus taking := "..."` |
| Element group | `element_group` | `all_of { ... }` |
| Match expression | `match_expression` | `match { case ... }` |
| Struct definition | `struct_definition` | `struct Foo { ... }` |
| Function definition | `function_definition` | `fn name(...) : type { ... }` |
| Doc comment | `doc_comment` | `/// This is documented` |
| Comment | `comment` | `// regular comment` |

## Precedence Rules

- `doc_comment` has precedence 1, `comment` has -1, ensuring `///` is always parsed as a doc-comment rather than a regular comment.
- `prec.left` / `prec.right` on binary operators follows standard mathematical precedence (multiplicative > additive > comparison > logical).

## Connecting Grammar to AST

After regenerating:

1. Check `src/yuho/ast/builder.py` -- this converts tree-sitter CST nodes to Yuho AST nodes.
2. For new node types, add a `_build_<node_type>` method in `ASTBuilder`.
3. For new AST nodes, add the dataclass to `src/yuho/ast/nodes.py` and update the `Visitor` class.

## Common Warnings

`tree-sitter generate` may emit conflict warnings for:
- `assignment_statement` / `expression_statement` -- benign, both start with an identifier.
- `match_arm` -- benign, resolved by tree-sitter's GLR.

These are pre-existing and do not affect correctness.
