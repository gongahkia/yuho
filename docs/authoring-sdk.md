# Experimental graph-authoring and diagram-projection SDK

The `Yuho.Authoring` Haskell library accepts authored semantic graphs, independent
case assertions, and explicitly selected application assessments. It compiles a
bounded fragment to the unchanged `SuppliedProofStatus-v1` backend and returns
object-linked application reports and scenario comparisons. No CLI, renderer,
research-directory lookup, or lexer-token construction is required.

Both the API and `yuho.authoring/v0.1-experimental` JSON format are experimental.
There is no migration or long-term compatibility promise. Unsupported format
versions are rejected at `/documentFormat`. The
[JSON schema](../schema/authoring-v0.1-experimental.schema.json) specifies the
supported serialized fields; semantic validation is performed by the SDK.

## Library flow

Import `Yuho.Authoring`. Construct an `AuthoringDocument` using its record types,
or use `decodeDocument` on supplied UTF-8 bytes. The public operations are:

```haskell
encodeDocument  :: AuthoringDocument -> ByteString
decodeDocument  :: ByteString -> Either AuthoringDiagnostic AuthoringDocument
validateDocument :: AuthoringDocument -> [AuthoringDiagnostic]
validateAnalysis :: AuthoringDocument -> Text -> ValidationReport
compileAnalysis :: AuthoringDocument -> Text
                -> Either [AuthoringDiagnostic] CompiledAnalysis
evaluateAnalysis :: CompiledAnalysis -> Either [AuthoringDiagnostic] Evaluation
compareAnalyses :: Evaluation -> Evaluation
                -> Either [AuthoringDiagnostic] Comparison
```

`encodeRecord` serializes structured validation, application, comparison,
snapshot and mapping records. `CompiledAnalysis` and `Evaluation` have hidden
constructors. Compilation always revalidates; callers cannot substitute an
unchecked request while retaining another artifact's validated state.

`validateDocument` checks the entire document's structure and references without
requiring bindings for every input. `validateAnalysis` adds selected-slice
binding checks and, when complete, compilation's existing kernel checks.
`documentValid` describes authored structure; `analysisReady` additionally
requires a complete, accepted executable request. Missing inputs are reported
with `AMISSING` diagnostics and `openInputs`, so incomplete drafts remain useful.
Compilation and evaluation return errors rather than results for missing inputs.

The lower-level `Yuho.Authoring.Validate.validateBindings` performs adapter checks
without attempting kernel compilation. Prefer the facade's `validateAnalysis`.

## Supported graph and authored information

A `LawDefinition` identifies its definition and revision. Law nodes have globally
unique IDs and kinds `rule`, `input`, `all`, or `any`. Executable `LawEdge`s have
their own IDs and explicit meanings:

| Kind | Direction | Meaning |
| --- | --- | --- |
| `requires` | rule → requirement | Exactly one root requirement per rule. |
| `member` | all/any → requirement | Ordered child; groups have at least two children. |
| `exception` | main rule → guard rule | Defeat the satisfied main branch if the guard is satisfied. |

An analysis selects one rule, with zero or one attached guard. Nested guards,
cycles and shared requirement structures are unsupported and diagnosed. The
fragment is general: no cheating-specific categories, jurisdiction, purpose,
burden, or date constants are imposed. Unrelated input drafts need no active
assessments. Structural errors, including dangling references in unrelated
material, remain document errors. Supported law trees may be used by multiple
analysis instances, but requirement nodes cannot have multiple structural parents.

Nodes retain labels, quotations, citations and original source references.
`lawScope` records the author's represented scope and exclusions; graph validity
does not establish complete or correct legal coverage.

`CaseAssertion` records a description, actor/context scope and optional source
references. It does not establish a classification. `Assessment` separately
identifies its legal input, actor/context, supplied classification, reason,
issuer, origin, basis, assertion references and source references. Its
`Classification` wraps the existing `Proved`, `NotProved`, or
`Unresolved NotDetermined/ExternalDecisionPending` constructors.

`Analysis.analysisAssessments` explicitly selects assessment IDs. There must be
exactly one selected assessment for every input in the main tree and attached
guard tree, even if execution later skips that guard. Multiple retained
alternatives are allowed. Repeated selection, multiple active alternatives,
wrong input kinds, out-of-slice targets and actor/context mismatches are errors.
No array order, recency or status preference resolves ambiguity.

