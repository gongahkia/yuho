# Yuho Memory

Current after fossil deletion: this repo is the local compiler, corpus, and verification toolchain. Do not look for old product/demo surfaces unless reading history.

## Key Paths

- `src/yuho/cli/main.py`: Click command registration.
- `src/yuho/cli/commands/`: CLI command implementations.
- `src/yuho/services/analysis.py`: shared parse, AST, semantic, lint, cache boundary.
- `src/yuho/parser/wrapper.py`: tree-sitter parser wrapper and parser-facing source validation.
- `src/yuho/ast/builder.py`: CST to AST builder.
- `src/yuho/ast/nodes.py`: frozen AST node definitions.
- `src/yuho/ast/statute_lint.py`: statute lint checks.
- `src/yuho/transpile/`: JSON, English, LaTeX/PDF, Mermaid, Alloy, DOCX, AKN, LegalRuleML emitters.
- `src/yuho/verify/`: Z3, Alloy, and combined verifier code.
- `src/yuho/eval/`: runtime interpreter and defeasible evaluation helpers.
- `src/yuho/library/`: reference graph and corpus graph lint helpers.
- `src/tree-sitter-yuho/grammar.js`: source tree-sitter grammar.
- `src/tree_sitter_yuho/`: packaged Python binding shim.
- `library/penal_code/`: canonical encoded Singapore Penal Code corpus.
- `library/bharatiya_nyaya_sanhita/`: BNS corpus.
- `library/indian_penal_code/`: IPC corpus/raw material.
- `library/malaysia_penal_code/`: Malaysia Penal Code corpus.
- `library/pakistan_penal_code/`: Pakistan Penal Code corpus.
- `mechanisation/`: Lean mechanisation and structural-diff fixtures.
- `scripts/`: corpus, scrape, round-trip, fuzz, and verification helpers.
- `tests/`: pytest suite; `tests/snapshots/` holds transpiler snapshot metadata.
- `docs/`: retained user, contributor, researcher, and positioning docs.
- `docs/user/lsp.md`: LSP install and editor setup.
- `docs/contributor/source-maps.md`: transpile source-map sidecar contract.
- `docs/contributor/grammar-pragma.md`: grammar pragma upgrade contract.
- `docs/contributor/conformance-matrix.md`: transpile snapshot matrix contract.
- `docs/researcher/archive/`: archived phase prompt/research notes.
- `Makefile`: retained verification gates, especially `make verify-core`.

## Removed Fossils

- Browser/Word/explorer editor surfaces are deleted.
- Generated static site output is deleted.
- Old Racket, Go, ANTLR, and archive-era source trees are deleted.
- Historical eval fixture dumps and benchmark scaffolds are deleted.

Use git history only when these fossil paths are explicitly needed.
