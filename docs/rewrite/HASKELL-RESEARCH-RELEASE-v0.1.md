# Yuho Haskell Research Language v0.1

This is a bounded research release, not a production legal system. It is coherent for authoring, checking, compiling, running and explaining the included Singapore criminal-law models. It does not claim exhaustive Penal Code coverage or legally current advice.

## Capability matrix

| Capability | Release status | Boundary |
|---|---|---|
| Exact local modules and exports | Supported | Deterministic local files; no registry or package distribution |
| Independent rule-graph composition | Supported in bounded form | Definitions, offences, general exceptions and candidate penalties; specialised participation/attempt modules remain whole graphs |
| Typed offence definitions and requirement graphs | Supported | Authored corpus only |
| General exceptions | Supported in bounded form | Sections 79, 80, 81, 82 and reviewed post-2022 s 84 expressions |
| Ordered multi-allegation cases | Supported in bounded form | 1–32 allegations; multi-offence hosts plus specialised participation/attempt cases |
| Typed shared supplied facts | Supported | Primitive inputs only; derived-result transfer is rejected |
| Actor-scoped exceptions | Supported in bounded form | Principal, participant and attempter contexts in the specialised s 84 integration |
| Temporal expressions | Supported in bounded form | Mechanical authored interval selection, not legal-currency determination |
| Candidate penalties | Supported in bounded form | Imprisonment and SGD fine term trees; never an imposed sentence |
| Registered presumptions | Supported in bounded form | Explicit technical subprogram with supplied trigger/rebuttal classifications |
| Burden and standard annotations | Supported in bounded form | Contextual metadata; no assessment that a burden was discharged |
| Participation | Supported in bounded form | Three s 107 routes for theft and reusable intentional-aid route for misappropriation; s 109 remains separate |
| Attempt | Supported in bounded form | Direct s 511 technical attempt for theft, assault and misappropriation |
| Narrative fact extraction | Explicitly deferred | Facts are authored and supplied |
| Evidence credibility or sufficiency | Intentionally out of scope | Yuho never assesses evidence |
| Automatic research or legal currency | Explicitly deferred | Sources and applicability assumptions remain authored |
| Judicial guilt, sentence or CPC outcome | Intentionally out of scope | No aggregate liability or court disposition |
| All Singapore legislation and doctrine | Explicitly deferred | Only indexed authored expressions execute |
| Production package registry, deployment and full LSP parity | Optional expansion | Not required for the research language |
| Core Yuho v0.2 typed finite rules | Supported in bounded form | Additive nominal entities, predicates/scalars, finite quantifiers, cardinality and explicit priority; one host module layer and finite domains only |

## Kernel variants

These are the seven preserved v0.1 boundaries. Core Yuho v0.2 adds `TypedFiniteRules-v1` as an eighth, additive variant because scalar, cardinality, witness and conflict observations cannot be represented losslessly by the historical seven.

| Kernel fragment | Haskell surface status |
|---|---|
| `SuppliedProofStatus-v1` | Directly authored by normal `.yh` models and scenarios |
| `RegisteredPresumptionDerivations-v1` | Directly authored through `presumption-program`, implemented as a separate technical subprogram |
| `GuardedPenaltySelection-v1` | Generated internally by higher-level candidate-penalty lowering and retained as a protocol suite |
| `PenaltyTerms-v1` | Generated internally by typed penalty terms and retained as a protocol suite |
| `ClosedBooleanBranches-v1` | Low-level compatibility boundary |
| `AcyclicGuardedExceptions-v1` | Low-level compatibility boundary underlying checked exception behavior |
| `TypedBooleanFacts-v1` | Low-level compatibility boundary underlying typed facts |
| `TypedFiniteRules-v1` | Directly authored by `typed-rules-model`/`typed-rules-scenario`; additive v0.2 boundary |

## Release corpus

The authored corpus has 11 distinct offence families: hurt, theft, cheating, mischief, rash endangerment, assault, dishonest misappropriation, criminal breach of trust, receiving/retaining qualifying property, criminal trespass and wrongful restraint. Four new general-exception families—ss 79, 80, 81 and 82—join s 84.

Seven new families have 56 substantive scenario files. Each family includes satisfied, ordinary not-satisfied, material unresolved, exception-defeat and exception-unresolved paths. Separate demonstrations apply s 511 attempt to assault and misappropriation and intentional-aid participation to misappropriation.

## Known bounded defects and omissions

- Cross-module participation and attempt declarations are imported as whole specialised models, not merged into the broad offence host.
- Simple multi-offence exceptions are actor-bound through allegation inputs but do not provide the reusable named instance machinery of the specialised actor-scoped s 84 model.
- The s 336 model executes only the rash limb. Its negligent limb and distinct penalty remain contextual.
- The s 411 model executes a bounded non-motor subsection (1) expression; the statutory reasonable-excuse defence is deferred.
- Candidate penalties omit unsupported punishment types such as caning and never choose an actual sentence.
- Saved statutory material supports the authored expressions but does not itself determine current applicability to real conduct.

These are explicit research limits rather than missing infrastructure required to operate the included language.