An assessment with basis `case_material` references at least one assertion;
multiple assertion references are provenance, without aggregation semantics.
An explicitly identified `assumption` may have a reason and no assertions.
Referenced assertions may describe other actors or contexts: these links are
retained provenance, not inferred actor relationships. General actor reasoning is
deferred. Origins distinguish
`external_assertion` supplied by a caller from retained `synthetic_fixture` data.

Independent source records have kinds `law`, `case`, `other`, or `synthetic` and
optional locators and retained text. Nothing is fetched from a locator.
`Relationship` supports `chronology`, `support`, and `challenge` as explicitly
non-executable records. They do not infer causation, entailment, or an opposite
conclusion. `Annotation` supports `draft` and `retained` text. Presentation is a
list of object IDs and string-valued properties, including coordinate strings.
It never enters execution. Unknown executable kinds are errors, not annotations.

## Validation responsibilities and provenance

| Adapter checks | Existing kernel checks delegated unchanged |
| --- | --- |
| Version; global IDs; references; supported node/edge meanings; tree shape, sharing and cycles. | Closed protocol fields; generated semantic IDs; registry and exception references; acyclicity. |
| Selected target, explicit binding uniqueness/completeness, assessment/input and actor/context compatibility. | Total leaf bindings, supported classification constructors, assignment identity and issuer/origin fields. |
| Required reasons/issuers, declared assumptions, independent assertion/source references. | Metadata consistency; existing empty penalty structures. |
| Original anchors against retained UTF-8 source text. | Generated source hashes, paths, UTF-8 offsets/columns, span containment, date, node/byte/depth limits. |

The wire decoder additionally rejects duplicate JSON keys, unknown record fields,
documents over one MiB and nesting over 64 containers. Authored documents are
limited to 4096 identified objects; compiled requests use the existing 1024-node
budget, one-MiB budget and depth checks. The supplied reference date must fit the
kernel's four-digit calendar-year representation. The SDK never selects the
applicable law from that date.

Original `SourceRef` anchors are optional. A supplied anchor requires retained
source text and must use half-open UTF-8 byte offsets and one-based byte columns,
matching `Yuho.Core.Source`. A locator or citation without an anchor is retained
without inventing offsets. Span validation does not verify the legal accuracy
of a quotation or citation.

Compilation creates separate `generated_law_projection` and
`generated_assessment_projection` source records. Their kernel spans describe
generated text. `compiledSourceMappings` explicitly connects generated IDs and
spans to authored objects and original references. These offsets are never
presented as statute, case-document, or original `.yh` locations.

`compiledRequirements` distinguishes a legal node, its occurrence path of authored
edge IDs, selected assessment, generated requirement, rule, branch and assignment.
`compiledIdentities` also maps generated guard and source identities. Generated
IDs are local to an artifact, not public aliases for legal input IDs; use the
mapping together with its snapshot. Group dependencies remain authored edge IDs.
The kernel transport request ID is `A00` to satisfy its existing wire grammar;
the SDK's `reportAnalysis`, snapshot and mappings carry the caller's actual
analysis identity.

`compiledSnapshot` retains an immutable copy of the entire document, selected
analysis and evaluator profile. Its SHA-256 identifies deterministic encoding
under the pinned library configuration, including reasons, issuers, case text,
citations, retained alternatives, drafts and presentation. The law fingerprint
includes the law record and its referenced original source records. This is a
local snapshot mechanism, not a cross-version canonicalization guarantee.
Reports carry both snapshot ID and kernel input digest; the latter alone cannot
identify all authorship changes. `evaluationSnapshot` recovers the exact retained
context, including non-executable material. `evaluationCompilation` recovers all
compiler identity/source mappings and the executable artifact alongside a result.

## Reports and comparisons

`evaluationReport` contains per-requirement observations, rule/branch records,
exception behaviour, conclusion and open-input inventory. Input observations
retain the selected assessment and original supplied status/reason, assertions
and sources. Groups have child relationships and computed information, with no
invented assessment. `evaluated` plus `not_satisfied` is different from
`not_evaluated` plus no computed value. `NotProved` remains supplied information
even when projected to technical non-satisfaction; this is no claim of factual
falsity or fulfilment of a legal proof standard.

