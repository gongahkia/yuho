# Bounded section 511 theft-attempt research POC

[section511-theft-attempt.yh](section511-theft-attempt.yh) authors one direct, single-actor attempt branch in the authoritative Haskell Yuho DSL. Its target is the bounded theft candidate under Penal Code ss 378–379, with the previously authored ss 23–24 definitions. The target is checked as a candidate offence and appears in explanations, but its completed-theft facts are not executable prerequisites for this attempt branch. All six [scenarios](scenarios/) use a fictional actor and externally supplied classifications.

From the repository root, build once with `(cd rewrite/haskell && cabal v2-build exe:yuho --offline --jobs=1)`, then run:

```sh
YUHO=$(cd rewrite/haskell && cabal list-bin exe:yuho --offline)
MODEL=research/singapore/attempt-pilot/section511-theft-attempt.yh
SCENARIO=research/singapore/attempt-pilot/scenarios/01_act_towards_commission.yh
"$YUHO" check "$MODEL"
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

The `.yh` model declares `party-role role:alleged-attempter`, an `offence o:theft` target, and a distinct typed attempt:

```yh
attempt attempt:theft route direct-self actor role:alleged-attempter target o:theft rule r:section511-candidate program p:section511 path section511 sections 511 {
  mental-state f:intends-target actor role:alleged-attempter kind intention target o:theft quote q:intends-target;
  conduct-stage stage:theft-conduct actor role:alleged-attempter output f:substantial-step quote q:substantial-step;
  all g:attempt-requirements (f:intends-target, f:substantial-step);
}
```

A separate scenario binds `role:alleged-attempter` to an opaque actor, supplies the intention proof status, and supplies exactly one typed conduct stage: `preparation_only`, `act_towards_commission`, or reasoned `unresolved`. Yuho maps those stage labels to `not_proved`, `proved`, and `unresolved` for the technical s 511 requirement while retaining the original label in Haskell metadata and `explain`. `not_proved` is not a finding that conduct was factually preparatory. The stage is an external classification of the bounded statutory **substantial-step** criterion; Yuho does not apply the s 511(2) “strongly corroborative” test or decide the preparation boundary from facts. The saved s 511 text does not define preparation as a separate stage. An actor's intention toward theft does not establish movement, dishonesty, absence of consent, or any other completed-theft element.

The saved Penal Code s 511(1) states intention and a substantial step toward commission; s 511(2) describes the substantial-step criterion, and s 511(3) addresses impossible attempts. This POC excludes impossible attempts, other-actor routes, abandonment, merger, offence-specific attempt provisions, proximity case law, and punishment. The separately acknowledged “no express attempt-punishment provision modelled” limitation concerns s 512's punishment structure; it is not an executable s 511 element and Yuho does not decide whether another provision applies. The scenario also explicitly acknowledges the direct-self route, uncompleted-target scope, punishment exclusion, supplied statutory expression, externally classified stage, and impossible-attempt exclusion. Missing acknowledgements fail checking.

The technical result is `satisfied`, `not_satisfied`, or `unresolved` from `SuppliedProofStatus-v1`. It is not a legal finding, evidence assessment, advice, conviction, acquittal, or sentence. [Snapshots](snapshots/) show deterministic actor-aware explanations. The remaining substantive language gap is actor-specific general-exception attachment: this POC does not evaluate section 84 for the alleged attempter or transfer another actor's status to this actor.
