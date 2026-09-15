# Singapore Haskell research corpus index

This index counts executable authored models and decision-covering synthetic scenarios, not raw captures, repeated result statuses or contextual citations. Every result is a technical evaluation of supplied classifications. Nothing here assesses evidence, determines guilt, selects applicable law for real conduct or imposes a sentence.

## Modelled executable material

| Family | Provision anchors | Runnable model | Decision-covering scenarios | Executable boundary |
|---|---|---|---:|---|
| Hurt | ss 319, 321, 323 | [`section323-with-section84.yh`](section-84-pilot/hurt-offence/section323-with-section84.yh) | 12 | act, hurt result, causation and intention/knowledge alternative, with bounded s 84 |
| Hurt and theft candidates | ss 319, 321, 323, 378, 379 | [`section323-section379-with-section84.yh`](section-84-pilot/multi-offence/section323-section379-with-section84.yh) | 12 | explicit candidate selection and shared s 84 attachment |
| Statutory definitions | ss 23, 24, 319, 321, 323, 378, 379 | [`section323-section379-definitions.yh`](section-84-pilot/statutory-definitions/section323-section379-definitions.yh) | 18 | typed definition references and derived outputs; also reusable through exact-version modules |
| Intentional-aid participation | ss 107–109 with theft target | [`intentional-aid-theft.yh`](abetment-pilot/intentional-aid-theft.yh) | 10 | bounded intentional aid and supplied consequence relationship |
| Theft attempt | s 511 with ss 378–379 target | [`section511-theft-attempt.yh`](attempt-pilot/section511-theft-attempt.yh) | 6 | target-directed intention and supplied conduct-stage classification |
| Actor-scoped exception integration | ss 84, 107–109, 378–379, 511 | [`actor-scoped-section84.yh`](actor-exception-pilot/actor-scoped-section84.yh) | 16 | independent principal, alleged-abettor and alleged-attempter s 84 instances |
| Three s 107 routes | ss 84, 107, 109, 378–379, 511 | [`section107-routes-theft.yh`](abetment-routes-pilot/section107-routes-theft.yh) | 24 | instigation, conspiracy and intentional-aid alternatives; s 109 inquiry remains separate |
| Cheating | ss 415 and 417 | [`modular-cheating-mischief.yh`](offence-corpus-pilot/modular-cheating-mischief.yh) | 10 new | deception plus property-inducement or intentional act/harm forms; s 417 candidate terms |
| Mischief | ss 425 and 426 | [`modular-cheating-mischief.yh`](offence-corpus-pilot/modular-cheating-mischief.yh) | 10 new | intention/knowledge and destruction/injurious-change alternatives; s 426 candidate terms |

The earlier scenario-file inventory is 98 successful Haskell POC scenarios: 12 hurt, 12 multi-offence, 18 definition, 10 participation, 6 attempt, 16 actor-scoped and 24 three-route abetment scenarios. The standalone s 84 surface suite additionally replays 12 inline authored request variants. Analysis cases are counted separately because each contains three requests. This pass adds 20 distinct scenario files, bringing the scenario-file total in the table to 118 and the surface replay total to 130. These are inventory counts, not claims of doctrinal coverage.

[`case-modular-warehouse-shared.yh`](abetment-routes-pilot/case-modular-warehouse-shared.yh) is the integrated modular case. Its three technical allegations reuse explicit shared primitive facts while preserving actor and act-context isolation. The other direct and shared warehouse cases remain regression fixtures.

## Contextually cited or presented

- Section 84 uses the reviewed post-1 March 2022 research expression only under an explicit scope acknowledgement. The date is not inferred from conduct facts.
- Section 108 is an authority and scope boundary around the bounded participation models; broader cases of abetment are excluded.
- Sections 417 and 426 are candidate penalty provisions. Their saved terms are presented and technically selected, but no sentence is calculated or imposed.
- Evidence Act s 107 burden annotations are contextual metadata and never classify evidence.
- Saved s 415 explanations and illustrations and saved s 425 explanations and illustrations inform the limitations, but are not executable requirements in this pass.

## Deferred or unsupported doctrine

- Legal applicability by conduct date, commencement, savings, retroactivity and continuing-conduct rules.
- Evidence sufficiency, credibility, fact finding, diagnosis and any guilt, conviction, acquittal or criminal-procedure disposition.
- General cheating doctrine beyond the quoted s 415 alternatives, including separate execution of ss 24–25 definitions and aggravated cheating provisions.
- Mischief ownership and property explanations, aggravated mischief provisions and non-s 84 general exceptions.
- Broader participation, conspiracy and s 108 doctrine; attempt doctrine beyond the bounded direct s 511 slice.
- Sentencing discretion, offender eligibility, enhancements, ancillary orders and actual sentences.
