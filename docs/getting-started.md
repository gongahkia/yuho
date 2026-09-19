# Haskell Yuho Research Language v1.0.0

Yuho v1 is a formally founded, executable research DSL and holistic representational framework for Singapore criminal law. It completely indexes the repository's saved 524-row Penal Code export and provides a broad, expressly partial executable subset. It is not legally authoritative, does not establish legal currency, does not assess evidence and produces no guilt, liability, conviction, acquittal, sentence or court disposition.

## Ten-minute tour

Build with the pinned compiler and no network access:

```sh
cabal v2-build all --offline -j1 --with-compiler=/home/gongahkia/.ghcup/bin/ghc-9.8.4
YUHO="$(cabal list-bin exe:yuho --offline --with-compiler=/home/gongahkia/.ghcup/bin/ghc-9.8.4)"
"$YUHO" version
"$YUHO" doctor --root ../..
"$YUHO" init /tmp/yuho-research-tour
cd /tmp/yuho-research-tour
"$YUHO" check model.yh --scenario scenario.yh
"$YUHO" compile model.yh --scenario scenario.yh > request.json
"$YUHO" run model.yh --scenario scenario.yh
"$YUHO" explain model.yh --scenario scenario.yh
"$YUHO" diagram model.yh --scenario scenario.yh --view trace --format svg --output trace.svg
```

The normal executable path is Haskell-only. Python, Mermaid, Graphviz, Node, a browser and the network are not required.

## Architecture and language

The authoritative pipeline is authored `.yh`, source-located Haskell AST, exact-version module resolution, static checking, normalized Core Yuho, KernelInput v1 lowering, one of eight in-process kernel variants, and technical result/explanation/diagram output.

Core v0.1 covers three-valued requirements, definitions, offences, actor-scoped general exceptions, participation, attempt, presumptions, temporal selection, penalties and independent allegations. Core v0.2 adds nominal entities, typed predicates and exact scalars, explicit negation, finite quantifiers, cardinality and explicit finite rule priority. Core v0.3 adds bounded normative positions, rich candidate-sanction surface forms and explicitly authored responsibility routes. See the [language reports](formal-semantics.md), [v0.2](formal-semantics.md) and [v0.3](formal-semantics.md).

Norms use this bounded form:

```yh
norm n:prohibition subject actor:alex modality prohibited
  action proposition p:specified-action when q:acts
  citation "fictional prohibition";
priority n:prohibition over n:permission;
```

Responsibility is never inferred from shared facts:

```yh
responsibility-route route:aid subject actor:blair kind intentional-aid
  target proposition p:responsibility-route when q:aid
  citation "fictional contribution route";
```

Supported route tags are `principal-conduct`, `joint-conduct`, `instigation`, `conspiracy`, `intentional-aid`, `attempt` and explicitly named `other:<identifier>` contributions. Each is only an authored tag plus a finite requirement; it carries no hidden doctrine.

Candidate sanctions support term imprisonment, exact SGD decimal-string fines evaluated without floating point, death, life imprisonment, bounded caning and `all-of`, `exactly-one-of` or `one-or-more-of` trees. They are candidate statutory presentations, never imposed sentences. Forfeiture, disqualification and judicial sentencing calculus are deferred.

## Stable command surface

| Command | Release status |
|---|---|
| `yuho check` | supported |
| `yuho compile` | supported; stdout or atomic `--output` |
| `yuho run` | supported; Haskell kernel in process |
| `yuho explain` | supported technical derivation |
| `yuho diagram` | supported native SVG/JSON |
| `yuho corpus` | supported offline coverage queries |
| `yuho doctor` | supported release/environment report |
| `yuho init` | supported atomic starter creation |
| `yuho version` | supported |
| `yuho release verify` | supported offline manifest verification |
| `yuho fmt` | deliberately not shipped |

The lexer currently discards comments. A complete v1 formatter therefore could not meet the required comment-preservation guarantee, and shipping a partial formatter would risk damaging authored models. This is an explicit limitation rather than a hidden legacy-Python fallback.

## Kernel and schemas

The eight variants are `ClosedBooleanBranches-v1`, `AcyclicGuardedExceptions-v1`, `TypedBooleanFacts-v1`, `GuardedPenaltySelection-v1`, `PenaltyTerms-v1`, `SuppliedProofStatus-v1`, `RegisteredPresumptionDerivations-v1` and `TypedFiniteRules-v1`. KernelInput v1, KernelResult v1 and Canonical IR v1.2 remain unchanged. The frozen version index is `release/schema-versions-v1.0.json`.

## Mechanisation and assurance

Core v0.1-v0.3 contain 79 registered Lean theorems: 43 v0.1, 25 v0.2 and 11 v0.3. The independent retained Haskell–Lean conformance corpora contain 95, 2,518 and 33 vectors respectively. This is a machine-checked theorem boundary and bounded implementation comparison, not a verified parser or compiler and not proof of legal correctness.

The trusted computing base and exclusions are detailed in the three mechanisation reports. Native diagrams and module filesystem resolution are tested rather than proved. The release manifest makes the retained evidence reproducible offline:

```sh
yuho release verify --root /path/to/yuho
```

## Singapore research corpus

The canonical coverage artifact classifies every saved Penal Code row exactly once. The release retains 26 executable offence families, 13 general-exception families, 22 candidate-penalty declarations, 306 valid Singapore scenarios and 16 cases. Fifty-five Penal Code rows connect to executable models; the contextual Evidence Act s 107 anchor brings the instrument/provision total to 56. Structural presence does not mean executable support, legal review or current law.

```sh
yuho corpus summary --corpus-root /path/to/yuho
yuho corpus list --category property-and-deception --corpus-root /path/to/yuho
yuho corpus show penal-code:84 --corpus-root /path/to/yuho
yuho corpus check --corpus-root /path/to/yuho
```

The defensible release stays below aspirational 30-family, 75-anchor, 350-scenario and 20-case figures. Reaching those numbers from the saved material would require interpretation, procedural semantics or shallow duplication. The generated [gap audit](roadmap.md) leaves those rows visible.

## Positioning

Yuho shares L4/Core L4's interest in explicit legal-rule structure, Catala's concern for reviewable legislative computation, OpenFisca's executable-policy orientation and Blawx's explainable rules. This repository does not claim feature parity or superiority: Yuho's distinctive release boundary is a finite Haskell criminal-law research language with machine-checked Core fragments, native diagrams and a saved Singapore structural/executable coverage distinction.

## Non-goals

- narrative-to-fact extraction or evidence credibility;
- automatic legal research, currency or transitional-law determination;
- exhaustive Singapore legislation or judicial interpretation;
- guilt, liability, conviction, acquittal, sentencing or criminal procedure;
- production registry/package distribution;
- full LSP or formatter parity with the archival Python product.

The legacy Python frontend and Mermaid exporters remain archival compatibility code. They are not the v1 authority or a dependency of the Haskell workflow.