The existing evaluator skips the guard when main requirements fail or remain
unresolved. Guard observations then retain their supplied assessments and
authored connections, with a skip reason and no fabricated computed status.
An unresolved guard evaluated after satisfied main requirements is separately
reported. The open-input inventory lists `missing` and `unresolved` inputs,
their rule, scope and structural occurrence paths. Those paths are not claims
of decisiveness or outcome sensitivity.

`compareAnalyses` requires identical law definition/revision/referenced sources,
target, actor/context, reference date and evaluator profile. This conservative
comparison can reject reordered law records too. It aligns observations by
authored identity and structural occurrence, never display labels or generated
IDs. It separates selection changes, classification changes, assessment
authorship changes, and referenced assertion/source changes from computed
changes and unchanged observations. New assessments need not change the overall
conclusion. Metadata-only changes do not become computed conclusion changes.
Unrelated retained-document edits remain accessible in the two snapshots rather
than being presented as assessment changes. This is not causal counterfactual
reasoning, interpretation equivalence, or broad law-version comparison.

## Build and run the independent consumer

The [consumer package](../examples/authoring-consumer/yuho-authoring-consumer.cabal)
depends on the exposed `yuho` library. Its [Cheating.hs](../examples/authoring-consumer/Cheating.hs)
constructs both alternatives and the represented exception, independent case
assertions, alternative assessments, chronology/challenge relationships and an
unfinished annotation. Its [Main.hs](../examples/authoring-consumer/Main.hs)
round-trips the document, validates, compiles, evaluates and compares a selected
pending assessment. All data is in the caller; runtime has no repository lookup.

From the checkout, with GHC 9.8.4 and cached pinned dependencies:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline)
cd /tmp
"$consumer_bin" --artifacts /tmp/yuho-authoring-example
```

The consumer prints two JSON records (application and comparison). The optional,
explicit artifact directory receives authored documents, validation/application
reports, inventory, comparison, request/result, snapshot and compiler mappings.
For a fresh Cabal cache, first run `cabal update`, then the same build without
`--offline` to fetch the pinned packages; no dependency upgrade is needed.

Verification from the checkout:

```sh
cabal v2-test yuho-test --offline -j1 --with-compiler=ghc-9.8.4 --test-show-details=direct
python3 test/authoring_consumer.py "$consumer_bin"
make protocols
python3 test/docs.py
```

The consumer check runs in a fresh temporary directory outside the checkout and
validates both authoring documents and the unchanged kernel request/result
schemas. Native SDK tests independently compile the retained cheating `.yh`
model through `compileSource`, decode/validate/evaluate it, and compare scenarios
01, 08, 10 and 05 against separately constructed graphs. An explicit authored-to-
legacy ID table aligns requirement statuses, rule/branch reasons and exception
behaviour; generated IDs, spans, digests and deferred penalty output are excluded
from this semantic comparison. Tests also cover metadata-only differences,
unchanged conclusions, missing/skipped/unresolved distinctions, malformed graphs
and bindings, serialization, snapshots and multibyte anchors/generated offsets.

Existing evaluator proofs do not establish correctness of this translator.
Editors, shared-graph execution, additional backends,
evidence weighing, penalty authoring, sensitivity and broader model comparison
remain outside this SDK fragment.

## Derived diagram projections — Tranche 02

Import `Yuho.Authoring` for the projection operations as well as the authoring
API. A `Projection` has a hidden constructor; `projectionData` exposes its
inspectable records. Projection consumes authorship and observations directly,
without converting through the legacy display graph and without running the
compiler or evaluator:

```haskell
projectAuthored :: AuthoringDocument -> Text
                -> Either [AuthoringDiagnostic] Projection
projectEvaluation :: Evaluation -> Either [AuthoringDiagnostic] Projection
projectEvaluationOn :: AuthoringDocument -> Evaluation
                    -> Either [AuthoringDiagnostic] Projection
projectComparison :: Evaluation -> Evaluation
                  -> Either [AuthoringDiagnostic] ProjectionComparison
