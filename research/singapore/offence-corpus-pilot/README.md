# Cheating and mischief Haskell research POC

[`modular-cheating-mischief.yh`](modular-cheating-mischief.yh) imports an exact local module whose checked graph contains two distinct Penal Code candidate families. The s 415 cheating expression preserves a common deception requirement and separates the property delivery/retention form from the intentional act-or-omission and harm form. The s 425 mischief expression separates intention/knowledge from destruction/injurious property change. One bounded post-2022 s 84 definition is explicitly attached to each candidate.

The 20 files under [`scenarios`](scenarios) cover independently meaningful satisfied, not-satisfied, unresolved and s 84-defeated paths. [`cheating-property-form.txt`](snapshots/cheating-property-form.txt) and [`mischief-knowledge-change.txt`](snapshots/mischief-knowledge-change.txt) are representative Haskell `explain` snapshots.

Sections 417 and 426 contribute only saved candidate terms: imprisonment up to three or two years respectively, fine, or both. `one-or-more-of` expresses the statutory alternatives. A selected candidate remains separate from the technical offence/exception result and is not a sentence.

Run from the repository root after building `rewrite/haskell`:

```sh
YUHO="$(cd rewrite/haskell && PATH=/home/gongahkia/.ghcup/bin:/usr/bin:/bin cabal list-bin exe:yuho)"
MODEL=research/singapore/offence-corpus-pilot/modular-cheating-mischief.yh
SCENARIO=research/singapore/offence-corpus-pilot/scenarios/mischief/02_knowledge_change_satisfied.yh
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

The saved material does not support treating the implemented expressions as complete cheating or mischief doctrine. Sections 24–25, explanations, illustrations, aggravated provisions, other exceptions, temporal applicability and sentencing discretion remain contextual or deferred. All scenarios are synthetic supplied classifications; Yuho does not assess a person, evidence or a proceeding.
