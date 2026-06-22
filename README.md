<h1 align="center">Yuho</h1>

<p align="center">
  <em>A domain-specific language for encoding statutes as executable, machine-checkable artefacts.</em>
</p>

<p align="center">
  <a href="https://github.com/gongahkia/yuho/actions/workflows/release.yml"><img src="https://github.com/gongahkia/yuho/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
  <a href="https://pypi.org/project/yuho/"><img src="https://img.shields.io/pypi/v/yuho" alt="PyPI"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"/></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"/>
</p>

<p align="center">
  <a href="https://gabrielongzm.com">Gabriel Ong Zhe Mian</a>
  &nbsp;·&nbsp;
  <a href="./docs/INDEX.md">Docs</a>
  &nbsp;·&nbsp;
  <a href="./library/penal_code/">Encoded library</a>
</p>

## What is Yuho?

Yuho is a local statute DSL compiler. Its primary job is to turn `.yh`
statute encodings into a typed AST, run syntax/semantic/lint checks, and
emit reviewable artefacts such as JSON, controlled English, LaTeX,
Mermaid, Mermaid mindmap, Alloy, DOCX, Akoma Ntoso, and LegalRuleML.

The repository also carries a checked-in corpus: all 524 sections of the
Singapore Penal Code 1871 are encoded under `library/penal_code/`. The
other corpus material covers the BNS 2023 replacement corpus for IPC, a
raw Indian Penal Code snapshot, and Malaysia/Pakistan IPC-lineage
proof-of-concept corpora.

## Current scope

Retained surfaces:

| Surface | Capability |
|---|---|
| Grammar | tree-sitter grammar for statute blocks, structs, functions, tests, imports, cross-section predicates, penalty combinators, and exception priority |
| Analysis | `yuho check`, `yuho lint`, formatting, AST visualization, source diagnostics |
| Transpilers | JSON, English, LaTeX, Mermaid, Mermaid mindmap, Alloy, DOCX, Akoma Ntoso, LegalRuleML |
| Verification | Z3/Alloy backends via `yuho verify`, plus Lean structural-diff checks |
| Corpus tools | Penal Code coverage checks, AKN round-trip, runtime test sweep, reference graph via `yuho refs` |
| Corpora | `library/penal_code` Singapore canonical corpus; `library/bharatiya_nyaya_sanhita` BNS 2023 replacement corpus for IPC; `library/indian_penal_code` raw IPC snapshot; `library/malaysia_penal_code` and `library/pakistan_penal_code` IPC-lineage proof-of-concept corpora |

Non-core product surfaces were removed; this repository now focuses on
the local compiler, transpilers, verification checks, and corpus tooling.

## Quickstart

```sh
git clone https://github.com/gongahkia/yuho
cd yuho
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
yuho --help
yuho check library/penal_code/s415_cheating/statute.yh
```

Read an encoded statute:

```sh
cat library/penal_code/s415_cheating/statute.yh
yuho transpile -t english library/penal_code/s415_cheating/statute.yh
```

Inspect the corpus reference graph:

```sh
yuho refs 415
yuho refs --scc --json
```

Run the retained verification gate:

```sh
make verify-core
```

## Verification backends

`uv pip install -e '.[dev]'` installs the Python Z3 binding used by
`yuho verify --engine z3`. Alloy is out-of-band: install the Alloy 6
Analyzer separately from the [Alloy download page](https://alloytools.org/download.html)
and pass the jar when invoking the Alloy backend:

```sh
yuho verify --engine alloy --alloy-jar path/to/org.alloytools.alloy.dist.jar FILE.yh
```

## Architecture

```text
.yh source -> tree-sitter parser -> Python AST -> analysis/lint
                                             -> transpilers
                                             -> verification
                                             -> corpus graph checks
```

## Documentation

Start with:

- [Documentation index](./docs/INDEX.md)
- [Getting started](./docs/user/getting-started.md)
- [5-minute tour](./docs/user/5-minutes.md)
- [Syntax reference](./docs/researcher/syntax.md)
- [Contributor architecture](./docs/contributor/architecture.md)

## Citation

If you use Yuho or its encoded library in academic work, cite the
software artefact:

```bibtex
@software{yuho_2026,
  author  = {Gabriel Ong Zhe Mian},
  title   = {Yuho: A Domain-Specific Language for Encoding the Singapore Penal Code as Executable Statute},
  year    = {2026},
  url     = {https://github.com/gongahkia/yuho},
  version = {5.1.0}
}
```

## License

[MIT](./LICENSE).
