# Grounded typed authoring (experimental v0.3)

Start with the [quickstart](authoring-quickstart.md) and [current API map](authoring-sdk.md#current-api-map). This opt-in profile extends the **capabilities** of the Haskell SDK, not the meaning of proof-profile nodes. Existing v0.1/v0.2 documents and operations are unchanged.

## Boundary and lifecycle

Import `Yuho.Authoring`. Use `TypedDocument` with `typedAuthoringFormat` (`yuho.authoring/v0.3-experimental`), `encodeTypedDocument` / `decodeTypedDocument`, `validateTypedDocument`, `validateTypedAnalysis`, `compileTypedAnalysis`, and `evaluateTypedAnalysis`. Compilation uses the production `TypedFiniteRules-v1` decoder, grounding/type/resource checks and evaluator. It does not use the proof backend. No evaluator truth tables have been copied into the adapter.

The typed document is a separate closed record and has its own decoder. `decodeDocument` continues to decode proof documents; it rejects v0.3. Adding proof nodes, `member`, `defines`, `use`, or linked-definition objects to a typed document is unsupported. Unknown JSON fields, duplicate keys and unknown expression constructors are rejected. There is no mixed-backend execution or cross-profile comparison. `compareAnalyses` remains a proof-profile operation: inspect typed revisions independently instead of forcing their reports into that API.

Each selected `TypedAnalysis` names one unparameterised establish rule, one matching proposition, concrete actor/context scope, explicitly selected assessment IDs and scalar-value IDs. Actor must identify a declared concrete entity. Unrelated draft bindings are not required for a selected analysis. Missing selected input is an error (`TMISSING`), not an inferred false or unresolved value. `projectTypedAuthored` can display a structurally valid incomplete draft, without compilation or evaluation, and returns its open-input inventory.

## Closed JSON constructor fields

Closure applies inside nested tagged constructors as well as ordinary records.
`GroundApplication`, `IntegerComparison`, `ExactInteger`, `UnknownInteger` and
`TechnicalUnresolved` admit exactly `tag` and `contents`. Nullary `TypedAll`,
`TypedAny`, `TechnicalTrue` and `TechnicalFalse` admit only `tag`; even an extra
`contents` field is rejected. A misspelling such as `negated` on
`GroundApplication` is an error, not an ignored extension or a negation operation.
The public `decodeTypedDocument` returns `TJSON` with the nested JSON path and
unexpected field in its diagnostic message. Missing required contents, incorrect
payload types and unsupported constructor tags remain distinct decode errors.
The v0.3 schemas already close these objects with `additionalProperties: false`.

`presentationProperties` is the documented open string-to-string map: arbitrary
presentation keys remain permitted there. Opening that map does not open its
containing record or any executable constructor. The v0.1/v0.2 decoders retain
their existing contracts.

## Declarations, tuples and supplied information

`TypedEntityType` declares a nominal type; `TypedEntity` names a concrete entity of that type. `TypedPredicate` contains one to four ordered `TypedArgument` roles. Roles are displayable names with nominal types; array positions determine application argument positions. `TypedApplication` retains one `GroundTuple` (predicate ID and concrete entity IDs).

`TypedAssessment` is separate from that application. It retains its target application ID, the exact tuple being classified, scope, `TechnicalTrue`, `TechnicalFalse` or `TechnicalUnresolved reason`, reason, issuer, origin, basis, assertion IDs and original sources. A tuple change requires an explicit compatible assessment; the old classification does not follow a changed actor, computer or access kind. Selecting two assessments for the same application is ambiguous. A selected assessment in another scope is rejected. Retained alternatives remain unselected supplied records and receive no computed result.

`TechnicalFalse` is an explicit technical classification. It is not proof of the negation of a factual proposition, an inference from absence, or a finding of unauthorised conduct. No public `not` constructor is admitted. Multiple assertion references are provenance, not evidence aggregation. Cross-context assertion references are retained; the adapter does not infer relationships between their actors.

All authored objects, relationships, analyses, assertions, sources and annotations have distinct IDs in a document-wide namespace. Predicate and entity IDs cannot contain comma or parentheses: these delimit the existing backend's ground tuple keys. IDs have a maximum of 128 UTF-8 bytes.

## Scalars and expressions

`TypedScalar` declares `integer`. `TypedValue` supplies either `ExactInteger Integer` or `UnknownInteger "integer" reason`, in an explicit scope, with reason and issuer. Integer arithmetic is exact. No date, enum, money, float or native physical-quantity authoring is admitted in this tranche.

Expressions are:

- `GroundApplication applicationId`.
- `IntegerComparison "gt" leftScalarId rightScalarId` (strict greater than).
- `IntegerComparison "eq" leftScalarId rightScalarId` (exact equality).
- `TypedAll` and `TypedAny`, with at least two `typed_member` child relationships.

A `typed_body` relationship connects a rule to its sole root. Expressions form finite trees, with depth at most four (root zero). Cycles and shared expression children are rejected. Public named references, parameters, quantifiers, priorities, defeat rules, technical negation, cardinality, nested guards, normative execution and result-consuming chaining are not admitted. This restriction is distinct from the broader backend's capabilities.

Different expression occurrences can refer to the same explicitly classified application. Duplicate application objects for the same backend tuple are rejected, avoiding aliasing and conflicting assignments. The scope of a ground assessment must match the selected analysis; a tuple can deliberately contain other entities as its operands without implying additional actor semantics.

The adapter registers each selected authored expression as a named backend requirement. Child references are generated internally. This obtains **actual named-expression observations** for groups and leaves from the unchanged backend. It does not invent per-child execution traces or expose general reference authoring. There is no short-circuit/skipped-child trace in this subset: returned expressions are evaluated. Supplied inputs, including scalar values, are never labelled kernel expression observations themselves.

## Results, identities and source inspection

`typedEvaluationReport` separates `typedReportExpressions`, `typedReportRules`, and `typedReportPropositions`. Each row retains its real structured backend row, computed status, evaluation state and distinct run observation ID. Proposition resolution (`established`, `not_established`, `unresolved`, etc.) is separate from its truth status. Rule results are ground; they are not aggregated claims about independently scoped actor bindings.

`typedEvaluationSnapshot` retains the exact original document, selected analysis and evaluator profile. Changing classifications, values, reasons or source content changes the snapshot. `projectTypedEvaluation` uses that snapshot. `projectTypedEvaluationOn editedDocument oldResult` rejects a changed document (`TSTALE`). Prior evaluations remain inspectable. Occurrence identity includes the law digest, selected rule, scope, authored expression and structural relationship path. Observations also include the run snapshot. Compatible supplied-input revisions align occurrences without conflating their observations.

`typedEvaluationMappings` and report mappings connect authored expressions, ground tuple keys, selected assessments, scalar declarations/value records, selected rule/proposition and declarations to executable identities. Generated fact reasons are explicitly labelled hashes pointing to retained full assessments. The typed kernel protocol has no original-source span field: original anchors remain exclusively in authored metadata and mappings, and no generated offsets are presented as original coordinates.

```haskell
-- document and analysisId are caller-supplied TypedDocument/Text.
compiled <- require (compileTypedAnalysis document analysisId)
result <- require (evaluateTypedAnalysis compiled)
projection <- require (projectTypedEvaluation result)
focus <- require (inspectTypedExpression projection expressionId)
-- typedFocusArguments: ordered roles + concrete typed entities
-- typedFocusSelected / typedFocusAlternatives: supplied records, separate
-- typedFocusScalars / typedFocusValues: operands + selected exact values
-- typedFocusObservation: actual containing/named expression observation
recovered <- traverse (require . recoverTypedSource projection)
                     (typedFocusSources focus)
```

Here `require = either (fail . show) pure` in an `IO` consumer. Original anchors can be constructed before any document exists using `sourceAnchorCodePoints` or `sourceAnchorBytes`. `recoverTypedSource` shares the existing original-source validation/recovery logic. Coordinates are half-open UTF-8 byte ranges with one-based byte columns; locator-only references return no excerpt. Projection/source inspection performs no evaluation, fetching or automatic source relocation.

## Projection and exports

`projectTypedAuthored`, `projectTypedEvaluation`, `inspectTypedExpression`, `typedReferenceView`, and `recoverTypedSource` compose the headless workflow. Focus by authored expression ID or projected occurrence ID; foreign/unselected occurrence targets fail with object-linked diagnostics. `TypedExpressionFocus id` selects the occurrence, application/operands, selected supplied information, concrete argument entities and immediate assertions. `TypedRuleFocus` includes all selected expression dependencies and the rule/proposition. Original source IDs are an explicit third argument for expansion; default views do not expand source documents.

Reference arrays preserve their authored entries. Repeating an assertion ID in
one assessment's `typedAssertionRefs`, or a target in one annotation's
`annotationAbout`, is permitted non-executable material. Projection emits one
relationship per entry with deterministic, distinct IDs; it does not duplicate
the target object, discard entries, or calculate additional evidential strength.
The first occurrence keeps its existing edge ID. Later occurrences of the same
owner/target pair receive an occurrence discriminator. IDs for documents without
these repetitions remain unchanged. Identical source references within one
object already use positional edge identities, including distinct original
anchors; shared sources across separate objects remain supported.

This rule does not admit executable structural sharing, duplicate object IDs or
ambiguous active assessment selections. Those remain validation errors. For
otherwise valid documents within the documented limits, these reference arrays
can progress through authored/evaluated projection without a late identity
collision. Focused views retain or explicitly omit each distinct edge through
their bindings; their separate 64-object/128-connection limits still apply.

The full contract is `yuho.typed-analysis-projection/v0.3-experimental`, with [authoring schema](../schema/authoring-v0.3-experimental.schema.json) and [projection schema](../schema/typed-analysis-projection-v0.3-experimental.schema.json). It retains the complete typed snapshot, original declarations/tuples/values/sources, typed records, structural operands, ordered argument edges, selected assessments, real observations and mappings. `typedNodeObservation` is absent on assertions, sources, applications, values and assessments. Computed expression information belongs to occurrences and observations.

`typedReferenceView` returns the unchanged `ProjectionView` inclusion/omission and rendering-binding contract. Reference views reject more than 64 objects / 128 connections rather than truncating. `encodeTypedViewJson`, `encodeTypedViewXml` and `encodeTypedViewSvg` validate identities/endpoints before encoding. The JSON/XML view uses the existing `yuho.semantic-graph/v0.1` presentation contract, with **no overloaded status field**. Full typed semantics live in `encodeTypedProjection` and its bindings companion. Neither simplified diagram view nor complete derived projection replaces the authored document as editable interchange.

Use distinct filenames: `example.document.json`, `example.report.json`, `example.projection.json`, `example.bindings.json`, `example.view.json`, `example.xml`, `example.svg`. The [public consumer](../examples/typed-authoring-consumer/Main.hs) demonstrates the complete export recipe without adding a public export wrapper.

## Executed examples and scope

The [typed consumer](../examples/typed-authoring-consumer/TypedExamples.hs) constructs both examples through public records. It does not import the legacy parser or kernel constructors.

The permission example uses a fixed CMA 2007 Revised Edition s 2(5) research context. It demonstrates the positive relation `permission(recipient, computer, access-kind)` and separate Ada/Ben classifications. It omits the entitled-controller inquiry and the full s 3 offence. Missing/false permission does not establish unauthorised access. Legal sources are locator-only; synthetic retained case text has a validated Unicode anchor. Historical fixed-edition access is documented in the coverage audit; the example makes no current-law claim.

The threshold example uses a fixed RTA 2004 Revised Edition ss 67/72 research context. Strict `value > 35` is false at 34 and 35, true at 36; an explicitly unknown integer yields unresolved. The example-local `normalisedThreshold` operation rejects an undeclared medium/unit or nonpositive scale before document construction. It validates the caller’s declared profile, not the physical sample. A common external scale of 100 represents 35.01 and 35 exactly as 3501 and 3500. **The caller must validate medium, unit and common scale before supplying integers.** Integer typing alone cannot distinguish blood from breath, or differently scaled measurements. No automatic dimensional conversion is provided. These supplied synthetic values are not legal findings or a complete offence model.

From the checkout:

```sh
cabal v2-build exe:yuho-typed-authoring --offline -j1 --with-compiler=ghc-9.8.4
cabal list-bin exe:yuho-typed-authoring --offline
```

Run the printed absolute executable from any directory with an explicit output folder. To build externally, copy `Main.hs`, `TypedExamples.hs` and `yuho-typed-authoring.cabal` to a new project. Use `packages: . /absolute/path/to/yuho`, `with-compiler: ghc-9.8.4`, `index-state: 2026-09-12T03:17:42Z`, `jobs: 1` in its `cabal.project`, and copy the unchanged Yuho `cabal.project.freeze`. Then run the same offline build command there. This is a local dependency, not a Hackage publication.

## Validation ownership and limits

The adapter checks authored uniqueness/references, nominal declarations, roles and tuple compatibility, exact assessment target copies and scope, explicit selections/completeness, integer-only operands, supported finite tree shape, cycles/sharing/depth, original anchors and retained metadata. It limits documents to one MiB / 4096 objects and applies protocol declaration limits. Compilation additionally passes its request through the production decoder: closed protocol, total selected scalar assignments, ground fact types, wire depth and expanded `max_nodes=2048` budget. Expansion can exceed the backend budget despite fitting the authored size; this returns `TBACKEND`, not truncation.

This is an experimental bounded typed profile. It adds no legal proof standard, evidence weighting, interpretation selection or mixed-profile reasoning. The consumer retains both revisions; a general typed comparison API is deliberately absent.