resolveProjectedObject :: Projection -> Text -> Maybe ProjectionResolution
encodeProjection :: Projection -> Either [AuthoringDiagnostic] ByteString
lawOccurrenceView :: Projection -> Either [AuthoringDiagnostic] ProjectionView
encodeProjectionLegacyJson :: Projection -> Either [AuthoringDiagnostic] ByteString
encodeProjectionLegacyXml :: Projection -> Either [AuthoringDiagnostic] ByteString
encodeProjectionSvg :: Projection -> Either [AuthoringDiagnostic] ByteString
```

`projectAuthored document analysisId` checks structure, references and binding
ambiguity, but accepts missing assessments. These are retained as `AMISSING`
diagnostics and open inputs. Selected unresolved assessments are separate open
inputs. No computed statuses are manufactured: occurrence evaluation is
`not_requested`. Backend compilation budgets do not determine whether an
otherwise supported draft can be projected. The projection is bounded to 1024
requirement occurrences; traversal overflow is an error rather than truncation.
Structurally ambiguous or invalid documents return object-linked diagnostics.

`projectEvaluation` uses the opaque evaluation's exact immutable snapshot and
existing application report. It retains compiler identities, generated sources
and generated spans without recompilation. `projectEvaluationOn` additionally
requires record equality with a separately supplied document; changes to reasons,
sources, alternatives, drafts or presentation reject the attachment with `PSTALE`.
Use the original snapshot to view an older result alongside newer work. None of
these APIs invokes evaluation implicitly.

### Complete output and identity

The complete derived format is `yuho.analysis-projection/v0.1-experimental`,
specified by the [projection JSON schema](../schema/analysis-projection-v0.1-experimental.schema.json).
It embeds the selected analysis, entire authored snapshot, optional application
report and compiler mappings, projected objects and relationships, diagnostics,
and open-input inventory. It is output, not a complete authoring import format.
Use `encodeDocument`/`decodeDocument` for authorship. A legacy diagram cannot be
imported as a lossless authored analysis.

The identity layers are explicit:

| Layer | Identity and alignment |
| --- | --- |
| Authored object | Original ID retained in the snapshot and `originAuthoredObjects`; `objectProjectionId` gives its projected handle. Law/descriptive relationships also have object handles so annotations can reference them. |
| Structural occurrence | Law fingerprint, selected target, actor/context, authored rule/node and path of authored edges. Assessment selection and generated kernel numbering do not enter this identity. |
| Supplied assessment | Independently projected authored object; `selected` and `bindingState` distinguish selected from retained alternatives. |
| Run observation | Snapshot, profile, category, authored object/path, original kernel and branch IDs. An `observes` link attaches it to a stable occurrence or exception relationship handle. |
| Generated material | Explicit `projection_generated` origin, authored origins, and separate compiler provenance records. Generated source spans are never original anchors. |

Projected IDs are deterministic SHA-256 handles with category prefixes. Distinct
original IDs such as `f:deception` and `f/deception` do not collapse through XML
sanitization. SVG DOM IDs prefix these safe handles with `node-` or `edge-`.
Every encoder validates uniqueness, origins and edge endpoints before encoding;
it cannot silently omit a connection to a missing endpoint. Distinct authored
relationships retain distinct IDs even with identical endpoints and labels.
Hashes use the pinned encoding configuration, not a cross-version canonicalization
promise. The projection API and all three new format versions are experimental.

Each edge separates its `kind` from `semantics`: `law_structure`,
`occurrence_structure`, `assessment_selection`, `assessment_binding`,
`provenance`, `descriptive`, `observation`, `generated_provenance`, or `projection`.
Provenance is not evidence aggregation; chronology/support/challenge remain
descriptive. Selected occurrence nodes reference definitions via `instance_of`.
Sources, original optional anchors, citations, assessment reasons/issuers,
presentation and unfinished annotations remain recoverable through the snapshot.
`resolveProjectedObject` joins an emitted node/edge to applicable law objects,
selected assessment, referenced assertions, original sources/anchors, related
descriptive material and generated mappings in separate fields.

### Supplied, computed and evaluation information

`projectedNodeBinding` retains the assessment ID, supplied classification and
reason. `projectedNodeComputed`, `projectedNodeEvaluation`,
`projectedNodeSkipReason` and `projectedNodeBranchReason` are independent fields.
Groups have dependencies and computed observations, without supplied assessments.

| View/state | Binding | Computed | Evaluation |
| --- | --- | --- | --- |
| Missing draft input | `missing` | absent | `not_requested` |
| Authored unresolved input | selected `unresolved(not_determined)` | absent | `not_requested` |
| Evaluated unresolved input | same supplied classification/reason | `unresolved` | `evaluated` |
| Evaluated `not_proved` input | selected `not_proved` | `not_satisfied` | `evaluated` |
| Skipped exception input | selected assessment retained | absent | `not_evaluated`, with skip reason |

In the pending cheating example, `f:unsoundness-time` remains supplied
`not_proved`, with no computed value and `not_evaluated`: main requirements were
unresolved. An evaluated, satisfied guard instead defeats the main rule. Neither
presentation nor projection changes those evaluator policies or establishes
factual falsity, evidence strength, legal completeness or a proof standard.

### Rendered views and bindings

The reference exports show **only the selected law occurrence tree, including
its exception guard**. Assertions, assessment alternatives, sources, other law
material and annotations remain in the complete projection. The companion
`yuho.projection-view/v0.1-experimental` record enumerates included and omitted
node/edge IDs, SVG DOM bindings, and each legacy edge's array index and rich edge
ID. These are explicit view omissions, not missing projected context. The SVG
embeds this view record in metadata and the occurrence records in node titles.

JSON and XML reference views reuse the unchanged `yuho.semantic-graph/v0.1`
encoders. That legacy contract has neither separate state fields nor edge IDs;
its `status` is left absent to avoid conflating supplied and computed values.
Use the **complete projection plus view bindings** as the machine-readable
contract, rather than relying on a rendered label. An isolated SVG renderer for
the new view prints supplied classification, computed value and evaluation
state in separate columns, with explicit skip/branch explanations. Its readable
labels may abbreviate descriptive titles; full IDs and text remain in the
complete output. Existing legacy entry points and rendering are unchanged.

### Projecting comparisons

`projectComparison` calls `compareAnalyses` and attaches its rows to projected
occurrences/assessment objects. It does not introduce a comparison engine or
infer causal counterfactuals. Each row retains both original run observation
identities and a stable `observationChangeAlignment` handle. It distinguishes a
changed computed field (including becoming absent) from a changed computed value
when both runs evaluated the object, evaluation-state changes and reason changes.
Metadata-only edits can change assessment authorship without changing computed
observations. Unchanged rows remain addressable even though their run IDs differ.

The consumer's proved-to-pending transition has **one assessment change, 20
changed observations and six unchanged**. Four main requirements and the main
rule change computed value (five). Thirteen guard requirements, the guard rule
and the exception attachment become unevaluated (15); their old computed values
are withdrawn. Two rule branch reasons also change; these are overlapping
attributes of those same rows. This is propagation through the represented
structure, not twenty independently changed facts. Another consumer scenario
keeps both alternatives satisfied, then changes the property fault to
`not_proved`: the selected conclusion remains satisfied via the other route.

### Consumer artifacts and verification

The consumer now projects pending authorship and a missing-assessment draft
before evaluating, projects satisfied/pending/defeated runs, maps comparisons,
and recovers the deception assessment's two assertions and retained draft
annotation. Run it outside the checkout with an explicit output path:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
cd /tmp
"$consumer_bin" --artifacts /tmp/yuho-authoring-tranche02
```

