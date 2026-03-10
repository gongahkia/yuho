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

- **Comparative transpiler** -- side-by-side markdown table comparing multiple statutes (`yuho transpile -t comparative`)
- **Verification report** -- LaTeX structural completeness report (`yuho verify-report`)
- **Jurisdiction metadata** -- `@jurisdiction` and `@meta` doc-comment annotations on statutes
- **Compliance matrix** -- checklist generator for compliance officers (`yuho compliance-matrix`)
- **Training pair export** -- JSONL export for LLM fine-tuning (`yuho export-training`)
- **Pre-built explanations** -- batch English explanation generator (`yuho explain-all`)
- **Web playground** -- browser-based editor with live transpilation (`yuho playground`)
- **Static site generator** -- browsable HTML site from statute library (`yuho static-site`)
- **Z3 test generation** -- generate test cases via constraint solving (`yuho generate-tests`)
- **Porting guide** -- `doc/PORTING_GUIDE.md` for modeling new jurisdictions
- **Python SDK docs** -- `doc/SDK.md` covering all public APIs
- **OpenAPI spec** -- `doc/openapi.yaml` for REST API endpoints
- **Dockerfile** -- production container with tree-sitter and all dependencies
- **GitHub Action** -- CI/CD workflow for Docker builds
- **Schema versioning** -- `AST_SCHEMA_VERSION` constant in JSON Schema module
- **Expanded library** -- 25 Singapore Penal Code sections (was 12)
- **Real per-element tests** -- parametrized tests for all library statutes
- **E2E transpiler tests** -- roundtrip tests for all transpile targets

### Changed
- tree-sitter grammar: `doc_comment` now parsed as named children of declarations (prec 1 vs -1)
- English transpiler accepts `plain_language=True` for simplified output
- Transpile CLI now supports 16 target formats (was 9)
- StatuteNode now carries `jurisdiction` and `jurisdiction_meta` fields

### Fixed
- Module resolver not running during semantic analysis
- Test command not resolving `referencing` statements before evaluation
