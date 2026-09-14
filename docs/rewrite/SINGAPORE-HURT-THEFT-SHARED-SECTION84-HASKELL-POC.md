# Shared section 84 across two Singapore candidates

**Status:** Haskell-only research POC using synthetic supplied classifications. The [multi-offence Yuho model](../../research/singapore/section-84-pilot/multi-offence/section323-section379-with-section84.yh) defines the section 84 requirement graph once and explicitly attaches it to the bounded hurt and theft candidates. The existing [hurt-only fixture](../../research/singapore/section-84-pilot/hurt-offence/section323-with-section84.yh) and its request remain unchanged.

The saved Penal Code browser snapshot contains s 319's hurt definition, s 321's act and intention-or-knowledge structure, and s 323's candidate punishment clause subject to ss 323A and 334. It also contains s 378's definition of theft and s 379's punishment clause. This model supplies distinct classifications for movable property, another person's possession, absence of consent, dishonest intention to take, movement, and movement in order to the taking. The snapshot's s 24 definition of “dishonestly” and s 378's explanations are **not** decomposed here; dishonesty is classified externally under an explicit theft-scope assumption. No s 379 penalty terms are executed. These are authored research boundaries, not conclusions about a real event or current law.

The new syntax keeps typed statutory-section references, the definition and the two attachments separate:

```yuho
general-exception x:section84 rule r:section84 program p:section84 path section84 sections 84 {
  // typed unsoundness and three route groups are authored here once
  all g:section84-requirements (f:unsoundness-time, g:section84-routes);
}
attach x:section84 to o:voluntary-hurt;
attach x:section84 to o:theft;
```

Each [scenario](../../research/singapore/section-84-pilot/multi-offence/scenarios/05_theft_satisfied.yh) declares exactly one `analyse o:...;` target and supplies only that offence's leaves plus the shared exception leaves. Hurt scenarios acknowledge the unmodelled ss 323A/334 situations; theft scenarios acknowledge that dishonesty was externally classified. Every scenario acknowledges supplied applicability of the post-2022 s 84 expression. The compiler checks the chosen attachment and acknowledgements, rejects assignments from the other offence, and builds a KernelInput containing only the selected candidate and the shared exception. No scope assumption becomes a proof fact. Section 107's accused-side legal burden and balance-of-probabilities standard annotate only the exception leaves; they do not determine supplied proof status.

From the repository root:

```sh
cd rewrite/haskell
cabal v2-build exe:yuho --offline --jobs=1
YUHO_BIN="$(cabal list-bin exe:yuho)"
MODEL=../../research/singapore/section-84-pilot/multi-offence/section323-section379-with-section84.yh
HURT=../../research/singapore/section-84-pilot/multi-offence/scenarios/01_hurt_satisfied.yh
THEFT=../../research/singapore/section-84-pilot/multi-offence/scenarios/06_theft_nature.yh
"$YUHO_BIN" check "$MODEL"
"$YUHO_BIN" compile "$MODEL" --scenario "$HURT"
"$YUHO_BIN" run "$MODEL" --scenario "$THEFT"
"$YUHO_BIN" explain "$MODEL" --scenario "$THEFT"
```

The theft nature-route [explanation snapshot](../../research/singapore/section-84-pilot/multi-offence/snapshots/06_theft_nature.txt) includes:

```text
Selected candidate offence: o:theft
Candidate statutory sections: Penal Code ss 378, 379
General exception: Penal Code s 84
Attachment: s 84 -> candidate o:theft
Definition instance: shared x:section84
Final technical status: not_satisfied (candidate branch technically defeated by section 84)
No guilt, conviction, acquittal or sentence was determined.
```

The [Haskell tests](../../rewrite/haskell/test/MultiOffenceChecks.hs) cover 12 technical outcomes, five scenario refusals, attachment and private-graph errors, selected-request isolation, stable section 84 quote IDs and an exact explanation snapshot. For the supplied all-proved/no-exception examples, the hurt request is SHA-256 `b84d4d7d8712e683674ae91eea07bebb82087f9cb2a57211d0f8ed00e01e53ba`; the theft request is `41289a7005c162e71eae95067eccfa6e3127be2e71ea10d19ea2dd1c5e507c58`. These hashes identify compiled bytes, not legal validity.

The Haskell DSL now has typed reusable general exceptions and explicit attachments within this bounded two-offence slice. It still lacks reusable typed statutory definitions and cross-references, a Haskell temporal selector, multiple simultaneously attached exceptions per candidate, and an executable treatment of s 24, s 378 explanations, ss 323A/334 or penalties. Yuho does not assess evidence, determine which law applies to real conduct, decide guilt or acquittal, impose a sentence, or give legal advice.