Each of `pending-authored`, `draft-authored`, `satisfied`, `pending` and `defeated`
produces `.projection.json` (complete), `.view-bindings.json`, `.view.json`,
`.view.xml` and `.svg`. `comparison-projection.json` and
`alternative-route.comparison-projection.json` retain projected comparison
bindings; `comparison-excerpt.json` is a consumer-selected three-row excerpt with
full projected IDs, original authored IDs and supplied/computed/evaluation states.
Recovery records demonstrate metadata access. The previously documented
native test, protocol and Python consumer commands apply. The consumer checker
validates complete outputs and companion artifacts against the schema's local
`$defs`, parses XML/SVG, verifies every rendered connection/DOM binding, checks
the supplied/computed/skip labels and audits the comparison counts.

Native projection tests additionally cover missing drafts, a bound tree exceeding
the backend compilation budget, stale snapshot rejection, exception defeat,
collision-prone original IDs, parallel relationships, bad emitted endpoints,
multibyte original anchors versus generated spans, stable occurrence alignment,
and metadata-only comparison changes. Projection supports the existing bounded
tree fragment; no renderer layout guarantee is made for arbitrary deep or very
long labelled documents. Interactive layout, authoring imports from projections,
shared-graph execution and additional diagram views remain deferred.

## Case information and focused application — Tranche 03

