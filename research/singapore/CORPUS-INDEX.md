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
| Rash endangerment | s 336 rash limb | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | act plus rash endangerment; distinct negligent limb deferred; s 80 attached |
| Assault | ss 351–352 | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | gesture/preparation, intention/knowledge, apprehension and bounded provocation condition; s 81 attached |
| Dishonest misappropriation | s 403 | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | movable property, dishonesty and misappropriation/conversion alternative; s 79 attached |
| Criminal breach of trust | ss 405–406 | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | entrustment/dominion and three nested dealing routes; s 82 attached |
| Receiving or retaining qualifying property | ss 410–411 | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | bounded non-motor s 411(1) receipt/retention, property source and knowledge/reason; s 79 attached |
| Criminal trespass | ss 441 and 447 | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | initial-entry and unlawful-remaining alternatives; s 80 attached |
| Wrongful restraint | ss 339 and 341 | [`modular-singapore-criminal-law-release.yh`](research-release/modular-singapore-criminal-law-release.yh) | 8 new | obstruction, prevention and right-to-proceed relationship; s 81 attached |

The earlier scenario-file inventory is 98 successful Haskell POC scenarios: 12 hurt, 12 multi-offence, 18 definition, 10 participation, 6 attempt, 16 actor-scoped and 24 three-route abetment scenarios. The cheating/mischief pass added 20. This release adds 56 substantive new-family scenarios plus two new attempt scenarios and one new participation scenario. The resulting valid Singapore scenario-file inventory is therefore 177. The standalone s 84 suite separately replays 12 inline authored request variants. Parser and semantic refusal fixtures, four fictional presumption scenarios and analysis cases are not included in the 177. These are file-based decision-path counts, not claims of doctrinal coverage.

[`case-modular-warehouse-shared.yh`](abetment-routes-pilot/case-modular-warehouse-shared.yh) is the integrated modular case. Its three technical allegations reuse explicit shared primitive facts while preserving actor and act-context isolation. The other direct and shared warehouse cases remain regression fixtures.

The release adds seven independent exact-version offence modules, seven candidate penalties, and four executable non-s 84 general-exception families. Across the Singapore corpus there are 11 distinct offence families, five executable general-exception families including s 84, nine distinct candidate-penalty declarations, three release showcase cases and 15 statutory-module manifest files. Compatibility-view manifests and true independent-composition modules are distinguished in the language guide.

The file inventory separates the following categories:

| Category | Count | Counting rule |
|---|---:|---|
| Distinct offence families | 11 | Family rows above; repeated models and statuses do not add a family |
| Distinct provision anchors | 35 | 34 distinct Penal Code sections plus Evidence Act s 107; an instrument/section pair is one anchor |
| Independently authored release modules | 7 | Separate source graphs under `research-release/modules`; the repository also has 8 compatibility or dependency manifests |
| Runnable model entry points | 25 | 20 files declaring a model plus 5 valid modular hosts; the refusal-cycle host is excluded |
| Valid decision-covering scenario files | 177 | 98 earlier, 20 cheating/mischief and 59 in this release as detailed above |
| File-based negative language roots | 13 | 3 hurt, 5 multi-offence, 4 definition-assignment and 1 import-cycle refusal; in-memory refusal mutations are not counted |
| Analysis cases | 12 | 10 warehouse cases plus the 2 new showcase cases |
| Executable general-exception families | 5 | Penal Code ss 79, 80, 81, 82 and 84 |
| Distinct candidate penalties | 9 | Penal Code ss 336 (rash limb), 341, 352, 403, 406, 411, 417, 426 and 447 |
| Contextual-only provision anchors | 4 | Penal Code ss 108, 323A and 334 plus Evidence Act s 107; they provide scope/authority/annotation rather than a separately evaluated rule |

Deferred doctrine is counted by topic rather than citations: the seven bullets below are the seven current deferred-topic groups. A deferred mention never increases executable corpus coverage.

## Contextually cited or presented

- Section 84 uses the reviewed post-1 March 2022 research expression only under an explicit scope acknowledgement. The date is not inferred from conduct facts.
- Section 108 is an authority and scope boundary around the bounded participation models; broader cases of abetment are excluded.
- Sections 417 and 426 are candidate penalty provisions. Their saved terms are presented and technically selected, but no sentence is calculated or imposed.
- Sections 336, 341, 352, 403, 406, 411 and 447 provide bounded candidate terms in the research release. The s 336 candidate is confined to the rash limb.
- Evidence Act s 107 burden annotations are contextual metadata and never classify evidence.
- Saved s 415 explanations and illustrations and saved s 425 explanations and illustrations inform the limitations, but are not executable requirements in this pass.

## Deferred or unsupported doctrine

- Legal applicability by conduct date, commencement, savings, retroactivity and continuing-conduct rules.
- Evidence sufficiency, credibility, fact finding, diagnosis and any guilt, conviction, acquittal or criminal-procedure disposition.
- General cheating doctrine beyond the quoted s 415 alternatives, including separate execution of ss 24–25 definitions and aggravated cheating provisions.
- Mischief ownership and property explanations, aggravated mischief provisions and non-s 84 general exceptions.
- Broader participation, conspiracy and s 108 doctrine; attempt doctrine beyond the bounded direct s 511 slice.
- Sentencing discretion, offender eligibility, enhancements, ancillary orders and actual sentences.
- Section 336 negligence and its distinct terms; s 411 motor-vehicle treatment and reasonable-excuse defence; broader provocation doctrine under s 352.
