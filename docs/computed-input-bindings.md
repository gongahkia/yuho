# Explicit computed typed-input bindings

This experimental execution adapter connects one actual v0.3 named expression
observation to one primitive input in a v0.1 proof or v0.4 registered-presumption
analysis. Start with [the quickstart](authoring-quickstart.md); the existing
[typed](typed-authoring.md) and [presumption](presumption-authoring.md) guides
remain the contracts for their respective evaluators.

The saved artifact is `yuho.computed-input/v0.1-experimental`, described by
[`computed-input-v0.1-experimental.schema.json`](../schema/computed-input-v0.1-experimental.schema.json).
It embeds the original typed document, tagged destination and exactly one binding.
It is an execution dependency declaration, not a change to any existing authored
profile. Ordinary proof compilation still requires its supplied assessments.

## Public lifecycle

```haskell
import Yuho.Authoring

-- sourceDocument and destinationDocument are ordinarily authored records.
-- In IO, require handles either existing diagnostic shape.
-- require :: Show e => Either e a -> IO a
upstream <- require (compileTypedAnalysis sourceDocument "typed-analysis"
              >>= evaluateTypedAnalysis)
let destination = presumptionInputDestination destinationDocument "proof-analysis"
    policy = ComputedStatusPolicy computedStatusMapping "not_determined"
binding <- require $ makeComputedInputBinding "binding:relationship" upstream
  "expr:relationship" destination "trigger" policy
  "Explicit author admission for this bounded technical input." []
let document = ComputedInputDocument computedInputFormat "workflow"
                 sourceDocument destination binding
-- validateComputedInput document returns diagnostics, without evaluation.
evaluation <- require (executeComputedInputWith document upstream)
-- executeComputedInput document instead compiles/evaluates the upstream first.
let report = computedInputReport evaluation
projection <- require (projectComputedInput evaluation)
view <- require (computedInputReferenceView projection)
svg <- require (encodeComputedInputViewSvg projection view)
saved <- require (decodeComputedInputDocument (encodeComputedInputDocument document))
```

The checked-in, runnable version is
[`examples/computed-input-consumer`](../examples/computed-input-consumer/).
`proofInputDestination` constructs the alternative proof destination. Neither
constructor makes an incomplete destination executable by itself.

`validateComputedInput` checks the source through its existing compiler, validates
the binding and checks a local destination compilation placeholder without running
either evaluator. That placeholder is not a result or returned authored material.
Execution resolves the actual opaque typed evaluation's uniquely identified named
expression row, maps its status, compiles the execution overlay and invokes the
existing destination evaluator. No rule/proposition aggregates, absent expressions,
or invented child observations are admitted.

## Explicit technical interpretation

The only policy is `yuho.technical-status-to-proof/v1`:

| Actual typed technical status | Generated destination technical classification |
| --- | --- |
| `satisfied` | `Proved` |
| `not_satisfied` | `NotProved` |
| `unresolved` | `Unresolved` with the policy's explicit reason |

The policy must explicitly name `not_determined` or `external_decision_pending`.
This is an author-authorised conversion between technical vocabularies, **not a
finding of legal proof, evidential sufficiency, factual absence, unauthorised
conduct, liability or a legally sufficient rebuttal**. A negative result does not
establish factual absence. The original backend observation, selected typed
assessments, original reason strings, exact scalar values, tuple operands and
sources remain recoverable in the typed snapshot and component projection.
The destination reason does not replace that upstream information.

The binding pins the source document/analysis/expression/snapshot and the exact
destination payload/analysis fingerprint. Actor and context must match exactly.
A change to tuple, classification, scalar, source text or other source authorship
requires fresh evaluation and an explicitly renewed binding. Identical ID strings
never establish correspondence. A selected direct destination assessment conflicts
even if its classification would agree. Unselected alternatives remain retained.
The bridge never overwrites or silently replaces an authored assessment.

## Original authorship and execution overlay

The saved artifact's destination document remains unchanged and may intentionally
lack the assessment for the one bound input. All other required assessments,
including presumption rebuttal and direct-target inputs, remain mandatory.
`makeComputedInputBinding` and `validateComputedInput` reject other missing inputs.

