[![](https://img.shields.io/badge/yuho_1.0-passing-green)](https://github.com/gongahkia/yuho/releases/tag/1.0) [![](https://img.shields.io/badge/yuho_2.0-passing-green)](https://github.com/gongahkia/yuho/releases/tag/2.0) ![](https://img.shields.io/badge/yuho_3.0-build-orange)
  
> [!IMPORTANT]
> Reworking the entirity of Yuho in v3.0.  
> Most things are about to change, but change is good.  
> Watch this space.  
>  
> ~ Gabriel  
  
# `Yuho`  
  
<p align="center">
<img src="./asset/logo/yuho_mascot.png" width=40% height=40%>
</p>

Yuho is a domain-specific language providing a programmatic representation of Singapore Tort and Criminal Law.

Dedicated to simplifying [legalese](https://www.merriam-webster.com/dictionary/legalese).

## Rationale

The law is innately complex.  

[Statutes](https://sso.agc.gov.sg/) are not always easy to understand, especially for incoming law students new to [legalese](https://www.merriam-webster.com/dictionary/legalese) and its [logical structure](https://law.stanford.edu/wp-content/uploads/2018/04/ILEI-Forms-of-Legal-Reasoning-2014.pdf).  

Criminal Law is often a [foundational module](https://law.smu.edu.sg/programmes/core-courses-description) most students take in their first year of law school. In particular, Singapore Criminal Law is nearly entirely statute-based, largely focusing on the [Penal Code](https://sso.agc.gov.sg/Act/PC1871).

Yuho is a DSL that seeks to *help law students* better understand statutes by providing a flexible syntax which affords a programmatic representation of Singapore Criminal Law. By allowing users to decide how to represent stautory provisions in `.yh` code, the hope is that the statute's key elements and its underlying conditional relationships surface themselves. These representations can be coarse or granular, entirely scoped by their use-cases.  

Getting into the specifics, Yuho provides the following four products.

1. [Yuho](./doc/main/syntax.md), a DSL made to be readable and codeable by law students and lawyers
2. [Formalised semantic](./tests/main) for legal reasoning modelled after the syntactical patterns of the law
3. [CLI tool](./src/main/) for interacting with Yuho's primary functions in the CLI
4. [Transpiler](./src/main/) that transpiles to the below targets

> FUA edit the entire above rationale to account for tort law and Yuho's future scope and specificity

### Output formats

| Target | Usage |   
| :--- | :--- |  
| | | 

Sold on Yuho? Check out the [quickstart](#quickstart) guide.

> FUA edit the above table and add transpilation outputs when they're worked out

## Nerd stuff

For those interested, Yuho provides a [grammatically-validated](https://www.usna.edu/Users/cs/wcbrown/courses/F19SI413/lec/l07/lec.html) syntax core that splays out all requirements and consequences for a given offence, providing assurance of logical correctness from the get-go. Yuho was also designed to be [exception-validated](https://www.reddit.com/r/learnjavascript/comments/y6663u/difference_between_input_validation_and_exception/) and [language-agnostic](https://softwareengineering.stackexchange.com/questions/28484/what-is-language-agnosticism-and-why-is-it-called-that), transpiling from one formally-specified source of truth to multiple target outputs, encouraging the development of tools that leverage off Yuho's logical core.   

Want to find out more? See Yuho's [documentation](#documentation).

> FUA edit the above section later when Yuho v3.0's purpose and scope is clear

### Documentation

* [Language specification](./doc/SYNTAX.md)
* [Grammer specification](./)
* [Formal verification](./)
* [Examples](./example)

> FUA add the relative links to the relevant directories here later

## Quickstart

Learn how Yuho works in 5 minutes at [`5_MINUTES.md`](./doc/5_MINUTES.md).

## Roadmap

The below products are in development. 

For more details on what's being worked on currently, refer to [`KANBAN.md`](./doc/KANBAN.md).  
  
For more details on what's being implemented in the future, refer to [`ROADMAP.md`](./doc/ROADMAP.md).

1. blah blah blah

> FUA add more details here later

## Scope

Development is currently scoped by the following statutes at [`SCOPE.md`](./doc/SCOPE.md). 

## Contribute

Yuho is open-source. Contribution guidelines are found at [`CONTRIBUTING.md`](./admin/CONTRIBUTING.md).

## References

### Analogues

Yuho takes much inspiration from the following projects.  

* [Natural L4](https://github.com/smucclaw/dsl): Language with an English-like syntax that transpiles to multiple targets, focused on codification of Singapore law at large and Contract Law in specific.
* [Catala](https://github.com/CatalaLang): Language syntax that explicitly mimicks logical structure of the Law, focused on general Socio-fiscal legislature in most jurisidictions.
* [Blawx](https://github.com/Lexpedite/blawx): User-friendly web-based tool for Rules as Code, a declarative logic knowledge representation tool for encoding, testing and using rules.
* [Morphir](https://github.com/finos/morphir): Technology agnostic toolkit for digitisation of business models and their underlying decision logic, enabling automation in fintech.
* [OpenFisca](https://github.com/openfisca/openfisca-core): Open-source platform for modelling social policies through tax and benefits systems across jurisdictions.
* [Docassemble](https://docassemble.org/): Document automation system for generating guided interview documents through a question-and-answer interface.
* [Akoma Ntoso](https://github.com/oasis-open/legaldocml-akomantoso): Standardised XML schema for representing parliamentary, legislative and judiciary documents across jurisdictions.

### Research

Yuho stands on the shoulders of past research and academia.  

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
