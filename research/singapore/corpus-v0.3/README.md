# Singapore Criminal Law Research Corpus v0.3

Start with [`modular-singapore-criminal-law-corpus-v0.3.yh`](modular-singapore-criminal-law-corpus-v0.3.yh). It composes 15 independently authored, exact-version local modules. The repository-wide [corpus index](../CORPUS-INDEX.md) combines these families with the 11 retained Haskell families and derives all published counts from the canonical coverage JSON.

From `rewrite/haskell`:

```sh
PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal v2-build exe:yuho --offline --jobs=1
YUHO="$(PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal list-bin exe:yuho)"
MODEL=../../research/singapore/corpus-v0.3/modular-singapore-criminal-law-corpus-v0.3.yh
SCENARIO=../../research/singapore/corpus-v0.3/scenarios/forgery/01_satisfied_primary.yh
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

The eight scenario files per family are a decision matrix: primary and alternative satisfaction, conduct/consequence failure, fault/circumstance failure, unresolved material input, established exception, unresolved exception, and an exception alongside an already failed offence. They are synthetic supplied classifications, not evidence findings.

The `showcases/` directory uses Core Yuho v0.2 typed finite rules for supplied age values, group cardinality, quantified property relations and an exact SGD minor-unit comparison. These are separate technical programs because the typed-finite kernel boundary does not silently change the historical offence requests.

The four `case-*.yh` files contain ordered independent allegations. Shared primitive facts are explicit and typed; exception classifications do not transfer between actors or allegations. Every case has no aggregate status.

The generated `graphs/penal-code-inventory.json` covers all 524 saved provision rows. The retained SVGs are bounded chapter/category views. They show structural references and coverage classes, not legal applicability or judicial results.

Limits are deliberate: source applicability is authored, open-textured facts are supplied, caning and tiered predicate-offence penalties are contextual, and several offence graphs cover only a stated branch. Yuho does not assess evidence or determine guilt, conviction, acquittal, liability, sentence or court disposition.