The case remains independently authored information. Assertions are not reconstructed
from evaluated inputs. An absent application link makes no finding of irrelevance,
falsity, uncertainty or rejection. These additional public operations are exposed
from `Yuho.Authoring`:

```haskell
caseView :: Projection -> Either [AuthoringDiagnostic] ProjectionView
applicationView :: Projection -> ApplicationFocus
                -> Either [AuthoringDiagnostic] ProjectionView
-- FocusInput authoredInputId
-- FocusOccurrence projectedOccurrenceId
-- FocusAssessments [authoredAssessmentId]
validateProjectionView :: Projection -> ProjectionView -> [AuthoringDiagnostic]
encodeViewJson, encodeViewXml, encodeViewSvg
  :: Projection -> ProjectionView -> Either [AuthoringDiagnostic] ByteString
caseAssertionLinks :: Projection -> Text
                   -> Either [AuthoringDiagnostic] AssertionLinks
inspectAssessment :: Projection -> Text
                  -> Either [AuthoringDiagnostic] AssessmentInspection
recoverOriginalSource :: Projection -> SourceRef
                      -> Either [AuthoringDiagnostic] OriginalSourceExcerpt
```

Start with `projectAuthored document analysisId` for case information before
completed application. A selected analysis is still required to establish the
snapshot and selection context; complete bindings and evaluation are not required.
The existing projection validation rules still apply. Neither selecting a view
nor inspecting an object performs compilation, evaluation or external URL fetching.

### Deterministic inclusion and omissions

`caseView` includes **every case assertion**, their directly referenced original
sources, descriptive relationships incident on these assertions/sources and both
endpoints of those relationships. This one-hop rule retains, for example, an
assertion's challenge to an assessment without expanding the assessment's whole
application context. Directly relevant draft/retained annotations are included.
An annotated descriptive relationship also retains its object handle. Remaining
annotation targets stay explicitly omitted rather than causing recursive expansion.
A case view can include an assessment as a descriptive endpoint; that does not
create a selected application or associate a computed result with it.

`FocusInput` and `FocusOccurrence` select one input occurrence in the selected
analysis and include its selected assessment plus retained alternatives for that
input **in the analysis's actor/context scope**. An occurrence focus takes the
stable projected occurrence ID, not a kernel ID. `FocusAssessments` takes one to
four distinct authored assessment IDs and includes exactly those assessments;
only selected bindings add structural occurrences and run observations. An
explicitly requested unselected or differently scoped assessment retains its
legal input definition and provenance without acquiring a computation. Invalid,
ambiguous or oversized focus requests return `PFOCUS` diagnostics.

Both application selections include the assessments' referenced assertions and
sources, the assertions' sources, target law definitions and original law sources,
and directly relevant annotations. Cross-context assertion references are retained
with their recorded scope: they are provenance, not inferred actor relationships.
Chronology/support/challenge edges are included when their endpoints are selected;
they do not expand an application focus. Shared objects keep one projected identity
and distinct relationships are retained.

These reference views are limited to 64 nodes and 128 relationships. Exceeding a
bound returns `PVIEWLIMIT`; nothing is silently truncated. Existing included/omitted
partitions, safe IDs, SVG DOM bindings and legacy edge-index bindings are reused.
Before encoding, the SDK checks snapshot/projection matching, exact partitions,
endpoint closure and bindings. The complete projection and existing format versions
are unchanged. The schema adds only `$defs` for the new inspection/helper records.
The old law-occurrence operations retain their behaviour.
The new JSON/XML reference exports use the legacy format's existing `case` view
category; their complete state and identity contract remains the full projection.

### Inspection, selection and original sources

`caseAssertionLinks projection "assertion:description"` separately returns all
assessment IDs referencing that assertion and those selected for this analysis.
Empty all-links means no assessment link in the document. Non-empty all-links with
empty selected-links means none selected. Neither describes whether an object is
rendered; use view bindings for that distinction.