Compilation uses a separate copy with one deterministic generated assessment:
combined origin `generated_computed_input_bridge`, the recorded mapping policy,
issuer `Yuho explicit computed-input adapter`, and an explicit GENERATED reason.
The inner assessment retains the unchanged v0.1 vocabulary: origin
`external_assertion` (external to the destination evaluator), basis `assumption`
(the author admits the technical mapping). No old validator is loosened.
`computedGeneratedOrigin`, `computedGeneratedAssessment` and
`computedExecutionOverlay` expose it as generated
execution material. It is **not** inserted into the persisted original destination.
The existing destination report/snapshot describe that execution overlay; the outer
report separately retains the exact original destination and binding.

No upstream source ID is copied into an unrelated destination source namespace.
Binding `computedOriginalSources` refer to original records in the typed source.
`recoverComputedInputSource evaluation "source" ref` recovers those originals;
use `"destination"` for the destination registry. Repeated references are retained;
sharing a source creates no independent evidential weight. Generated compiler spans
remain in each component's original generated-source mapping category.

## Reports, projections and revisions

`computedInputReport` retains the original artifact, actual typed snapshot and
observation, upstream report, generated classification and overlay, downstream
snapshot/report and optional full presumption report. `computedExecutionId` hashes
the artifact, actual upstream observation/snapshot, generated input and downstream
snapshot. There is no mutable session or background evaluation.

`computedEvaluationSource`, `computedEvaluationProof` and
`computedEvaluationPresumption` retain separately inspectable opaque executions.
`inspectComputedInputOn` checks exact attachment and returns the report;
`projectComputedInputOn` performs the same check before projection. Old executions
remain inspectable through their own snapshots. No cross-profile or cross-law
`compareAnalyses` semantics have been added.

The complete `yuho.computed-input-projection/v0.1-experimental` record contains the
unchanged native typed and proof/presumption projections, the typed expression
inspection, integration nodes/edges and `ComputedNavigation` links. These links
name a component projection and node explicitly, avoiding bare-ID or kernel-string
joins. All actual downstream requirement/guard observations and their skip reasons
remain in the native component. An effective globally derived presumption target
can coexist with a skipped downstream guard; the bridge does not invent a guard
result or treat that derivation as skipped.

Save the following distinct files:

```haskell
encodeComputedProjection projection        -- complete integration projection
encodeRecord view                         -- view bindings
encodeComputedInputViewJson projection view -- simplified diagram JSON
encodeComputedInputViewXml projection view  -- simplified diagram XML
encodeComputedInputViewSvg projection view  -- reference SVG
```

The reference view includes the integration chain; other component context is
retained in the named complete projections rather than silently discarded.
The companion uses the existing `projectionViewFormat`; all encoders validate
versions, partitions, endpoints and rendered bindings. Source details are recovered
explicitly and do not trigger evaluation or network access. The reference view is
bounded to 64 nodes/128 edges and rejects overflow rather than truncating.

## Limits and refusals

One source, one binding, one destination, one-way dependency. The source is only a
v0.3 named expression; destinations are v0.1 primitive proof inputs or v0.4 primitive
proof/condition inputs. Exact actor/context equality is required. Recursive/reverse
dependencies, typed definitions, linked destinations, temporal payloads, rule and
proposition sources, arbitrary JSON values and general cross-profile chaining are
unsupported. These payload types and profile gates exclude dependency cycles.
The adapter's single binding record has no duplicate-binding collection; duplicate
JSON keys and unknown fields in closed records are rejected.

A one-MiB integration budget and all existing backend document, grounding, depth,
identity and execution limits apply. Invalid original anchors, missing observations,
stale snapshots, scope mismatches, unknown mappings and generated-ID collisions
are diagnosed before successful execution/projection. No evaluator truth table,
presumption policy or old format changes.

## Running the public example

From the checkout, build with the pinned compiler and existing cache:

```sh
cabal v2-build exe:yuho-computed-input --offline -j1 --with-compiler=ghc-9.8.4
cabal list-bin exe:yuho-computed-input --offline --with-compiler=ghc-9.8.4
```

Run the returned absolute executable from another directory with an explicit
output-directory argument. For an independently built package, copy
`examples/computed-input-consumer` outside the checkout, copy the unchanged
`cabal.project.freeze`, and create a `cabal.project` with `packages: .` plus the
absolute local Yuho package path, `with-compiler: ghc-9.8.4`, and the repository's
pinned `index-state`. No released Hackage availability is implied.

The consumer executes true/false/unresolved proof compositions and active,
inactive, unresolved, rebutted, direct-proof-dominant and downstream-skipped
presumption compositions. Independent supplied-input reference documents are
saved separately. Equal technical outcomes do not imply equal provenance.
