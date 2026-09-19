# Singapore Criminal Law Research Corpus v0.3

This index is generated from [`SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json`](SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json) by `scripts/generate_singapore_corpus_v03.py`. Edit the generator and canonical coverage inputs, not the counts below.

Structural indexing, executable research coverage and legal review are separate. The saved Penal Code export does not determine legal currency. Every execution uses authored assumptions and externally supplied classifications; Yuho does not assess evidence or determine guilt, conviction, acquittal, liability, sentence or court disposition.

## Inventory summary

- Saved Penal Code provision rows: **524**.
- Executable offence families: **26** (15 added in v0.3).
- Valid Singapore scenario files: **306** (129 added in v0.3: 120 offence scenarios and 9 typed-rule showcases).
- Executable general-exception families: **13**.
- Candidate-penalty declarations: **21**.
- Analysis cases: **16**.

Counts use distinct authored family identities, file-based valid scenarios, distinct exception definitions and distinct candidate declarations. Repeated statuses, parser refusals, raw statute files and contextual citations do not increase these totals.

### Coverage classification

| Classification | Provisions |
|---|---:|
| `definition_only` | 55 |
| `executable_partial` | 24 |
| `executable_research` | 31 |
| `saved_source_unmodelled` | 414 |

### Subject category

| Category | Provisions |
|---|---:|
| `attempt` | 2 |
| `currency-stamps-and-measures` | 12 |
| `documents-records-and-identity` | 28 |
| `general-exceptions` | 33 |
| `general-part` | 54 |
| `human-body` | 122 |
| `intimidation-nuisance-and-reputation` | 9 |
| `participation` | 18 |
| `preliminary` | 7 |
| `property-and-deception` | 76 |
| `public-health-safety-and-nuisance` | 31 |
| `public-order` | 18 |
| `public-servants-and-justice` | 73 |
| `punishments` | 10 |
| `state-and-armed-forces` | 31 |

Chapter counts are available through `yuho corpus summary` and the canonical JSON. Chapter assignments are bounded section-range classifications because the saved export omits chapter-heading records.

## New executable families

| Family | Provision anchors | Scenarios | Attached exception | Candidate penalty | Executable boundary |
|---|---|---:|---|---|---|
| unlawful-assembly-membership | s 141, s 142, s 143 | 8 | section76 | s 143 candidate | The qualifying common object is externally supplied; Yuho does not infer it from group conduct. |
| rioting | s 141, s 146, s 147 | 8 | section76 | none (unsupported form) | Caning stated by section 147 is contextual because the candidate-term fragment does not encode caning. |
| false-information-public-servant | s 182 | 8 | section77 | s 182 candidate | The causal and public-servant power classifications are supplied rather than inferred. |
| obstructing-public-servant | s 186 | 8 | section76 | s 186 candidate | This branch is limited to section 186(1)(a), concerning an individual. |
| disappearance-of-evidence | s 201 | 8 | section78 | none (unsupported form) | Section 201's tiered penalty depends on the predicate offence and is not represented by the current candidate-term form. |
| obstruction-of-justice | s 204A | 8 | section77 | s 204A candidate | The tendency and course-of-justice classifications are supplied open-textured inputs. |
| public-nuisance | s 268, s 290 | 8 | section83 | s 290 candidate | Only the base section 290(a) fine branch is represented; knowledge and repeat-conviction branches are deferred. |
| culpable-homicide | s 299, s 304 | 8 | sections96-98-private-defence | none (unsupported form) | Section 304 has different terms for intention and knowledge routes, including forms the candidate-term fragment cannot express; no candidate penalty is selected for this combined offence graph. |
| rash-causing-death | s 304A | 8 | section85-involuntary-nature-route | s 304A candidate | This executable branch is rashness only; the separate negligent branch and its two-year maximum are indexed but deferred. |
| outraging-modesty | s 354 | 8 | section87 | s 354 candidate | The model is limited to subsection (1); caning and the subsection (2) child-victim branch are contextual. |
| cheating-by-personation | s 416, s 419 | 8 | section85-involuntary-nature-route | s 419 candidate | The underlying cheating classification is supplied; this model does not duplicate the complete section 415 graph. |
| forgery | s 463, s 465 | 8 | section78 | s 465 candidate | False-document status and the selected statutory intent are supplied classifications. |
| using-forged-record | s 471, s 465 | 8 | section76 | s 465 candidate | Section 471 applies section 465's manner of punishment; aggravated forgery provisions are not selected. |
| criminal-intimidation | s 503, s 506 | 8 | section94 | s 506 candidate | Only the base section 506 punishment branch is represented; aggravated threats are deferred. |
| defamation | s 499, s 500 | 8 | section94 | s 500 candidate | The ten statutory exceptions and their explanations are not expanded; non-application is an explicit supplied classification. |

The reusable v0.3 module host is [`corpus-v0.3/modular-singapore-criminal-law-corpus-v0.3.yh`](corpus-v0.3/modular-singapore-criminal-law-corpus-v0.3.yh). Each family has an exact-version manifest and independently authored source under `corpus-v0.3/modules/`. Eight scenarios per family cover established, alternative-route, material not-proved, unresolved and exception interactions.

## Core v0.2 showcases and cases

- `corpus-v0.3/showcases/typed-section83-age.yh`: supplied integer age comparison plus supplied maturity classification.
- `corpus-v0.3/showcases/typed-unlawful-assembly-cardinality.yh`: five typed people and a three-valued `at-least 5` group condition.
- `corpus-v0.3/showcases/typed-property-and-fine.yh`: finite existential property relation and exact SGD minor-unit comparison.
- Four v0.3 cases cover public order/justice, person/harm, documents/intimidation and actor-specific exception isolation. Allegations remain independent and cases have no aggregate status.

## Querying the corpus

```sh
yuho corpus summary
yuho corpus list --category property-and-deception
yuho corpus show penal-code:84
yuho corpus check
yuho corpus coverage --format json
yuho corpus graph --format json --output inventory.json
yuho corpus graph --category human-body --format svg --output human-body.svg
```

From another working directory, append `--corpus-root /path/to/yuho`. Complete inventory SVG output is intentionally refused above 120 nodes; use JSON or a chapter/category/provision filter.

## Coverage meanings

- `executable_research`: retained, runnable Haskell research model.
- `executable_partial`: runnable bounded expression with material doctrine explicitly omitted.
- `definition_only`: structurally identified definition or General Part concept, not a standalone offence result.
- `saved_source_unmodelled`: saved text indexed but not executable.
- `repealed_or_reserved`: only used when the saved structure expressly marks that state.

Review status is a separate field. A saved or executable row is not automatically qualified-reviewed. See [`../../docs/rewrite/CORE-YUHO-v0.3-LANGUAGE-GAPS.md`](../../docs/rewrite/CORE-YUHO-v0.3-LANGUAGE-GAPS.md) for the coarse language-gap audit.
