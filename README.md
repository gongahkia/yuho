> [!IMPORTANT]  
> Yuho is not actively under development right now.  
> This means language features are relatively set in stone.  
> Also, note that there is currently only rudimentary support  
> for transpilation of Yuho to other outputs.  
> 
> I will return to work on this in the future.  
> 
> *\- Gabriel* 

![](https://img.shields.io/badge/yuho_1.0-passing-green)

# `Yuho`

Yuho is a domain-specific language providing a programmatic representation of Singapore Criminal Law.

## Rationale

The law is innately complex, with statutes often calling for further human discernment. 

In a bid to automate out inefficiency, many public systems incorporate [programs](https://youtu.be/jmHwAh_-IOU?si=f4DlP7pklN424kCw) *(written in languages like C, COBOL, Java, etc.)* that compute payments to be collected and disbursed, especially in the areas of income, housing and corporate tax. 

However, these computations are often written by programmers who have little understanding of the actual legislation invoked to arrive at the given valuation. As such, the only way to ensure the correctness of these programs is through unit tests which must be calculated and handwritten by lawyers. Due to the aforementioned intricacies and many exceptions found in the law, the number of unit tests quickly skyrockets into the thousands. Moreover, inevitable modifications to existing legislation effectively mean these unit tests have to be rewritten multiple times, wasting many manhours. 

Ultimately, the tedium of such a task means most programs in this vein fail the minimum requirements of [sufficient unit testing](https://daedtech.com/unit-testing-enough/), resulting in large-scale undertesting that causes [costly failures](https://inria.hal.science/hal-02936606v1/document).

Yuho combats these issues by providing a [grammatically-validated](https://www.usna.edu/Users/cs/wcbrown/courses/F19SI413/lec/l07/lec.html) syntax core for Singapore Criminal Law that presents all possible consequences for a given offence, whilst providing an assurance of logical correctness to reduce the number of unit tests that must be written for a given computation. Additionally, Yuho is designed to be [exception-validated](https://www.reddit.com/r/learnjavascript/comments/y6663u/difference_between_input_validation_and_exception/) and [language-agnostic](https://softwareengineering.stackexchange.com/questions/28484/what-is-language-agnosticism-and-why-is-it-called-that), transpiling from a single formally-specified source of truth to multiple target outputs, encouraging the development of tools that leverage off Yuho's logical core.

Getting into the specifics, Yuho provides the following three products.

1. [Yuho](doc/syntax.md), a DSL made to be readable and codeable by lawyers
2. [Formalised semantic](tests/) for legal reasoning modelled after the syntactical patterns of the law
3. [Transpiler](src/secondary/) that transpiles to the below targets

### Output formats

| Target | Usage |
| :--- | :--- |
| JavaScript | browser simulations and extensions |
| JSON | REST APIs |
| R | data modelling and visualisation |
| Alloy | formal verification |
| Whiley | decision logic |
| F* | proof backends |

## Documentation

* [Language specification](doc/syntax.md)
* [Grammer specification](grammer/)
* [Formal verification](tests/)
* [Examples](example/)

## Scope

Development is currently scoped by the following statutes as specified [here](doc/scope.md). 

## Usage

### CLI 

```console
$ git clone https://github.com/gongahkia/yuho
$ cd yuho  
$ make config
$ make build
```

## Contribute

Yuho is open-source. Contribution guidelines are found at [CONTRIBUTING.md](admin/CONTRIBUTING.md).

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
