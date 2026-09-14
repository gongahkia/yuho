# Typed Penal Code s 107 abetment routes — research POC

[The authored model](section107-routes-theft.yh) contains three closed routes to a bounded s 107 technical status. The locally saved Penal Code text describes direct instigation in s 107(1)(a), engagement in a conspiracy with an act or illegal omission in pursuance and in order to the thing in s 107(1)(b), and intentional aid by act or illegal omission in s 107(1)(c). The [synthetic scenarios](scenarios/) supply the classifications; Yuho does not infer any relationship, intention, conduct stage, or factual truth. This is a research POC, not a court finding.

The key declaration is readable as legal structure rather than a JSON request:

```yh
abetment p:abet-theft actor role:alleged-abettor target o:theft
  principal role:principal rule r:section109-candidate
  program p:section109 path section109 sections 107,108,109 {
  instigation route route:instigation {
    relation rel:instigates from role:alleged-abettor to role:principal
      target o:theft status f:instigation-link quote q:instigation;
  }
  conspiracy route route:conspiracy with role:co-conspirator {
    relation rel:agreement from role:alleged-abettor to role:co-conspirator
      target o:theft status f:agreement-link quote q:agreement;
    conduct conduct:pursuant actor role:co-conspirator {
      element pursuant-act f:pursuant-act quote q:pursuant-act;
      element pursuant-illegal-omission f:pursuant-omission quote q:pursuant-omission;
      any g:pursuant-form (f:pursuant-act, f:pursuant-omission);
    }
    element causation f:pursuance-link quote q:pursuance;
    all g:conspiracy (f:agreement-link, g:pursuant-form, f:pursuance-link);
  }
  // the intentional-aid route separately requires intention, aid relation,
  // and an act or illegal omission; it remains authored in the model.
  any g:section107-routes (f:instigation-link, g:conspiracy, g:intentional-aid);
  relation rel:consequence from role:alleged-abettor to role:principal
    target o:theft status f:consequence quote q:consequence;
  element consequence f:consequence quote q:consequence;
  all g:section109 (g:section107-routes, f:consequence);
}
```

The s 107 `any` status and the separate s 109 candidate-consequence status are observable technical nodes. An s 107 route does not require completed theft; the s 109 branch separately requires the supplied consequence classification and an explicit no-express-punishment-provision scope acknowledgement. The model does not choose punishment. The bounded theft offence remains an explicit target reference, not an automatic prerequisite in the s 107 tree. This restriction does not state a general rule about s 108.

The model declares a principal, alleged abettor, co-conspirator and alleged attempter. Scenarios bind distinct opaque actor IDs. Directed relation statuses are supplied using those endpoints, while the co-conspirator's pursuant act or illegal omission is actor-attributed. The reusable section 84 definition is authored once and explicitly attached to the principal offence, the overall alleged-abettor branch, and the separate attempt branch. Each attachment has its own actor and act context; a scenario may `observe` another instance without attaching it to the selected branch. Evidence Act s 107 is a contextual burden annotation, distinct from Penal Code s 107 abetment.

From the repository root, after the pinned offline Haskell build:

```sh
(cd rewrite/haskell && cabal v2-build exe:yuho --offline --jobs=1)
YUHO=$(cd rewrite/haskell && cabal list-bin exe:yuho --offline)
MODEL=research/singapore/abetment-routes-pilot/section107-routes-theft.yh
SCENARIO=research/singapore/abetment-routes-pilot/scenarios/08_conspiracy_act.yh
"$YUHO" check "$MODEL" --scenario "$SCENARIO"
"$YUHO" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO" run "$MODEL" --scenario "$SCENARIO"
"$YUHO" explain "$MODEL" --scenario "$SCENARIO"
```

The 24 scenarios cover each route's satisfied, not-proved and unresolved states; both conspiracy conduct forms; failed agreement, conduct and pursuance; a failed s 109 consequence despite a satisfied s 107 route; two routes satisfied together; and actor-scoped section 84 defeat and isolation. For example, `05_consequence_not_proved` has a satisfied s 107 instigation status but a not-satisfied s 109 candidate status. `07_instigation_principal_isolation` supplies an observed principal s 84 nature route; the alleged abettor's branch remains satisfied. The principal and attempter's observed section 84 classifications are never the abettor's inputs.

Frozen explanations show [instigation](snapshots/01_instigation_established.txt), [conspiracy by act](snapshots/08_conspiracy_act.txt), [intentional aid](snapshots/17_aid_by_act.txt), and [section 84 defeat of intentional aid](snapshots/15_aid_abettor_section84.txt).

The model excludes deemed instigation by concealment or misrepresentation, substantive criminal conspiracy, broader s 108 situations, other target offences, proof or evidence assessment, legal selection of an applicable statutory expression, guilt, conviction, acquittal, liability and imposed punishment. Every status is a technical result from synthetic classifications. The saved snapshot has not been authenticated as current law by this POC, and no output is a judicial determination.
