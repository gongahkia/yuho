# Yuho Haskell Research Language v0.1 — start here

This directory is the shortest route into the bounded Haskell-authoritative Singapore criminal-law research release. Yuho evaluates authored requirement graphs against synthetic supplied classifications. It does not assess evidence, determine guilt, choose legally applicable law, impose a sentence or make a court disposition.

From `rewrite/haskell`:

```sh
PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal v2-build all --offline --jobs=1
YUHO="$(PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal list-bin exe:yuho)"
MODEL=../../research/singapore/research-release/modular-singapore-criminal-law-release.yh
SCENARIO=../../research/singapore/research-release/scenarios/misappropriation/01_satisfied_primary.yh
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

Then run the three showcase cases:

```sh
"$YUHO" explain ../../research/singapore/research-release/case-property-deception-showcase.yh
"$YUHO" explain ../../research/singapore/research-release/case-person-harm-showcase.yh
"$YUHO" explain ../../research/singapore/abetment-routes-pilot/case-modular-warehouse-shared.yh
```

The modular release imports seven independently authored source graphs from [`modules/`](modules/). Its equivalent monolithic graph is [`singapore-criminal-law-release.yh`](singapore-criminal-law-release.yh). The 56 decision-covering scenario files exercise satisfied, not-satisfied, unresolved and exception-defeat paths for seven new offence families.

The authoritative syntax guide is [`HASKELL-YUHO-DSL-GUIDE.md`](../../../docs/rewrite/HASKELL-YUHO-DSL-GUIDE.md). The release capability matrix is [`HASKELL-RESEARCH-RELEASE-v0.1.md`](../../../docs/rewrite/HASKELL-RESEARCH-RELEASE-v0.1.md).
