<h1 align="center"><code>Yuho</code></h1>

<p align="center">
    <img src="./assets/logo/yuho_mascot.png" width=40% height=40%>
</p>

<p align="center">
  <em>Domain-specific language for encoding statutes as executable bytes.</em>
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
  <a href="./docs/positioning/status-matrix.md">Status matrix</a>
  &nbsp;·&nbsp;
  <a href="./library/penal_code/">Encoded library</a>
</p>

## What is Yuho?

`Yuho` is a [formally verified](https://en.wikipedia.org/wiki/Formal_verification) domain-specific language dedicated to simplifying [legalese](https://www.merriam-webster.com/dictionary/legalese) by providing a programmatic representation of Singapore Law.  

Current applications are focused on Singapore Criminal Law but really can be applied to any jurisdiction that relies on [statutes](https://www.merriam-webster.com/dictionary/statute).

## For Language Nerds

In specific, `Yuho` mainly comprises a statute DSL compiler that transpiles `.yh` statute encodings *(specified in `Yuho`'s grammer spec)* into a typed AST.

This means you can run syntax, semantic and lint checks on `.yh` code.

`Yuho` also additionally emits reviewable artefacts in JSON, Plaintext English, $LaTeX$, Mermaid, Alloy, DOCX, Akoma Ntoso, and LegalRuleML.

## Current Capabilities

> [!NOTE]  
> See the [feature status matrix](./docs/positioning/status-matrix.md) for stable, partial, experimental and presently unsupported surfaces.

### General

| Surface | Capability |
|---|---|
| Grammar | Tree-sitter grammar for statute blocks, structs, functions, tests, imports, cross-section predicates, penalty combinators, and exception priority |
| Analysis | `yuho check`, `yuho lint`, formatting, AST visualization, source diagnostics |
| Transpilers | JSON, English, LaTeX, Mermaid, Alloy, DOCX, Akoma Ntoso, LegalRuleML |
| Verification | Z3/Alloy backends via `yuho verify`, plus Lean structural-diff checks |
| Corpus tools | AKN round-trip, runtime test sweep, reference graph via `yuho refs` |
| Corpora | `library/penal_code` Singapore canonical corpus, `library/bharatiya_nyaya_sanhita` BNS 2023 replacement corpus for IPC, `library/indian_penal_code` raw IPC snapshot, `library/malaysia_penal_code` and `library/pakistan_penal_code` IPC-lineage proof-of-concept corpora |

### Encoded statues

One of my gripes with [most Legal DSLs](#references) presently available *(in the current year 2024)* are their lack of examples of the DSL actually in use or application.

With this specific trauma in mind, `Yuho` provides a thoroughly encoded corpus of all 524 sections of the
Singapore Penal Code 1871 are encoded at [`library/penal_code/`](./library/penal_code/).

## Installation

### PyPI

The easiest way to get started with `Yuho` is via PyPI installation from the CLI.

```console
$ uv tool install 'yuho[dev]'
$ yuho doctor
$ yuho init yuho-starter
```

### Direct GitHub Repo

Alternatively run the below.

```console
$ git clone https://github.com/gongahkia/yuho && cd yuho
$ ./install.sh --dev
```

## Usage

The below instructions are for locally using and running `Yuho`.

```console
$ uv venv --python 3.13 .venv
$ source .venv/bin/activate
$ uv pip install -e '.[dev]'
$ yuho doctor
$ yuho --help
$ yuho doctor
$ yuho init yuho-starter
$ yuho check library/penal_code/s415_cheating/statute.yh
$ yuho lint library/penal_code/s415_cheating/statute.yh
$ yuho ast library/penal_code/s415_cheating/statute.yh --stats --depth 3
$ yuho verify --capabilities
```

## Shell Completion

`Yuho` optionally provides shell completion for most popular shells.

```console
$ yuho completion zsh --install
$ yuho completion bash --install
$ yuho completion fish --install
```

## Documentation

* [Documentation index](./docs/INDEX.md)
* [Getting started](./docs/user/getting-started.md)
* [5-minute tour](./docs/user/5-minutes.md)
* [Syntax reference](./docs/researcher/syntax.md)
* [Canonical semantics](./docs/researcher/canonical-semantics.md)
* [Contributor architecture](./docs/contributor/architecture.md)

## Citation

If you use `Yuho` or its encoded library in academic work, cite the below.

```bibtex
@software{yuho_2026,
  author  = {Gabriel Ong Zhe Mian},
  title   = {Yuho: A Domain-Specific Language for Encoding the Singapore Penal Code as Executable Statute},
  year    = {2026},
  url     = {https://github.com/gongahkia/yuho},
  version = {5.1.0}
}
```

## Contribute

Yuho is open-source. Contribution guidelines are found at [`CONTRIBUTING.md`](./.github/CONTRIBUTING.md).

## References

### Analogues

`Yuho` takes much inspiration from the following projects.  

* [Natural L4](https://github.com/smucclaw/dsl): Language with an English-like syntax that transpiles to multiple targets, focused on codification of Singapore law at large and Contract Law in specific.
* [Catala](https://github.com/CatalaLang): Language syntax that explicitly mimicks logical structure of the Law, focused on general Socio-fiscal legislature in most jurisidictions.
* [Blawx](https://github.com/Lexpedite/blawx): User-friendly web-based tool for Rules as Code, a declarative logic knowledge representation tool for encoding, testing and using rules.
* [Morphir](https://github.com/finos/morphir): Technology agnostic toolkit for digitisation of business models and their underlying decision logic, enabling automation in fintech.
* [OpenFisca](https://github.com/openfisca/openfisca-core): Open-source platform for modelling social policies through tax and benefits systems across jurisdictions.
* [Docassemble](https://docassemble.org/): Document automation system for generating guided interview documents through a question-and-answer interface.
* [Akoma Ntoso](https://github.com/oasis-open/legaldocml-akomantoso): Standardised XML schema for representing parliamentary, legislative and judiciary documents across jurisdictions.

### Research

`Yuho` stands on the shoulders of past research and academia.  

* [A Logic for Statutes](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088206) by Sarah B Lawsky
* [An End-to-End Pipeline from Law Text to Logical Formulas](https://ebooks.iospress.nl/volumearticle/62060) by Aarne Ranta, Inari Listenmaa, Jerrold Soh and Meng Weng Wong
* [Symbolic and automatic differentiation of languages](https://dl.acm.org/doi/10.1145/3473583) by Conal Elliott
* [Legal Rules, Legal Reasoning, and Nonmonotonic Logic](https://philpapers.org/rec/RIGLRL-2) by Adam W Rigoni
* [Law and logic: A review from an argumentation perspective](https://www.sciencedirect.com/science/article/pii/S0004370215000910) by Henry Prakken and Giovanni Sartor
* [Rules as code: Seven levels of digitisation](https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=5051&context=sol_research) by Meng Weng Wong
* [Defeasible semantics for L4](https://ink.library.smu.edu.sg/cclaw/5/) by Guido Governatori and Meng Weng Wong
* [CLAWs and Effect](https://www.lawsociety.org.sg/publication/claws-and-effect/) by Alexis N Chun
* [The LKIF Core Ontology of Basic Legal Concepts](https://ceur-ws.org/Vol-321/paper3.pdf) by Rinke Hoekstra, Joost Breuker, Marcello Di Bello and Alexander Boer
* [ChatGPT, Large Language Models, and Law](https://fordhamlawreview.org/issues/chatgpt-large-language-models-and-law/) by Harry Surden
* [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) by Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu and Dario Amodei
* [Large Language Models in Law: A Survey](https://arxiv.org/pdf/2312.03718) by Jinqi Lai, Wensheng Gan, Jiayang Wu, Zhenlian Qi and Philip S Yu
* [Automating Defeasible Reasoning in Law with Answer Set Programming](http://platon.etsii.urjc.es/~jarias/GDE-2022/GDE-07.pdf) by Lim How Khang, Avishkar Mahajan, Martin Strecker and Meng Weng Wong
* [User Guided Abductive Proof Generation for Answer Set Programming Queries](https://dl.acm.org/doi/10.1145/3551357.3551383) by Avishkar Mahajan, Martin Strecker and Meng Weng Wong
* [Computer-Readable Legislation Project: What might an IDE-like drafting tool look like?](https://osf.io/uk2vy/) by Matthew Waddington, Laurence Diver and Tin San Leon Qiu
* [Normalized Legal Drafting and the Query Method](https://repository.law.umich.edu/articles/29/) by Layman E Allen and C Rudy Engholm
* [An IDE-like tool for legislative drafting](https://crlp-jerseyldo.github.io/work/an-ide-for-legislation) by crlp-jerseyldo.github.io
* [The Grammar And Structure Of Legal Texts](https://academic.oup.com/edited-volume/34877/chapter-abstract/298341735?redirectedFrom=fulltext) by Risto Hiltunen
* [Does Justice Have a Syntax?](https://www.jstor.org/stable/27073484) by Steven L Winter
* [The syntax of legal exceptions: how the absence of proof is a proof of absence thereof](https://www.tandfonline.com/doi/abs/10.1080/20414005.2017.1283567) by Kyriakos N Kotsoglou
* [The British Nationality Act as a logic program](https://www.semanticscholar.org/paper/The-British-Nationality-Act-as-a-logic-program-Sergot-Sadri/16d480717a1d233ae94b09e3b983d8cc96437644) by M Sergot, F Sadri, R Kowalski, F Kriwaczek, P Hammond and H T Cory