# Experimental registered-presumption authoring

Import `Yuho.Authoring`. This additive **`yuho.authoring/v0.4-experimental`**
profile wraps a v0.1 `AuthoringDocument` in `PresumptionDocument`. It executes
`RegisteredPresumptionDerivations-v1`. Existing v0.1 trees, v0.2 linked
definitions and v0.3 grounded typed documents retain their formats and behavior.
The current wrapper rejects linked and typed composition. Descriptive support,
challenge and chronology connections never become operative registrations.

Start with the [quickstart](authoring-quickstart.md), then the
[current API map](authoring-sdk.md#current-api-map). This guide describes the
additional opt-in boundary, not an alternative general legal language.

## Author a registration

An `AuthoredRegistration` has an ID, label, primitive target, explicit applicable
analysis IDs, original source references, trigger and rebuttal trees.
`RegisteredCondition` uses `leaf_effective`, `all_of` or `any_of`. Every condition
has its own authored ID and source references. A leaf has `Just input` and no
members; a group has `Nothing` and at least two members. Conditions are trees,
not named references or arbitrary shared graphs. Child order supplies the stable
condition path; no geometric or descriptive connection supplies semantics.

```haskell
import Yuho.Authoring

-- proofDoc contains primitive inputs "possession", "contrary", "knowledge",
-- an analysis "case:one", and explicit scoped assessments of all three.
let trigger = RegisteredCondition "condition:possession" "leaf_effective"
                (Just "possession") [] [statutoryReference]
    rebuttal = RegisteredCondition "condition:contrary" "leaf_effective"
                (Just "contrary") [] [statutoryReference]
    registration = AuthoredRegistration "registration:knowledge"
                "Registered knowledge support" "knowledge" ["case:one"]
                [statutoryReference] trigger rebuttal
    doc = PresumptionDocument presumptionAuthoringFormat "document:registered"
                proofDoc [registration] ["Bounded externally assessed model."]
let readiness = validatePresumptionAnalysis doc "case:one"
compiled <- compilePresumptionAnalysis doc "case:one"
evaluated <- evaluatePresumptionAnalysis compiled
projection <- projectPresumptionEvaluation evaluated
inspection <- inspectPresumptionTarget projection "knowledge"
view <- presumptionReferenceView projection "knowledge" []
svg <- encodePresumptionViewSvg projection view
```

The final five operations above can compose in an `Either [AuthoringDiagnostic]`
block. `readiness` exposes `presumptionAnalysisReady`,
`presumptionDiagnostics` and `presumptionOpenInputs`; validation never evaluates.
`validatePresumptionDocument` checks whole-document structure and sources.
`projectPresumptionAuthored doc analysisId` admits a structurally identifiable
draft with missing assessments; it supplies inventory, never computed results.

Each applicable registration is resolved globally in the selected analysis's
actor/context scope. The SDK requires exactly one selected direct assessment
for every input in the proof slice **and** every applicable registration target,
trigger and rebuttal. A missing rebuttal remains missing; it does not mean
`not_proved`. Wrong-scope, ambiguous or outside-slice selections are rejected.
An assessment may cite several assertions, including cross-context material;
these are attribution links, not evidence aggregation.

## Execution and meaning

Compilation reuses ordinary proof compilation, adds explicit registrations and
condition-only input declarations, then calls the existing presumption wire
decoder and validator. Evaluation calls `evaluatePresumptions`, then
`evaluateProofWith` using its effective map, penalty selection and the existing
presumption result encoder. The adapter contains no presumption truth tables.

`PresumptionReport` has separate `presumptionReportLeaves`,
`presumptionReportDerivations` and `presumptionReportProof`:

- `EffectiveLeafObservation` retains the **original selected assessment**, direct
  technical value, effective technical value, route IDs and downstream mappings.
- `RegistrationObservation` retains its registration, trigger/rebuttal trace
  trees, route state and actual derivation evaluation state.
- The downstream `ApplicationReport` carries effective requirement statuses,
  rule/branch reasons and exception evaluation/skip information. Its selected
  assessment still holds the original supplied classification.

An active route can support effective satisfaction while direct `not_proved`
remains visible. A rebutted route withdraws its support; it does not establish
factual falsity. Direct proof or another active route can still support the
target. Unresolved routes remain distinct from inactive routes. All routes and
condition children are retained, including those beside decisive values.
These are the existing backend's technical policies, not evidence weighing.

**Global derivation evaluation differs from downstream execution.** A guard's
input may have a resolved effective value even when the proof evaluator skips
the guard because ordinary requirements were unresolved. The report retains
`not_evaluated`, no computed downstream value and the actual skip reason. The
projection emits no proof-trace observation for a skipped requirement; its
structural occurrence and authored assessment remain available.

## Identity, sources and budgets

The [authored schema](../schema/authoring-v0.4-experimental.schema.json) and
[complete projection schema](../schema/presumption-projection-v0.4-experimental.schema.json)
are additive. Closed records reject unknown fields through the public decoder,
including nested fields. Open presentation string maps retain their existing
contract. The bounded semantic validator rejects unsupported condition kinds,
including burden effects. No operative `burden_shift` or `burden_effect` exists.

All authored identities, including registration and condition IDs, occupy one
namespace. Generated registration IDs, condition paths, proof requirement IDs,
assignments and observations are separately mapped. The complete projection
retains the exact `PresumptionSnapshot`, original document, compiled mappings,
generated sources, all authored objects and explicit relationships. Repeated
provenance entries produce distinct position-indexed edges; several objects may
legitimately reference the same source. Repetition assigns no evidential weight.

Scoped proof occurrences retain the underlying proof-law/path/scope identity.
That `occurrenceLawDigest` describes the underlying proof structure, not the
entire registration graph. The outer presumption snapshot covers registrations,
conditions, applicability and all retained content; it is required for result
attachment. An unchanged proof occurrence alone does not authorize comparing or
attaching executions of different presumption graphs. The exposed ordinary proof
compilation component is scaffolding for mappings, not a presumption evaluation.

Kernel spans describe **generated compilation material**. They never become
original statutory locations. `presumptionCompiledMappings` records the owner,
condition path, generated source/span and original references. Every generated
condition span is inside its generated registration span. Original conditions
may cite different original sources; their anchors are independently validated.
Condition-only primitive inputs use generated registry storage branches because
the protocol forbids undeclared facts. Those branches are compiler scaffolding,
not authored rules or additional downstream proof observations.

Use `sourceAnchorCodePoints` or `sourceAnchorBytes` when retaining original text.
The MDA anchors are offsets within the retained statutory extract, not the entire
SSO page. `recoverPresumptionSource projection ref` shares the existing validated UTF-8
recovery contract. Locator-only references have no invented excerpt. No operation
fetches a URL. Default reference views omit original source cards;
`presumptionReferenceView projection target [sourceId]` explicitly expands
relevant original sources after the explanation.

The document is bounded to one MiB and 4,096 authored objects. Conditions have
backend depth at most 16 and groups at least two children. The complete compiled
request must also pass the wire's one MiB/64-container limit and 1,024 semantic
identity budget, which counts expanded conditions, registrations, assignments
and storage branches as well as ordinary requirements. Document size is not
executable size. Reference views have 64-object/128-connection limits; oversized
views fail instead of truncating. Complete projections retain omitted context.

## Inspection and revisions

`inspectPresumptionTarget` accepts an authored primitive input or its selected
structural occurrence ID. It returns its scope, selected assessment, compatible
unselected alternatives, assertions, sources, all targeting registrations and
route observations, direct/effective observation, downstream occurrences, structural
ancestors and associated rule/exception state.
`inspectRegistration` returns an authored registration and an optional run
observation. Registrations not applicable to the selected analysis have no run
observation. Condition trees in the structured report preserve child/leaf links
without requiring a consumer to reconstruct kernel traces.

Ordinary immutable record updates can revise a supplied assessment or explicitly
select another one in `presumptionProofDocument.documentAnalyses`. The proof-only
`selectAssessment` helper intentionally rejects condition-only targets outside
its own slice; use explicit record selection for those inputs and validate the
wrapper. No new editing/session framework is introduced.

Encode/decode with `encodePresumptionDocument` / `decodePresumptionDocument`.
Recompile and evaluate a changed document to get a new snapshot; earlier
`PresumptionEvaluation`s retain their original inputs and sources.
`projectPresumptionEvaluationOn` rejects any different retained content. Focusing
or expanding sources does not evaluate or alter the snapshot. Generic proof and
typed comparisons do not accept presumption evaluations. Keep the two structured
reports separately inspectable; this tranche adds no cross-profile comparison.

## Executable consumer and conformance

The [public-only consumer](../examples/presumption-consumer/Main.hs) and
[authored fixtures](../examples/presumption-consumer/PresumptionExamples.hs)
exercise synthetic routes, chains, skipped guards and a bounded MDA research
example. From the checkout, using its pinned cache/compiler:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
cabal list-bin exe:yuho-presumption-consumer --offline --with-compiler=ghc-9.8.4
```

Run the returned **absolute executable path** from `/private/tmp`, with an
explicit output directory. It needs no research fixtures or checkout discovery.
`python3 test/presumption_authoring_consumer.py ABSOLUTE_EXECUTABLE` performs
schema/export/binding/replay checks from outside the checkout. The example can
also be copied into an external Cabal project with `packages: . /absolute/yuho`
and the existing frozen constraints; Yuho is a local dependency, not a published
Hackage promise. Native tests compare independently authored
[kernel reference programs](../test/fixtures/presumption-authoring) with the SDK
path, normalizing generated IDs/spans rather than route states or classifications.

## Historical MDA model boundary

The research fixture uses [MDA 1973, 2020 RE, published 31 December 2021,
s 18(2)–(3)](https://sso.agc.gov.sg/Act-Rev/MDA1973/Published/20211231?DocDate=20211231&ProvIds=P13-),
with one identified person, drug and event. It represents possession proved or
presumed supporting a knowledge presumption, subject to externally assessed
contrary proof. The rebuttal input explicitly means **legally adequate contrary
proof subject to s 18(3)**; no-physical-possession narrative alone is not such a
classification. This scope constraint is retained and named in the fixture;
SDK structural validation cannot verify legal adequacy of a caller's assessment.

The statutory upstream s 18(1) chain is not admitted here: the backend's effective
leaves do not themselves enforce a direct-only trigger. Synthetic chaining tests
technical composition, not legal justification. Complete offences, s 17
trafficking, sentencing, s 18(4) multi-person deeming, evidential sufficiency,
automatic burden transfer and current applicability remain outside this model.