`inspectAssessment projection "assessment:deception"` returns the original
assessment (scope, supplied status/reason, issuer, origin, basis and references),
its selection state, the existing resolver's assertion/source/context records,
eligible occurrence links and associated observations. For an unselected
alternative, application links have `applicationSelected = False`,
`applicationEvaluation = "not_applicable"`, and no computed value or attributed
observation. The legal occurrence's actual selected result is never copied onto
an alternative. A selected assessment can instead have `not_requested` in an
authored projection, `evaluated`, or `not_evaluated` with the original skip reason.
Selection alone establishes no evaluator visit or reliance.

The pending guard preserves all four dimensions: `assessment:unsoundness-time`
is selected, supplied `not_proved`, has absent computed value, and is
`not_evaluated` because the main requirements were unresolved. An assumption is
labelled with its authored basis and reason; no assertion/source is invented.
Assertion and source cards have no computed legal statuses.

For an original anchored reference:

```haskell
recoverOriginalSource projection
  (SourceRef "source:case-note" (Just (TextSpan 6 15 1 7 1 16)))
-- excerptState = "anchored", excerptText = Just "猫 item."
```

The supplied source text is `Note: 猫 item.\nDelivery reported.`. Offsets are
half-open UTF-8 bytes and columns are one-based UTF-8 byte columns. The existing
span validator checks boundaries and positions before extraction. Invalid anchors
return `PSOURCE`. Unanchored retained text returns `retained_unanchored` without an
excerpt; locator-only sources return `locator_only`, also without an excerpt.
Original source records/anchors and generated compiler mappings occupy separate
fields. None of these links establishes reliability, weight, admissibility or a
legal proof standard.

### Ordinary revision workflow and consumer outputs

[CaseApplication.hs](../examples/authoring-consumer/CaseApplication.hs) is a public
library consumer extending the same cheating model, not another legal model:

1. Clear assessment selections in an immutable document copy and create a case
   view, including an unmapped weather assertion, descriptive relationships,
   original references and a draft annotation.
2. Select the existing assessments, evaluate explicitly, and focus on deception.
   Its selected assessment cites two assertions, including one about another
   actor/context, alongside an unselected proved alternative and shared source.
3. Change only the description of `assertion:description`. Keep the old snapshot
   and evaluation. `projectEvaluationOn revisedDocument oldEvaluation` rejects
   the stale attachment. Compile/evaluate the revised document explicitly: the
   classifications and selected conclusion remain unchanged. The comparison has
   one referenced-material change, no selection/classification/assessment-metadata
   changes, zero changed computed observations and 26 unchanged observations.
4. Explicitly select the pending property-fault assessment. Its supplied status
   is unresolved; the guard is skipped. This separate change has one selected
   assessment transition and 20 changed observations, as explained above.

The comparison's assessment-change rows include `changeReferencedMaterial` even
when the assessment record itself is unchanged. Consumers should read these flags,
rather than treating the number of rows as a count of changed classifications.
Narrative editing does not automatically revise classifications or their reasons;
a caller must decide whether to revise those authored assessments.

Build and run the same separately packaged consumer outside the checkout:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
cd /tmp
"$consumer_bin" --artifacts /tmp/yuho-authoring-tranche03
```

New output stems are `case-before`, `application-selected`, `application-revised`,
`application-pending` and `application-skipped`. Each has a complete
`.projection.json`, `.view-bindings.json`, `.view.json`, `.view.xml` and `.svg`.
`assessment-resolution.json`, `alternative-resolution.json` and
`skipped-resolution.json` demonstrate inspection; `resolution-excerpt.json` is a
compact recovery example. `revision-excerpt.json`,
`narrative.comparison-projection.json`, `explicit-selection.comparison-projection.json`
and stale-attachment diagnostics retain the revision evidence and prior snapshots.
The established native, protocol, docs and independent-consumer checks cover these
outputs too. Optional PNG previews can be created with:

```sh
rsvg-convert --output /tmp/yuho-authoring-tranche03/application-selected.png /tmp/yuho-authoring-tranche03/application-selected.svg
```

The SVG uses readable cards and numbered, typed connections with a relationship
legend. It is a reference navigation view, not an interactive layout engine.
Dense gutter routes and long unbroken identifiers can reduce readability; focus
more narrowly or use the complete contract in a downstream renderer. Full
identities and metadata remain in the complete projection and DOM bindings.
The next validation should use a materially different legal model; no additional
model or further reference-view family is implemented here.
