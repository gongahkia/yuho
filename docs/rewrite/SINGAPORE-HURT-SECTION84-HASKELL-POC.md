# Singapore hurt candidate with section 84: Haskell DSL research POC

**Status:** Bounded, non-production research proof of concept. The [authored model](../../research/singapore/section-84-pilot/hurt-offence/section323-with-section84.yh) and [synthetic scenarios](../../research/singapore/section-84-pilot/hurt-offence/scenarios/01_intention_no_exception.yh) run entirely through the authoritative Haskell frontend and kernel under [ADR-0002](ADR-0002-HASKELL-AUTHORITATIVE-FRONTEND.md). No real person, allegation, evidence or legal outcome is assessed.

The saved Penal Code browser snapshot used for this bounded authoring exercise contains s 319's hurt definition (bodily pain, disease or infirmity, with an explanation about unconsciousness), s 321's act plus intention **or** knowledge and resulting hurt, and s 323's candidate punishment provision. Section 323 expressly excepts cases provided for by **both s 323A and s 334**. The model places conduct, hurt result and causal link in conjunction with the intention/knowledge alternative. `section323_candidate_requirements` names that pre-exception requirement group; `final_rule` names the rule after the exception guard. It attaches the existing reviewed post-2022 [s 84 research structure](../../research/singapore/section-84-pilot/surface/section84.yh) as a defeating general exception: unsoundness at the act time and one of the nature, wrongfulness or control routes, each retaining its causal relationship. The wrongfulness route requires both ordinary-standards and contrary-to-law components. The [prior research report](SINGAPORE-SECTION-84-AUTHORITY-AND-TEMPORAL-RESEARCH.md) remains the legal-analysis record; this POC adds no new verification or approval claim.

The model declares three typed research-scope assumptions: outside the modelled s 323A situation, outside the modelled s 334 situation, and applicability of the post-2022 s 84 expression. Every scenario must acknowledge all three with `assume`; the compiler does not infer them, treat them as evidence, include them among KernelInput facts, or select law from a date. Missing, duplicate and unknown acknowledgements fail before execution. The s 107 accused-side burden and balance-of-probabilities standard annotate only s 84 leaves. They do not classify evidence or change technical proof statuses.

From the repository root after an offline Cabal build:

```sh
cd rewrite/haskell
cabal v2-build exe:yuho --offline --jobs=1
YUHO_BIN="$(cabal list-bin exe:yuho)"
MODEL=../../research/singapore/section-84-pilot/hurt-offence/section323-with-section84.yh
SCENARIO=../../research/singapore/section-84-pilot/hurt-offence/scenarios/06_nature_route.yh
"$YUHO_BIN" check "$MODEL"
"$YUHO_BIN" compile "$MODEL" --scenario "$SCENARIO"
"$YUHO_BIN" run "$MODEL" --scenario "$SCENARIO"
"$YUHO_BIN" explain "$MODEL" --scenario "$SCENARIO"
```

For that synthetic scenario, the explanation ends:

```text
Section 84 kernel rule: satisfied
Section 107 context: section107; defence legal burden; balance_of_probabilities. This annotation does not classify evidence.
Final technical status: not_satisfied (candidate branch technically defeated by section 84)
No guilt, conviction, acquittal or sentence was determined.
```

The [Haskell scenario checks](../../rewrite/haskell/test/LegalSurfaceChecks.hs) cover 12 successful technical evaluations and three missing-scope refusals. Intention-only and knowledge-only scenarios each pass the fault alternative. Hurt absent or both fault inputs not proved leaves candidate requirements not satisfied; an unresolved causal input leaves them unresolved. Complete nature, control and conjunctive wrongfulness routes defeat a satisfied candidate branch. Either wrongfulness component alone does not establish that route. An unresolved section 84 guard remains unresolved rather than being treated as absent. [Deterministic explanation snapshots](../../research/singapore/section-84-pilot/hurt-offence/snapshots/06_nature_route.txt) cover a defeated branch and an unresolved guard.

The compiler's `source_text` is built from short `.yh` quote declarations; those labels are not an authenticated statutory copy. The saved browser snapshot and existing research packet were not modified. The s 319 unconsciousness explanation is not independently decomposed into executable leaves; a supplied hurt classification must be made outside Yuho. The model also omits s 323A and s 334 doctrine, other potentially applicable offences or exceptions, conduct-date selection, witness and medical assessment, and punishment terms. `not_proved` is not a factual finding of falsity. The result is a technical derivation, not a finding that a section 323 offence was legally proved, a judgment, sentence or legal advice. The Haskell DSL still lacks reusable general-exception composition across more than one offence, real-law temporal selection and richer offence-definition types.
