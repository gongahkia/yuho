# Reusable statutory definitions in the Haskell Yuho DSL

**Status:** bounded Singapore criminal-law research POC. The [authored model](../../research/singapore/section-84-pilot/statutory-definitions/section323-section379-definitions.yh) and its [synthetic scenarios](../../research/singapore/section-84-pilot/statutory-definitions/scenarios/01_hurt_pain.yh) are checked, compiled, run and explained entirely in Haskell. They do not determine a person's guilt or which statutory expression applies to real conduct.

The model declares a statutory definition with a type, section reference, primitive inputs, a named output and an `all` or `any` graph. A `use` is an **executable dependency**: its derived status contributes to the referring graph. The offence selects the definition explicitly:

```yuho
statutory-definition d:hurt kind hurt-result sections 319 {
  input result f:bodily-pain quote q:bodily-pain;
  input result f:disease quote q:disease;
  input result f:infirmity quote q:infirmity;
  any g:hurt (f:bodily-pain, f:disease, f:infirmity);
  output g:hurt;
}

offence o:voluntary-hurt rule r:section323-candidate program p:section323 path section323 sections 321,323 {
  use d:voluntarily-causing-hurt as voluntary-hurt;
  all g:section323-requirements (d:voluntarily-causing-hurt);
}
```

The section 321 definition uses `d:hurt` as an executable result dependency and separately accepts supplied classifications for the act, its causal relationship, and intention to cause hurt **or** knowledge that hurt was likely. `d:hurt` derives from bodily pain, disease or infirmity classifications; Yuho does not diagnose any of them. The section 323 candidate references the section 321 output instead of repeating that graph. The scenario must acknowledge that ss 323A and 334 are outside this bounded model.

The theft candidate uses `d:dishonestly`, which represents the bounded section 24 alternatives: intention to cause wrongful gain or wrongful loss, or an act dishonest by ordinary standards with knowledge of that character. `d:wrongful-gain` and `d:wrongful-loss` are separately authored bounded section 23 concepts. In this theft graph they are **mental-state targets**, not executable dependencies:

```yuho
mental-state f:intends-wrongful-gain kind intention
  target d:wrongful-gain as wrongful-gain quote q:intends-gain;
mental-state f:intends-wrongful-loss kind intention
  target d:wrongful-loss as wrongful-loss quote q:intends-loss;
use d:dishonestly as dishonesty;
```

The supplied intention classification does not prove an actual gain or loss. Likewise, merely naming `d:hurt` as the target of an intention does not prove that hurt occurred; the section 321 graph also executes its `use d:hurt`. The bounded section 23 definitions cover gain by unlawful means without entitlement and loss by unlawful means of entitled property. Other section 23 routes and explanations, the section 319 unconsciousness explanation, and the section 378 explanations are not separately executed. Theft still requires separately supplied movable-property, possession, consent, movement and movement-for-taking classifications. Section 379 punishment is not an imposed penalty.

One authored `x:section84` graph remains explicitly attached to both candidates. Its post-2022 unsoundness, route-specific causation, nature, conjunctive wrongfulness and control branches are unchanged from the [shared-exception POC](SINGAPORE-HURT-THEFT-SHARED-SECTION84-HASKELL-POC.md). Every scenario explicitly acknowledges the supplied post-2022 applicability assumption; the compiler does not select law by date. The section 107 accused-side legal burden and balance-of-probabilities standard remain contextual annotations, not evidence assessment or proof-status generation.

From the repository root:

```sh
cd rewrite/haskell
cabal v2-build exe:yuho --offline --jobs=1
YUHO_BIN="$(cabal list-bin exe:yuho)"
MODEL=../../research/singapore/section-84-pilot/statutory-definitions/section323-section379-definitions.yh
HURT=../../research/singapore/section-84-pilot/statutory-definitions/scenarios/01_hurt_pain.yh
THEFT=../../research/singapore/section-84-pilot/statutory-definitions/scenarios/10_theft_gain_intent.yh
"$YUHO_BIN" check "$MODEL"
"$YUHO_BIN" compile "$MODEL" --scenario "$HURT"
"$YUHO_BIN" run "$MODEL" --scenario "$THEFT"
"$YUHO_BIN" explain "$MODEL" --scenario "$THEFT"
```

The deterministic [theft explanation snapshot](../../research/singapore/section-84-pilot/statutory-definitions/snapshots/10_theft_gain_intent.txt) makes the distinction visible:

```text
Selected candidate offence: o:theft
Statutory definition: d:dishonestly — Penal Code s 24
Mental-state target: f:intends-wrongful-gain -> d:wrongful-gain (type-checked; not an executable dependency)
Referenced by: o:theft
Attachment: s 84 -> candidate o:theft
Final technical status: satisfied (candidate requirements technically satisfied; no section 84 defeat)
No guilt, conviction, acquittal or sentence was determined.
```

The [focused Haskell tests](../../rewrite/haskell/test/DefinitionSurfaceChecks.hs) exercise the three section 319 alternatives, section 321 fault alternatives, section 24 branches, unresolved inputs, section 84 defeat for both candidates, selected-definition closure and source-located graph failures. A scenario may assign primitive `f:` inputs only. It cannot override a derived `d:` or `g:` output, or supply a primitive used only by the unselected offence or an unreachable definition.

This is a single-program definition graph. It does not implement parties or participation, attempts, the omitted statutory explanations, evidence assessment, multiple legal expressions, or a judicial disposition. Hashes of compiled requests identify bytes only; they do not establish legal currency, source authenticity or correctness for a real case.
