# Changelog

All notable changes to Yuho are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **BibTeX transpiler** -- export caselaw entries as BibTeX records (`yuho transpile -t bibtex`)
- **HTML transpiler** -- standalone HTML pages with embedded Mermaid diagrams (`yuho transpile -t html`)
- **Mermaid renderer** -- SVG/PNG output via mermaid-cli (`yuho transpile -t svg` / `-t png`)
- **JSON Schema** -- `yuho schema` command outputs JSON Schema for AST validation
- **PDF export** -- LaTeX-to-PDF compilation pipeline (`yuho transpile -t pdf`)
- **Plain-language English mode** -- simplified non-legal English output
- **Batch commands** -- `yuho batch check` and `yuho batch transpile` for directory-level operations
- **Library bulk export** -- `yuho library export -t <target>` transpiles all installed statutes
- **Diff scoring** -- `yuho diff --score` grades student submissions against model answers
- **Doc-comment preservation** -- `///` doc-comments attached to struct/function/statute AST nodes
- **Module resolver wiring** -- scope analysis and type checking now use cross-file resolution
- **Law student guide** -- `doc/LAW_STUDENT_GUIDE.md` practical tutorial
- **Architecture docs** -- `doc/ARCHITECTURE.md` module dependency diagram
- **Transpiler plugin guide** -- `doc/TRANSPILER_PLUGINS.md` for adding new targets
- **Grammar development guide** -- `src/tree-sitter-yuho/GRAMMAR.md`
- **Developer quickstart** -- added to `.github/CONTRIBUTING.md`

### Changed
- tree-sitter grammar: `doc_comment` now parsed as named children of declarations (prec 1 vs -1)
- English transpiler accepts `plain_language=True` for simplified output
- Transpile CLI now supports 13 target formats (was 9)

### Fixed
- Module resolver not running during semantic analysis
- Test command not resolving `referencing` statements before evaluation
