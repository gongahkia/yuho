# Changelog

## [3.0.0] - 2024-09-19

### Added
- **Complete Python implementation** of Yuho language
- **Lark-based parser** with formal grammar specification
- **Comprehensive CLI tools** with `check`, `draw`, `alloy`, `draft`, and `how` commands
- **Interactive REPL** for testing Yuho code
- **Semantic analyzer** with type checking and error reporting
- **Mermaid transpiler** for flowcharts and mindmaps
- **Alloy transpiler** for formal verification
- **Improved error messages** with colorized output
- **Module import system** with `referencing ... from ...` syntax
- **Package management** with pip-installable setup

### Changed
- **Primary implementation language** changed from Racket to Python
- **Build system** updated to use Python/pip instead of Rust/Cargo
- **CLI interface** redesigned with Click framework
- **Documentation** updated for v3.0 with quickstart guide

### Deprecated
- **Racket implementation** (v2.0) marked as legacy
- **Rust implementation** (v1.0) marked as archived

### Technical Details
- Python 3.8+ required
- Dependencies: lark-parser, click, colorama
- Modular architecture with separate lexer, parser, semantic analyzer, and transpilers
- Full AST support with comprehensive node types
- Error handling with detailed diagnostics

## [2.0.0] - Previous Release (Racket)
- Racket-based implementation
- Basic CLI tools
- Limited transpilation support

## [1.0.0] - Initial Release (Rust)
- Proof of concept implementation
- Basic parsing capabilities