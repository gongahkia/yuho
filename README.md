<h1 align="center"><code>Yuho</code></h1>

<p align="center">
    <img src="./assets/logo/yuho_mascot.png" width=40% height=40%>
</p>

<p align="center">
  <em>Haskell-authoritative finite research DSL for reviewable legal-rule models.</em>
</p>

<p align="center">
  <a href="https://github.com/gongahkia/yuho/actions/workflows/release.yml"><img src="https://github.com/gongahkia/yuho/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"/></a>
  <img src="https://img.shields.io/badge/GHC-9.8.4-5e5086.svg" alt="GHC 9.8.4"/>
</p>

<p align="center">
  <a href="./docs/INDEX.md">Docs</a>
  &nbsp;·&nbsp;
  <a href="./docs/positioning/status-matrix.md">Status matrix</a>
  &nbsp;·&nbsp;
  <a href="./library/penal_code/">Encoded library</a>
</p>

## What is Yuho?

`Yuho` is a domain-specific language for finite research representations of law. The current release is the [Haskell Yuho Research Language v1.0.0](./docs/rewrite/HASKELL-YUHO-RESEARCH-LANGUAGE-v1.0.md). Core v0.1-v0.3 cover typed criminal-law structures, finite rules, normative positions, candidate sanctions and explicitly authored responsibility routes. Their documented finite technical-status fragments have machine-checked Lean semantics and independent bounded Haskell–Lean conformance. No whole-project compiler proof or legal-corpus correctness proof is claimed, and Yuho does not determine legal outcomes.

Current applications are focused on Singapore Criminal Law but really can be applied to any jurisdiction that relies on [statutes](https://www.merriam-webster.com/dictionary/statute).

## Authority boundary

The default `yuho` documented for v1 is the executable built from `rewrite/haskell`. It performs parsing, checking, lowering, in-process kernel execution, explanations, corpus queries and native SVG/JSON diagrams without Python, Mermaid, Graphviz, Node, a browser or network access.

The older Python/Tree-sitter product and its Mermaid/transpiler surfaces remain archival compatibility code. Their commands and package are not the Haskell v1 authority.

## Current Capabilities

> [!NOTE]  
> See the [feature status matrix](./docs/positioning/status-matrix.md) for stable, partial, experimental and presently unsupported surfaces.

### General

| Surface | Capability |
|---|---|
| Language | Source-located Haskell parser/checker; Core Yuho v0.1-v0.3; exact-version local modules |
| Operation | `check`, `compile`, `run`, `explain`, `diagram`, `corpus`, `doctor`, `init`, `version`, `release verify` |
| Semantics | Eight versioned KernelInput v1 variants evaluated in-process |
| Formal assurance | 79 registered Lean theorems plus bounded independent Haskell–Lean conformance; not a verified compiler |
| Corpus | 524 saved Penal Code rows structurally indexed; 26 executable offence families in a broad partial research subset |
| Diagrams | Native deterministic standalone SVG and semantic-graph JSON |

### Encoded statues

One of my gripes with [most Legal DSLs](#references) presently available *(in the current year 2024)* are their lack of examples of the DSL actually in use or application.

With this specific trauma in mind, `Yuho` provides a structurally indexed saved corpus of 524 Singapore Penal Code provision records at [`library/penal_code/`](./library/penal_code/). The [Haskell research corpus index](./research/singapore/CORPUS-INDEX.md) separately identifies which bounded rules are executable, partial, definition-only or still unmodelled; structural presence is not executable support or a claim of legal currency.

## Build and ten-minute start

```console
$ git clone https://github.com/gongahkia/yuho && cd yuho
$ cd rewrite/haskell
$ cabal v2-build all --offline -j1 --with-compiler=/home/gongahkia/.ghcup/bin/ghc-9.8.4
$ YUHO="$(cabal list-bin exe:yuho --offline --with-compiler=/home/gongahkia/.ghcup/bin/ghc-9.8.4)"
$ "$YUHO" version
$ "$YUHO" doctor --root ../..
$ "$YUHO" init /tmp/yuho-starter
$ cd /tmp/yuho-starter
$ "$YUHO" check model.yh --scenario scenario.yh
$ "$YUHO" run model.yh --scenario scenario.yh
$ "$YUHO" explain model.yh --scenario scenario.yh
```

The pinned Cabal plan is retained and the normal workflow is offline. See the [v1 release guide](./docs/rewrite/HASKELL-YUHO-RESEARCH-LANGUAGE-v1.0.md) for modules, cases, diagrams, corpus queries and the complete claim boundary.

## Documentation

* [Documentation index](./docs/INDEX.md)
* [Getting started](./docs/user/getting-started.md)
* [5-minute tour](./docs/user/5-minutes.md)
* [Syntax reference](./docs/researcher/syntax.md)
* [Canonical semantics](./docs/researcher/canonical-semantics.md)
* [Contributor architecture](./docs/contributor/architecture.md)

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
