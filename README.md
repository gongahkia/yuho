> [!IMPORTANT]  
> Yuho is undergoing a major overhaul right now.   
> This means language features are likely to change.
> 
> For a rough idea of where Yuho is headed, see  
> [`reworked_sample_cheating.md`](./doc/main/reworked_sample_cheating.md).  
>   
> As such, support for other transpilation outputs is not   
> currently my primary focus. To see what is being worked on,   
> refer [here](./doc/main/future.md).  
>   
> I can be found on Linkedin for anything urgent.  
>   
> *\- Gabriel*   

![](https://img.shields.io/badge/yuho_1.0-passing-green)

# `Yuho`

Yuho is a domain-specific language providing a programmatic representation of Singapore Criminal Law.

## Rationale

The law is innately complex.  

[Statutes](https://sso.agc.gov.sg/) are not always easy to understand, especially for incoming law students new to [legalese](https://www.merriam-webster.com/dictionary/legalese) and its [logical structure](https://law.stanford.edu/wp-content/uploads/2018/04/ILEI-Forms-of-Legal-Reasoning-2014.pdf).  

Criminal Law is often a [foundational module](https://law.smu.edu.sg/programmes/core-courses-description) most students take in their first year of law school. In particular, Singapore Criminal Law is nearly entirely statute-based, largely focusing on the [Penal Code](https://sso.agc.gov.sg/Act/PC1871).

Yuho is a DSL that seeks to *help law students* better understand statutes by providing a flexible syntax which affords a programmatic representation of Singapore Criminal Law. By allowing users to decide how to represent stautory provisions in `.yh` code, the hope is that the statute's key elements and its underlying conditional relationships surface themselves. These representations can be coarse or granular, entirely scoped by their use-cases.  

For those interested, Yuho provides a [grammatically-validated](https://www.usna.edu/Users/cs/wcbrown/courses/F19SI413/lec/l07/lec.html) syntax core that splays out all requirements and consequences for a given offence, providing assurance of logical correctness from the get-go. Yuho was also designed to be [exception-validated](https://www.reddit.com/r/learnjavascript/comments/y6663u/difference_between_input_validation_and_exception/) and [language-agnostic](https://softwareengineering.stackexchange.com/questions/28484/what-is-language-agnosticism-and-why-is-it-called-that), transpiling from one formally-specified source of truth to multiple target outputs, encouraging the development of tools that leverage off Yuho's logical core.

Getting into the specifics, Yuho provides the following four products.

1. [Yuho](./doc/main/syntax.md), a DSL made to be readable and codeable by law students and lawyers
2. [Formalised semantic](./tests/) for legal reasoning modelled after the syntactical patterns of the law
3. [Web frontend](./web/) that displays a statute's logic as a flowchart
4. [Transpiler](./src/) that transpiles to the below targets

### Output formats

| Target | Usage | 
| :--- | :--- |
| [JSON](src/archive/v1/secondary/yuho_to_json) | REST APIs |
| [Mermaid](src/archive/v1/secondary/json_to_mmd) | diagrammatic representation |  
| [JavaScript](src/archive/v1/secondary/yuhoToJavaScript) | :warning: *DISCONTINUED, REPLACED BY JSON* :warning: |
| [HTML](src/archive/v1/secondary/yuho_json_mmd_to_html) | frontend display for learning purposes |  
| [R](src/archive/v1/secondary/yuhoToR) | data modelling and visualisation |
| [Alloy](src/archive/v1/secondary/yuhoToAlloy) | formal verification |
| [Whiley](src/archive/v1/secondary/yuhoToWhiley) | decision logic |
| [Catala](src/archive/v1/secondary/yuhoToCatala) | decision logic |
| [F*](src/archive/v1/secondary/yuhoToFStar) | proof backends |

## Documentation

* [Language specification](./doc/main/syntax.md)
* [Grammer specification](./grammer/)
* [Formal verification](./tests/)
* [Examples](./example/)

## Scope

Development is currently scoped by the following statutes as specified [here](./doc/main/scope.md). 

## Usage

### CLI 

```console
$ git clone https://github.com/gongahkia/yuho
$ cd yuho  
$ make config
$ make build
```

## Contribute

Yuho is open-source. Contribution guidelines are found at [CONTRIBUTING.md](./admin/CONTRIBUTING.md).

## FAQ

### 1. What does Yuho mean?

Yuho is derived from 夢 法 (*yume ho*) which roughly translates to 'ideal law' in Japanese.

## References

### Analogues

Yuho takes much inspiration from the following projects.

* [Catala](https://github.com/CatalaLang): Language syntax that explicitly mimicks logical structure of the Law, focused on general Socio-fiscal legislature in most jurisidictions.
* [Natural L4](https://github.com/smucclaw/dsl): Language with an English-like syntax that transpiles to multiple targets, focused on codification of contracts and Singapore Contract Law.
* [Blawx](https://github.com/Lexpedite/blawx): User-friendly web-based tool for Rules as Code, a declarative logic knowledge representation tool for encoding, testing and using rules.
* [Morphir](https://github.com/finos/morphir): Technology agnostic toolkit for digitisation of business models and their underlying decision logic, enabling automation in fintech.

### Research

* [A Logic for Statutes](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088206) by Sarah B Lawsky
* [Symbolic and automatic differentiation of languages](https://dl.acm.org/doi/10.1145/3473583) by Conal Elliott
* [Legal Rules, Legal Reasoning, and Nonmonotonic Logic](https://philpapers.org/rec/RIGLRL-2) by Adam W Rigoni
* [Law and logic: A review from an argumentation perspective](https://www.sciencedirect.com/science/article/pii/S0004370215000910) by Henry Prakken, Giovanni Sartor
* [Defeasible semantics for L4](https://ink.library.smu.edu.sg/cclaw/5/) by Guido Governatori, Meng Weng Wong
* [CLAWs and Effect](https://www.lawsociety.org.sg/publication/claws-and-effect/) by Alexis N Chun
* [The LKIF Core Ontology of Basic Legal Concepts](https://ceur-ws.org/Vol-321/paper3.pdf) by Rinke Hoekstra, Joost Breuker, Marcello Di Bello, Alexander Boer
* [ChatGPT, Large Language Models, and Law](https://fordhamlawreview.org/issues/chatgpt-large-language-models-and-law/) by Harry Surden
* [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) by Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, Dario Amodei
* [Large Language Models in Law: A Survey](https://arxiv.org/pdf/2312.03718) by Jinqi Lai, Wensheng Gan, Jiayang Wu, Zhenlian Qi and Philip S Yu
