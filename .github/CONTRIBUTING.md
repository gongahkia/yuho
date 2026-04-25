# Contributing to Yuho

The following is a set of guidelines for contributing to Yuho lang spec, hosted [here](https://github.com/gongahkia/yuho) on GitHub. 

These are guidelines, not rules. Use your best judgment, and feel free to propose changes to [this document](https://github.com/gongahkia/yuho/blob/main/.github/CONTRIBUTING.md) in a pull request.

## Table Of Contents

1. [Code of Conduct](#code-of-conduct)
2. [What should I know before I get started?](#what-should-i-know-before-i-get-started)
3. [How Can I Contribute?](#how-can-i-contribute)
    * [Reporting Bugs](#reporting-bugs)
    * [Suggesting Enhancements](#suggesting-enhancements)
    * [Your First Code Contribution](#your-first-code-contribution)
4. [Styleguides](#styleguides)
    * [Git Commit Messages](#git-commit-messages)
    * [Documentation Styleguide](#documentation-styleguide)
5. [FAQ](#faq)

## Code of Conduct

This project and everyone contributing to it is governed by this [Code of Conduct](https://github.com/atom/atom/blob/master/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [gabrielzmong@gmail.com](mailto:gabrielzmong@gmail.com).

## What should I know before I get started?

1. Read through the [README](../README.md) file for prerequisites, installation details and configuration requirements.
2. If you want to contribute, see [here](#how-can-i-contribute).
3. If you have a question, see the [FAQ](#faq) before opening an issue. It could be answered already

## How can I contribute? 

### Reporting Bugs 

This section guides you through submitting a bug report for Yuho. **Following these guidelines** helps maintainers and the community...

1. Understand your report
2. Reproduce the behavior 
3. Find related reports

#### Guidelines for Reporting Bugs

1. Perform a cursory search [here](https://github.com/gongahkia/yuho/issues) for whether the issue has already been reported.
2. If it has already been reported, add a comment to **that issue** instead of opening a new issue.
3. If not already reported, please be as detailed as possible in describing the issue.
4. Follow [this template](./ISSUE_TEMPLATE/BUG_REPORT.md) in the issue's description when opening a new issue.

> [!NOTE]
> If you find a closed issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the new issue description.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Yuho. **Following these guidelines** helps maintainers and the community...

1. Understand your suggestion
2. Gauge demand and popularity

#### Guidelines for Suggesting Enhancements

1. Perform a cursory search [here](https://github.com/gongahkia/yuho/issues) for whether the enhancement has already been suggested.
2. If it has already been suggested, add a comment to **that issue** instead of opening a new issue.
3. If not already suggested, please be as detailed as possible in describing the suggestion.
4. Follow [this template](./ISSUE_TEMPLATE/SUGGEST_ENHANCEMENT_FORM.md) in the issue's description when opening a new issue.

### Your First Code Contribution

Unsure where to begin contributing to Yuho? You can start by looking through these beginner and help-wanted issues:

* [Beginner issues](https://github.com/gongahkia/yuho/labels/good%20first%20issue): Issues which should only require a few lines of code, and a test or two.
* [Help wanted issues](https://github.com/gongahkia/yuho/labels/help%20wanted): Issues which should be a bit more involved than beginner issues.

As for **how** to contribute to Open Source projects, follow [this guide](https://daily.dev/blog/how-to-contribute-to-open-source-projects-as-a-beginner) for a step-by-step walkthrough of opening a pull request.

#### Other useful references

* [Open Source Friday](https://opensourcefriday.com/)
* [Github Docs: Contributing to Open Source](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
* [freeCodeCamp: Open Sourcing](https://github.com/freeCodeCamp/how-to-contribute-to-open-source)
* [Video on Open Source](https://youtu.be/8nq14dHrXgo?si=RiVCIzvGh6-WVkWj)

## Developer Quickstart

Set up a local development environment in under 5 minutes.

### Prerequisites

- Python 3.11+
- Node.js 18+ (for tree-sitter grammar regeneration)
- Git

### Setup

```bash
git clone https://github.com/gongahkia/yuho.git
cd yuho
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Project Layout

```
src/
  tree-sitter-yuho/    # grammar.js -> parser.c
  yuho/
    ast/               # AST nodes, builder, visitor, scope/type analysis
    cli/               # Click CLI commands
    transpile/         # JSON, English, LaTeX, Mermaid, Alloy, etc.
    services/          # analysis pipeline (parse -> AST -> semantic checks)
    resolver.py        # cross-file module resolution
library/               # example statutes (.yh files)
doc/                   # user-facing documentation
```

### Common Tasks

| Task | Command |
|:-----|:--------|
| Run CLI | `yuho --help` |
| Parse + check a file | `yuho check library/penal_code/s415_cheating/statute.yh` |
| Transpile to English | `yuho transpile <file> -t english` |
| Run tests | `yuho test library/penal_code/s415_cheating/test_statute.yh` |
| Regenerate parser | `cd src/tree-sitter-yuho && npx tree-sitter generate` |
| Lint | `yuho lint <file>` |

### Adding a Transpiler

1. Create `src/yuho/transpile/<name>_transpiler.py` implementing `TranspilerBase`
2. Add a variant to `TranspileTarget` enum in `base.py`
3. Register in `registry.py` `_register_builtins()`
4. Add to `__init__.py` exports and CLI choice lists

See `doc/ARCHITECTURE.md` for the full module dependency diagram.

### Adding a CLI Command

1. Add implementation in `src/yuho/cli/commands/<name>.py`
2. Register in `main.py` (top-level) or `commands_registry.py` (grouped)

### Modifying the Grammar

1. Edit `src/tree-sitter-yuho/grammar.js`
2. Run `cd src/tree-sitter-yuho && npx tree-sitter generate`
3. Update `src/yuho/ast/builder.py` to handle new CST node types
4. Verify: `yuho check <file>` on a sample

## Styleguides

### Git Commit Messages

We follow [these guidelines](https://gist.github.com/robertpainsi/b632364184e70900af4ab688decf6f53) to style commit messages. Keep them concise and informative.

### Documentation Styleguide

Our documentation is written in [Markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax), and we follow the [Github Markdown Styleguide](https://github.com/google/styleguide/blob/gh-pages/docguide/style.md).

## [FAQ](../docs/user/faq.md)
