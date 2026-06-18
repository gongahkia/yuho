<p align="center">
  <img src="./assets/logo/yuho_mascot.png" width="200" alt="Yuho mascot"/>
</p>

<h1 align="center">Yuho</h1>

<p align="center">
  <em>A domain-specific language for encoding statutes as executable, machine-checkable artefacts.</em>
</p>

<p align="center">
  <a href="https://github.com/gongahkia/yuho/actions/workflows/release.yml"><img src="https://github.com/gongahkia/yuho/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
  <a href="https://doi.org/10.5281/zenodo.19935537"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.19935537.svg" alt="Zenodo DOI"/></a>
  <a href="https://pypi.org/project/yuho/"><img src="https://img.shields.io/pypi/v/yuho" alt="PyPI"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"/></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/L1%2BL2-524%2F524-brightgreen.svg" alt="L1+L2 coverage"/>
  <img src="https://img.shields.io/badge/L3-524%2F524-brightgreen.svg" alt="L3 coverage"/>
</p>

<p align="center">
  <a href="https://gabrielongzm.com">Gabriel Ong Zhe Mian</a>
  &nbsp;·&nbsp;
  <a href="./paper/">Paper</a>
  &nbsp;·&nbsp;
  <a href="./docs/INDEX.md">Docs</a>
  &nbsp;·&nbsp;
  <a href="./library/penal_code/">Encoded library</a>
</p>

## What is Yuho?

Yuho is a domain-specific language dedicated to simplifying [legalese](https://www.merriam-webster.com/dictionary/legalese) by providing a programmatic representation of Singapore Law.  

Yuho's top-level construct is a `statute` block with first-class fields for `elements`, `penalties`, `illustrations`, `exceptions`, and `amendment` lineage. 

By tracking how statues are actually drafted, Yuho allows you to encode a section line-for-line *(the same way you would read it)*.

[Current applications](#coverage) are focused on Singapore Criminal Law but really can be applied to any jurisdiction that relies on [statutes](https://www.merriam-webster.com/dictionary/statute).

## Coverage

The proof of concept is a complete encoding of all 524 sections of the **Singapore Penal Code 1871**

In mass-encoding the full code surfaced fourteen distinct grammar gaps (G1–G14), all either resolved in the parser or rerouted to a fidelity-diagnostic linter. These are documented in greater detail at [`docs/researcher/phase-c-gaps.md`](./docs/researcher/phase-c-gaps.md).

Road-map wise, a second corpus (in the **Indian Penal Code 1860**) was considered with presently conservative coverage of 493 of its sections at [`library/indian_penal_code/_raw/act.json`](./library/indian_penal_code/_raw/)).

## Ecosystem

Yuho is built around a toolchain of 8 other transpilers, including Akoma Ntoso for cross-jurisdictional interop, an LSP, an MCP server, a VS Code extension, and Z3 / Alloy verification hookups.

For more on Yuho, see the paper at [`paper/`](./paper/) or check out a 5-minute tour at [`docs/user/5-minutes.md`](./docs/user/5-minutes.md)

## Quickstart

### Installation

#### `uv`

```sh
git clone https://github.com/gongahkia/yuho && cd yuho
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
yuho --version
pytest tests/ --ignore=tests/e2e -q
```

#### `pip` 

```sh
git clone https://github.com/gongahkia/yuho && cd yuho
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### Usage

#### I want to *read* an encoded statute

```sh
cat library/penal_code/s415_cheating/statute.yh           
yuho transpile -t english library/penal_code/s415_cheating/statute.yh
```

#### I want to *encode* a new statute

```sh
yuho --version                                            
yuho check examples/simple_statute.yh
```

## Feature matrix

| Surface | Capability |
|---|---|
| **Grammar** | Tree-sitter, 14 grammar gaps closed, deontic types, Catala-style exception priority, nested penalty combinators, lam4-style `is_infringed` + Catala-style `apply_scope` cross-section predicates |
| **Transpilers** | JSON · controlled English · LaTeX · Mermaid flowchart (statute / schema shapes) · Mermaid mindmap · Alloy · DOCX · Akoma Ntoso |
| **Editors** | LSP (hover, inlay hints, completion, code lens, fidelity diagnostics) · VS Code · Word add-in · browser extension · static explorer site |
| **AI integration** | MCP server (tools, resources, prompts) usable from Claude Desktop / Claude Code / Codex CLI / Cursor |
| **Verification** | Z3 (exception-priority + cross-section conflict) · Alloy (bounded element-combination enumeration) |
| **Analytical tools** | Counter-example explorer (`yuho explore`) · charge recommender (`yuho recommend`, structural ranking, not legal advice) · fact-pattern simulator · cross-library comparator (`yuho refs --compare-libraries`) |
| **Chronology / provenance** | Source-backed facts, timelines, relationships, issues, deadlines, exhibits, scenarios, semantic diff, and JSON/Markdown/Mermaid/SVG/HTML exports via `yuho chronology` |
| **Coverage harness** | L1 (parse) · L2 (build + lint + fidelity) · L3 (11-point human audit) |
| **Library** | 524 / 524 sections of the SG Penal Code 1871 encoded, stamped, and indexed; 493 IPC sections raw-scraped + 8 phase-1 encoded for comparative analysis |

## Architecture

```
.yh source ──▶ tree-sitter parser ──▶ Python AST ──▶ analyser stack
                                                        │
                                       ┌────────────────┼────────────────┐
                                       ▼                ▼                ▼
                                   Transpilers      Verification      Editor surfaces
                              (JSON/EN/TeX/MMD/
                               mindmap/Alloy/DOCX/AKN)  (Z3, Alloy)       (LSP, MCP, VSCode)
```

## Citation

If you use Yuho or its encoded library in academic work, please cite:

```bibtex
@software{yuho_2026,
  author  = {Gabriel Ong Zhe Mian},
  title   = {Yuho: A Domain-Specific Language for Encoding the Singapore
             Penal Code as Executable Statute},
  year    = {2026},
  url     = {https://github.com/gongahkia/yuho},
  version = {5.1.0}
}
```

A `CITATION.cff` is provided at the repo root for tools that consume that
format.

## Contributing

See [`.github/CONTRIBUTING.md`](./.github/CONTRIBUTING.md)

## License

[MIT](./LICENSE).
