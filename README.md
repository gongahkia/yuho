![](https://img.shields.io/badge/yuho_1.0-WIP-orange)

# `yuho`

Yuho is a domain-specific language providing a programmatic representation of Singapore Criminal Law.

Development is currently scoped by the [Penal Code 1871](https://sso.agc.gov.sg/Act/PC1871).

## Rationale

> [!WARNING]
> To add more here later

## Documentation

* [Grammer specification](grammer)
* [Language specification](doc/syntax.md)
* [Example](example)

## Usage

### CLI 

```console
$ git clone https://github.com/gongahkia/yuho
$ cd yuho  
$ make config
$ make build
```

## Contribute

Yuho is open-source! For contribution guidelines, refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## References

### Analogues

Yuho takes much inspiration from the following projects.

* [Catala](https://github.com/CatalaLang): Language syntax that explicitly mimicks logical structure of the Law, focused on general Socio-fiscal legislature in most jurisidictions.
* [Natural L4](https://github.com/smucclaw/dsl): Language with an English-like syntax that transpiles to multiple targets, focused on codification of contracts and Singapore Contract Law.

### Research

* [A Logic for Statutes](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088206) by Sarah B Lawsky
* [Law and logic: A review from an argumentation perspective](https://www.sciencedirect.com/science/article/pii/S0004370215000910) by Henry Prakken, Giovanni Sartor
* [Defeasible semantics for L4](https://ink.library.smu.edu.sg/cclaw/5/) by Guido Governatori, Meng Weng Wong
* [CLAWs and Effect](https://www.lawsociety.org.sg/publication/claws-and-effect/) by Alexis N Chun
