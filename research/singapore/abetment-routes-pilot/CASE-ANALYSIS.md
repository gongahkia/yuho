# Three-issue Singapore research case

The [authored case](case-warehouse.yh) uses the [bounded theft, s 107 abetment and s 511 attempt model](section107-routes-theft.yh). It names one principal, alleged abettor, co-conspirator and alleged attempter, then supplies a separate synthetic classification block for each allegation. The model authors one section 84 definition and three explicit actor-scoped attachments; the case does not create new attachments.

```yh
analysis-case case:warehouse-incident model "section107-routes-theft.yh" {
  bind role:principal to actor:principal-1;
  bind role:alleged-abettor to actor:participant-1;
  bind role:co-conspirator to actor:co-1;
  bind role:alleged-attempter to actor:attempt-actor-1;

  allegation a:principal-theft analyse offence o:theft for role:principal {
    // scoped assumptions, actor-attributed inputs and principal s 84 inputs
  }
  allegation a:abet-theft analyse participation p:abet-theft
    for role:alleged-abettor {
    // separate s 107 route, s 109 consequence and abettor s 84 inputs
  }
  allegation a:attempt-theft analyse attempt attempt:theft
    for role:alleged-attempter {
    // target-directed intention, supplied stage and attempter s 84 inputs
  }
}
```

From the repository root, after the pinned offline build:

```sh
cd rewrite/haskell
cabal v2-build exe:yuho --offline --jobs=1
YUHO=$(cabal list-bin exe:yuho)
CASE=../../research/singapore/abetment-routes-pilot/case-warehouse.yh
"$YUHO" check "$CASE"
"$YUHO" compile "$CASE"
"$YUHO" run "$CASE"
"$YUHO" explain "$CASE"
```

`compile` emits canonical `yuho.case-input/v0.1` JSON containing three separately checked KernelInput requests. `run` calls the existing Haskell kernel in process for each request and emits canonical `yuho.case-result/v0.1` JSON. Both formats list issues in offence, participation, attempt order regardless of declaration order. Each issue retains its own technical status and trace. There is no case-level status or court outcome.

The case model must be a sibling `.yh` file. `SFE106` rejects malformed case shape or an unsafe model reference, `SFE107` rejects a mismatched typed target or role, and `SFE108` reports an unexpected checked-request or kernel failure. Existing source-located actor, scope and assignment diagnostics apply within each allegation.

In this synthetic case the principal theft and bounded abetment branches are technically satisfied. The attempt branch is not satisfied because the scenario supplies `preparation_only`; Yuho does not classify conduct. Changing one actor's section 84 classifications changes only that actor's issue request and result. The s 107 route status and supplied s 109 consequence remain distinct inside the abetment issue.

This is a bounded research example. It uses one existing local sibling model and exactly one allegation of each closed kind. It does not resolve competing allegations, infer facts, assess evidence, decide statutory applicability, calculate punishment or produce an aggregate legal conclusion. Actor identities are opaque synthetic IDs, and every scope acknowledgement is supplied rather than inferred.
