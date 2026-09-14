# Actor-scoped section 84 research POC

[actor-scoped-section84.yh](actor-scoped-section84.yh) authors one Penal Code s 84 general-exception definition and three explicit attachment instances. It combines the bounded theft candidate under ss 378–379, intentional-aid participation under ss 107–109, and direct theft attempt under s 511. All [scenarios](scenarios/) use opaque synthetic actor IDs and externally supplied classifications. The Haskell frontend and in-process kernel perform a technical analysis only.

From the repository root:

```sh
(cd rewrite/haskell && cabal v2-build exe:yuho --offline --jobs=1)
YUHO=$(cd rewrite/haskell && cabal list-bin exe:yuho --offline)
MODEL=research/singapore/actor-exception-pilot/actor-scoped-section84.yh
SCENARIO=research/singapore/actor-exception-pilot/scenarios/07_abettor_ignores_principal.yh
"$YUHO" check "$MODEL"
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

The definition is actor-parameterised and its reviewed proposition structure is authored once: unsoundness at the relevant act time, three alternative incapacity routes, route-specific causation, and both wrongfulness components in one conjunction. Evidence Act s 107's defence-side legal burden and balance-of-probabilities standard are contextual annotations; they do not classify evidence.

```yh
general-exception x:section84 subject subject:actor rule r:section84 program p:section84 path section84 sections 84 {
  // eight primitive classifications and the reviewed all/any route graph
}
attach x:section84 to offence o:theft for role:principal context principal-conduct as xi:principal-section84;
attach x:section84 to participation p:intentional-aid for role:alleged-abettor context aid-conduct as xi:abettor-section84;
attach x:section84 to attempt attempt:theft for role:alleged-attempter context attempt-conduct as xi:attempter-section84;
```

The closed target and context types prevent attaching the principal instance to the aid or attempt branch. A scenario selects one target, binds three distinct synthetic actors, acknowledges the declared research-scope assumptions, and supplies classifications under the selected instance:

```yh
analyse p:intentional-aid;
bind role:alleged-abettor to actor:participant-1;
exception-status xi:abettor-section84 f:unsoundness-time by actor:participant-1 context aid-conduct = not_proved;
```

`observe xi:principal-section84;` permits the scenario to include a complete, separately attributed principal classification set for isolation checks. It does not attach that instance to the selected branch. The selected kernel result remains unchanged, and the nonselected rule is not evaluated as an independent legal conclusion. To inspect another actor's technical branch, select that branch in a separate scenario. Unqualified, inactive, wrong-actor and wrong-context section 84 classifications fail checking. The compiler derives distinct canonical leaf IDs for each typed attachment instance while retaining authored IDs in `explain`.

For the example scenario, `explain` identifies `p:intentional-aid`, `actor:participant-1`, the `xi:abettor-section84` attachment and `aid-conduct` context. It reports `xi:principal-section84` as supplied for observation but not affecting the selected branch. The final technical status is `satisfied`; it does not assert a court outcome. [ActorExceptionSurfaceChecks.hs](../../../rewrite/haskell/test/ActorExceptionSurfaceChecks.hs) covers 16 decision cases, including independent unresolved inputs, and 16 source-located refusals.

This bounded POC does not assess evidence or diagnose unsoundness, decide which statutory expression applies, transfer a principal's section 84 position to an alleged abettor, resolve broader s 108 cases, decide the attempt conduct stage, or impose punishment. The theft dishonesty classification and all section 84 classifications are supplied. The output is not legal advice or a finding of guilt, conviction, acquittal, liability, sentence or court disposition.
