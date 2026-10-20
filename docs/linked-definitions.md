# Experimental linked legal definitions

Start with the [quickstart](authoring-quickstart.md), then the
[public API map](authoring-sdk.md#current-api-map). This optional profile adds
named reusable expressions to the existing headless Haskell SDK. It does not
change the proof evaluator or provide rule-result chaining.

## Opt in explicitly

Use `documentFormat = linkedAuthoringFormat`, currently
`yuho.authoring/v0.2-experimental`. The records, strict decoder and ordinary
lifecycle stay the same. The [v0.2 schema](../schema/authoring-v0.2-experimental.schema.json)
extends the executable vocabulary explicitly:

| Construct | Meaning |
| --- | --- |
| `LawNode` with `nodeKind = "definition"` | Single authored, named expression. Nonempty `nodeLabel`; ordinary quotation, citation and original-source fields. |
| `LawEdge id definition body "defines"` | Exactly one body root, of kind `input`, `all` or `any`. |
| `LawEdge id ruleOrGroup definition "use"` | Explicit occurrence of that definition at this requirement location. The edge has its own authored identity. |

A rule has exactly one root connection, either `requires` to an ordinary
expression or `use` to a definition. An `all`/`any` group has at least two
`member`/`use` connections. A definition body may contain acyclic references to
other definitions through its groups. Direct and indirect cycles reject.
Definitions are unparameterised; typed arguments, recursion, fixed points,
negation, numerical operations and result-consuming references remain outside
this profile. `member` is still structural membership, never implicit sharing.

The old `authoringFormat` constant and v0.1 schema remain unchanged. Existing
v0.1 documents still reject these new node/edge kinds, and valid old documents
produce the same requests, reports, snapshots and projections. There is no
implicit upgrade. Both versions remain experimental; no automatic migration or
long-term compatibility promise is introduced.

## Meaning, scope and identities

The [public example](../examples/linked-definitions-consumer/LinkedExample.hs)
authors one `definition:dishonesty` and two references,
`use:theft-dishonesty` and `use:misappropriation-dishonesty`. Its body retains both
s 24 routes: gain/loss-directed intention, or ordinary standards together with
knowledge. Intention does not require completed gain/loss. An independent case
assertion records no completed gain without becoming a prerequisite.

Each analysis selects a rule, actor/context scope and explicit assessment IDs.
The same primitive authored input can have distinct assessments for actor A's
theft event and actor B's misappropriation event. No selection is inferred from
array order, a source, a quotation or another actor's result. Missing inputs
produce `AMISSING`; explicitly unresolved inputs remain supplied classifications.
Every selected input, including attached guards, needs a binding even if skipped.
`not_proved` remains distinct from factual falsity and from skipped computation.

This tranche rejects `AREUSE` if any primitive appears more than once in a selected
analysis, even when the uses seem equivalent. Assessment selection is not yet
occurrence-qualified. Separate analyses may reuse definitions safely; repeated
inputs in one target or across its main/exception slices must be remodelled or
await a separately specified selection contract. Ordinary accidental structural
sharing still rejects `ASHARING`. Nonselected draft material is not instantiated
and does not create selected-slice missing assessments; global reference, source,
identity, shape and cycle checks still apply.

Keep these identities separate:

- One authored definition and its derived content digest. The digest includes
  its reachable expression, references and retained original source records.
  It is computed, not a user-asserted version that could disagree with the body.
- Each authored `use` edge. Copying a subtree never creates this relationship.
- Each structural occurrence: law digest, selected target, actor/context, owning
  rule, authored input and full ordered edge path, including `use` and `defines`.
  The selected analysis is retained alongside it in the projection snapshot.
- The explicitly selected assessment and its independent reason, basis and sources.
- Generated requirement/rule/branch/assignment identities and generated spans.
  v0.2 IDs are namespaced by the immutable input snapshot. They are local
  executable identities, not replacements for original IDs.
- Each run observation, identified by its own snapshot/profile/kernel mapping.

The kernel receives ordinary trees. Definition/use segments remain transparent
in execution, but their complete paths remain in `compiledRequirements`,
`evaluationMappings`, report `observationOccurrence`, source mappings and
projection origins. The nearest executable prefix is the parent requirement;
no wrapper Boolean or extra assessment is invented for a definition declaration.
Expansion is deterministic under the pinned encoder/toolchain.

## Inspect, focus and export

All operations below are exported by `Yuho.Authoring`:

```haskell
compiled <- require (compileAnalysis document "analysis:A")
evaluated <- require (evaluateAnalysis compiled)
projection <- require (projectEvaluation evaluated)
shared <- require (inspectDefinition projection "definition:dishonesty")
focus <- require (focusRequirement projection
  (AuthoredRequirement "f:intends-wrongful-gain"))
let handle = projectedNodeId (explanationOccurrence focus)
links <- require (inspectDefinitionOccurrence projection handle)
overview <- require (definitionView projection "definition:dishonesty")
focused <- require (definitionOccurrenceView projection handle)
```

`require = either (fail . show) pure` is caller-local error handling.
`inspectDefinition` returns the single declaration, body, original sources,
derived digest, all authored uses/referencing rules and occurrences in this
projection's selected analysis. It works on `projectAuthored` drafts with missing
assessments as well as evaluated projections. It does not evaluate other rules.
`inspectDefinitionOccurrence` accepts an occurrence handle, returning its
reference chain, shared definition/digest, existing requirement explanation,
selected assessment, observations and generated mappings. An occurrence can
cross several acyclic definitions. A nonlinked occurrence returns an empty list;
an unknown occurrence is an object-linked focus error. An unknown/wrong-kind
definition returns `DDEFINITION`.

`definitionView` shows the single definition and authored paths from its rules.
It deliberately does not pretend both analyses were evaluated in one projection.
`definitionOccurrenceView` shows one selected occurrence, assessment, referenced
case material, shared definition, use and direct original sources. Use the
existing `encodeViewJson/XML/Svg`, `encodeProjection` and view bindings as in the
[export recipe](authoring-sdk.md#export-recipe). Source recovery uses the unchanged
`recoverOriginalSource`; locator-only references never fabricate excerpts.

Complete linked projections use `yuho.analysis-projection/v0.2-experimental`
and the [v0.2 projection schema](../schema/analysis-projection-v0.2-experimental.schema.json).
The retained authored snapshot and compiler provenance provide the complete
contract; explicit `definition_use` links connect occurrences to declarations.
Existing occurrence/observation identity record shapes and view/legacy export
formats stay unchanged. View bindings enumerate every omission. The bounded
reference views retain the existing 64-node/128-edge limit and refuse overflow.
A legacy view or SVG is not a lossless authoring format.

Editing a shared body once changes both subsequent compilations. Existing
`editLawNode`/`editLawEdge` preserve authored IDs; validation is still necessary.
Old evaluations retain their old snapshots and original sources.
`projectEvaluationOn` rejects edited input. Law revisions remain incompatible
with ordinary `compareAnalyses`; independently inspect each revision instead.
Compatible assessment changes continue to use the existing comparison API.
View focus and source opening remain pure and never change authored meaning.

## Checks and limits

The adapter checks global identities, typed edge endpoints, one definition body,
cycles, accidental sharing, selected-slice repeated primitives, bindings/scopes,
source references and UTF-8 anchors. It checks one MiB/4096 authored objects,
1024 expanded occurrences, 64-edge reference paths, and the kernel's 1024
semantic identities (requirements, assignments, rules, branches, sources and guards).
`AEXPANSION` distinguishes expansion from authored `ALIMIT`. Generated byte/depth,
span, status metadata and remaining closed-protocol invariants are additionally
checked by the unchanged kernel decoder/validator. No failed resolution becomes
an unresolved or false input, and no overflowing tree is truncated into execution.

Native tests independently author a flat v0.1 expression, compare all 81
three-valued input combinations and explicit exception cases, and compare seven
mapped definition requirements against five retained `.yh` scenarios. The legacy
model's singleton wrappers and false post-2022 guard are not claimed to be the
fixed-edition example's surroundings; only the equivalent dishonesty expression
and matching candidate outcomes are compared. Existing proof evidence does not
by itself prove this new adapter.

## Build and run the public consumer

From the checkout, with the existing pinned dependency cache:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
linked_bin=$(cabal list-bin exe:yuho-linked-definitions --offline --with-compiler=ghc-9.8.4)
cd /tmp
"$linked_bin" /tmp/yuho-linked-definition-review
```

The [consumer package](../examples/linked-definitions-consumer/yuho-linked-definitions.cabal)
depends on the exposed Yuho library and imports the public facade, not compiler
internals. It constructs sources explicitly, saves/reloads documents, evaluates
two scopes, recovers an original excerpt, revises the shared body in an explicitly
hypothetical copy and exports reports/projections/bindings/SVG/JSON/XML. It needs
no runtime research-file discovery. To build from a separate project, copy its
three files plus the unchanged checkout freeze and set a local `packages` entry
to that checkout, as in the tested quickstart.

This is a research decomposition of the **PC 2020 Revised Edition**, particularly
ss 23–24, 378 and 403 ([official fixed PDF](https://assets.egazette.gov.sg/2021/Legislative%20Supplements/Revised%20Acts/21rs8334.pdf)).
The second target is a bounded misappropriation/conversion candidate, not complete
s 403 coverage: explanations, general exceptions, interpretive applicability,
evidence and punishment are excluded. Broader s 23 qualifications are retained
as concept/scope context, not computed from property events. The example stores
only a short actual s 24 excerpt; substantive section references are locator-only.
The synthetic classifications and hypothetical ALL-routes revision do not assert
current applicable law, a proposed statutory interpretation or guilt.
