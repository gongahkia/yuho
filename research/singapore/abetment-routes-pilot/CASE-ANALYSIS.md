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

The [shared-fact case](case-warehouse-shared.yh) supplies synthetic classifications once and binds them explicitly to compatible primitive inputs. It leaves other classifications local to their allegations:

```yh
supplied-fact fact:principal-movement kind conduct subject actor:principal-1
  status proved reason "synthetic movement classification";
supplied-fact fact:principal-unsoundness kind circumstance
  subject actor:principal-1 instance xi:principal-section84
  context principal-conduct status not_proved
  reason "synthetic principal classification";

allegation a:principal-theft analyse offence o:theft for role:principal {
  bind-fact fact:principal-movement to input f:property-moved;
  bind-fact fact:principal-unsoundness
    to exception-input xi:principal-section84 f:unsoundness-time;
  // other local classifications and scope acknowledgements
}
allegation a:abet-theft analyse participation p:abet-theft
  for role:alleged-abettor {
  observe xi:principal-section84;
  bind-fact fact:principal-unsoundness
    to exception-input xi:principal-section84 f:unsoundness-time;
  // all other observed-instance inputs remain explicitly supplied
}
```

The initial closed fact kinds are `conduct`, `circumstance`, `mental-state` and `relationship`. A relationship fact names bound `from` and `to` actors plus its target offence. A section 84 fact also names the exact attachment instance and act context. Classifications are `proved`, `not_proved` or `unresolved(not_determined)` / `unresolved(external_decision_pending)` with a separate human-readable supplied reason. An unresolved reason code is required; an attempt `conduct-stage` remains a different type and cannot be bound as a proof fact.

The [mixed-result case](case-warehouse-shared-mixed-three.yh) supplies an attempt intention with `subject actor:attempt-actor-1 target o:theft`; the target must match the authored attempt target. This target reference does not supply completed theft elements.

`bind-fact` works only with a checked primitive input of the selected allegation. `input`, `relation-input` and `exception-input` identify three distinct input types. Matching names alone bind nothing. Yuho checks kind, subject actor, relation endpoints and target, and section 84 instance and act context before expanding the supplied status into the same assignment a local classification would produce. Multiple bindings also require the same exact authored primitive category and source quote (or typed relation quote); a movement classification cannot simultaneously supply the distinct “movement in order to taking” requirement. Binding to a route, statutory or offence result, scope acknowledgement, contextual annotation, attempt stage or another fact is rejected. A direct local classification cannot also bind the same input. The author asserts that the same supplied proposition belongs at every binding; structural type checking does not establish factual or doctrinal equivalence. The s 107 abetment issue does not treat completed principal theft as an executable prerequisite; a principal-theft technical result cannot be transferred into it.

To run the shared case from `rewrite/haskell`, set `CASE=../../research/singapore/abetment-routes-pilot/case-warehouse-shared.yh` and use the four commands above. `explain` lists each supplied fact, its actor and classification, every binding, and the three independent results. Yuho does not assess evidence or determine a fact. Shared cases add a typed `supplied_facts` array to the frontend-owned canonical case input and result; the array is omitted from the unchanged direct-only case, preserving its exact bytes. Eight shared examples in this directory, including the [declaration-order variant](case-warehouse-shared-order.yh) and a [fully fact-bound principal issue](case-warehouse-shared-all-principal.yh), cover proved, not-proved and unresolved statuses, actor isolation and mixed three-issue results; the Haskell tests compare every one with equivalent direct classifications.

The case model must be a sibling `.yh` file. `SFE106` rejects malformed case shape or an unsafe model reference, `SFE107` rejects a mismatched typed target or role, and `SFE108` reports an unexpected checked-request or kernel failure. `SFE109`–`SFE118` cover fact-only syntax, unknown or duplicate facts, kind and subject incompatibility, unavailable inputs, binding conflicts, unused facts, incompatible multiple destinations and incomplete expanded assignments. Existing source-located actor, scope and assignment diagnostics apply within each allegation.

In this synthetic case the principal theft and bounded abetment branches are technically satisfied. The attempt branch is not satisfied because the scenario supplies `preparation_only`; Yuho does not classify conduct. Changing one actor's section 84 classifications changes only that actor's issue request and result. The s 107 route status and supplied s 109 consequence remain distinct inside the abetment issue.

This is a bounded research example. It uses one existing local sibling model and exactly one allegation of each closed kind. It does not resolve competing allegations, infer facts, assess evidence, decide statutory applicability, calculate punishment or produce an aggregate legal conclusion. Actor identities are opaque synthetic IDs, and every scope acknowledgement is supplied rather than inferred.
