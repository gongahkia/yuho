<p align="center">
  <img src="./assets/logo/yuho_mascot.png" width="200" alt="Yuho mascot"/>
</p>

<h1 align="center">Yuho</h1>

<p align="center">
  <em>A domain-specific language for encoding statutes as executable, machine-checkable artefacts.</em>
</p>

<p align="center">
  <a href="https://github.com/gongahkia/yuho/actions/workflows/ci.yml"><img src="https://github.com/gongahkia/yuho/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <a href="https://github.com/gongahkia/yuho/actions/workflows/release.yml"><img src="https://github.com/gongahkia/yuho/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
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

---

## What is Yuho?

Yuho is a statute-shaped DSL: the top-level construct is a `statute N { … }`
block with first-class fields for elements, penalties, illustrations,
exceptions, and amendment lineage. The grammar tracks how penal code is
actually drafted, so encoding a section is line-for-line with reading it.

The proof of concept is a complete encoding of the **Singapore Penal Code
1871** — all 524 sections, 524 passing parse-and-build (L1+L2), 524
author-stamped at the strictest fidelity tier (L3, 11-point checklist;
external counsel review remains future work — see paper §7).
Mass-encoding the full
code surfaced fourteen distinct grammar gaps (G1–G14), all either resolved
in the parser or rerouted to a fidelity-diagnostic linter; the catalogue
is documented in [`docs/researcher/phase-c-gaps.md`](./docs/researcher/phase-c-gaps.md).

Around the language sits a complete toolchain — seven transpilers
(including Akoma Ntoso for cross-jurisdictional interop), an LSP, an
MCP server, a VS Code extension, and Z3 / Alloy verification hookups —
described below.

---

## Quickstart

### Supported Python: 3.10 – 3.13

CI tests 3.10, 3.11, 3.12, 3.13. **Avoid Python 3.14 on macOS Homebrew** —
the current `python@3.14` formula has an Expat ABI mismatch
(`Symbol not found: _XML_SetAllocTrackerActivationThreshold`) that
breaks every Python project doing XML parsing, including Yuho's AKN
transpiler. A future Homebrew rotation will fix it; until then use
3.10–3.13.

### Recommended: install via `uv`

`uv` ships its own statically-linked Pythons and sidesteps Homebrew's
`ensurepip` and `libexpat` glitches entirely.

```sh
brew install uv                 # one-time; or pipx install uv
git clone https://github.com/gongahkia/yuho && cd yuho
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
yuho --version                  # 5.1.0
pytest tests/ --ignore=tests/e2e -q
```

### Fallback: plain `pip` (works if your Python install is healthy)

```sh
git clone https://github.com/gongahkia/yuho && cd yuho
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### I want to *read* an encoded statute

```sh
cat library/penal_code/s415_cheating/statute.yh           # the source
yuho transpile -t english library/penal_code/s415_cheating/statute.yh
```

### I want to *encode* a new statute

```sh
yuho --version                                            # 5.1.0
yuho check examples/simple_statute.yh                     # validate
```

VS Code: install the extension under `editors/vscode-yuho/`, open a `.yh`
file, hover over a `statute N` header to see its canonical SSO link and
coverage badges. See [`editors/vscode-yuho/README.md`](./editors/vscode-yuho/README.md).

### I want to *understand* the design

Read the paper draft in [`paper/`](./paper/) — full prose treatment of
the grammar, the toolchain, and the empirical findings from mass-encoding.
The 5-minute tour at [`docs/user/5-minutes.md`](./docs/user/5-minutes.md)
covers the same ground in less depth.

---

## Feature matrix

| Surface | Capability |
|---|---|
| **Grammar** | Tree-sitter, 14 grammar gaps closed, deontic types, Catala-style exception priority, nested penalty combinators, lam4-style `is_infringed` + Catala-style `apply_scope` cross-section predicates |
| **Transpilers** | JSON · controlled English · LaTeX · Mermaid · Alloy · DOCX · Akoma Ntoso |
| **Editors** | LSP (hover, inlay hints, completion, code lens, fidelity diagnostics) · VS Code · Word add-in · browser extension · static explorer site |
| **AI integration** | MCP server (tools, resources, prompts) usable from Claude Desktop / Claude Code / Codex CLI / Cursor |
| **Verification** | Z3 (exception-priority + cross-section conflict) · Alloy (bounded element-combination enumeration) |
| **Analytical tools** | Counter-example explorer (`yuho explore`) · charge recommender (`yuho recommend`, structural ranking, not legal advice) · fact-pattern simulator |
| **Coverage harness** | L1 (parse) · L2 (build + lint + fidelity) · L3 (11-point human audit) |
| **Library** | 524 / 524 sections of the SG Penal Code 1871 encoded, stamped, and indexed |

---

## Architecture

```
.yh source ──▶ tree-sitter parser ──▶ Python AST ──▶ analyser stack
                                                        │
                                       ┌────────────────┼────────────────┐
                                       ▼                ▼                ▼
                                   Transpilers      Verification      Editor surfaces
                              (JSON/EN/TeX/MMD/         (Z3, Alloy)       (LSP, MCP, VSCode)
                               Alloy/DOCX)
```

A rendered SVG version lives at `paper/figures/architecture.mmd` and
will land at `docs/architecture.svg` once the Mermaid CLI build runs.

---

## Project status

| Metric | Value |
|---|---|
| Sections encoded | 524 / 524 |
| L1 (parse) | 524 / 524 |
| L2 (build + lint) | 524 / 524 |
| L3 (author-stamped) | 524 / 524 (external counsel review pending) |
| Grammar gaps (G1–G14) | 10 fixed · 2 not-a-gap · 1 lint · 1 deferred |
| Implementation SLOC | ~38.7k Python + 900 grammar.js |
| Library SLOC | ~16.4k `.yh` |

Numbers regenerate from `library/penal_code/_coverage/coverage.json` via
`scripts/coverage_report.py`.

---

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

---

## Contributing

See [`.github/CONTRIBUTING.md`](./.github/CONTRIBUTING.md). Issues and pull
requests welcome; the [`TODO.md`](./TODO.md) file tracks current
priorities and `[x]`-marks completed work.

## License

[MIT](./LICENSE).
