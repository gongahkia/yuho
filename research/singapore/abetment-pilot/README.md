# Bounded intentional-aid theft research POC

The [authored Yuho model](intentional-aid-theft.yh) analyses a synthetic principal's bounded theft requirements and a separate alleged abettor's intentional aid. It uses the Haskell frontend and `SuppliedProofStatus-v1`; every primitive classification comes from a [synthetic scenario](scenarios/01_aid_by_act.yh). The model is a Singapore criminal-law research POC, not a finding about a person or a court outcome.

The Penal Code 1871 snapshot saved with the earlier section 84 research supplied the bounded text: s 107(1)(c) describes intentional aid by an act or illegal omission; s 107 Explanation 2 addresses facilitation; s 108 and its explanations require care about the capacity and mental state of the person abetted; and s 109 addresses an act committed in consequence of abetment where no express punishment provision is made. The model restricts the target to separately supplied requirements for theft under ss 378–379. It does not assert that this restriction is a general legal rule about abetment. Instigation, conspiracy, broader s 108 situations, other target offences, punishment, and actor-specific general exceptions are outside this POC.

The saved ss 23–24 definition chain gives the principal's `d:dishonestly` output. A mental-state target such as `d:wrongful-gain` identifies the concept intended; it does not assert that actual gain occurred. The target offence's movable property, possession, consent, movement and dishonest-intention classifications remain external. Every section used in this bounded graph has a typed instrument and source reference. The Evidence Act 1893 s 107 citation is distinct from Penal Code 1871 s 107 and remains contextual; it does not classify proof or establish this aid route.

The key authoring constructs are:

```yuho
party-role role:principal;
party-role role:alleged-abettor;

relation rel:aid from role:alleged-abettor to role:principal
  target o:theft status f:aid-link quote q:aid-link;
any g:aid-form (f:aid-by-act, f:aid-by-illegal-omission);
all g:intentional-aid (f:intends-aid, f:aid-link, g:aid-form);
all g:section109 (g:theft-requirements, g:intentional-aid, f:consequence);
```

The scenario binds opaque synthetic actors and acknowledges each research-scope restriction. An actor-attributed mental state cannot substitute for a different actor's mental state:

```yuho
analyse p:intentional-aid;
bind role:principal to actor:principal-1;
bind role:alleged-abettor to actor:participant-1;
f:intends-aid by actor:participant-1 = proved;
rel:aid from actor:participant-1 to actor:principal-1 = proved;
```

From the repository root, with the Haskell executable built offline:

```sh
cd rewrite/haskell
cabal v2-build exe:yuho --offline --jobs=1
yuho_bin=$(cabal list-bin exe:yuho --offline)
model=../../research/singapore/abetment-pilot/intentional-aid-theft.yh
scenario=../../research/singapore/abetment-pilot/scenarios/01_aid_by_act.yh
"$yuho_bin" check "$model" --scenario "$scenario"
"$yuho_bin" compile "$model" --scenario "$scenario" > /tmp/yuho-abetment-request.json
"$yuho_bin" run "$model" --scenario "$scenario"
"$yuho_bin" explain "$model" --scenario "$scenario"
```

The decision-covering scenarios include [aid by act](scenarios/01_aid_by_act.yh), [illegal omission](scenarios/02_illegal_omission.yh), separately failed principal and alleged-abettor requirements, failed consequence, and reasoned unresolved inputs. The [explanation snapshot](snapshots/01_aid_by_act.txt) shows the actor groups and relation direction. The output is a technical `satisfied`, `not_satisfied`, or `unresolved` result from supplied classifications; `not_proved` does not assert factual falsity, and no result is guilt, liability, conviction, acquittal, or a sentence.

Required scope acknowledgements cover the unmodelled express-punishment inquiry, the intentional-aid-only route, separately supplied principal theft requirements, broader s 108 cases, punishment exclusion, and supplied statutory expression. They are neither kernel facts nor defaults. The Haskell frontend currently lacks general actor-specific exception attachment, other abetment routes, and a more general target-offence participation abstraction.
