# Experimental graph-authoring and diagram-projection SDK

The `Yuho.Authoring` Haskell library accepts authored semantic graphs, independent
case assertions, and explicitly selected application assessments. It compiles a
bounded fragment to the unchanged `SuppliedProofStatus-v1` backend and returns
object-linked application reports and scenario comparisons. No CLI, renderer,
research-directory lookup, or lexer-token construction is required.

## Recommended reading path

1. Start with the [tested Haskell quickstart](authoring-quickstart.md): local Cabal
   dependency, pinned compiler, and a complete load → anchor → select → validate →
   evaluate → inspect/export → edit → save/reload workflow.
2. Use the [current API map](#current-api-map) below to find operations and record
   accessors, then the [export recipe](#export-recipe) for named output files.
   For a cohesive diagram interaction, follow [focus, reveal and revise](#focus-reveal-and-revise).
3. Consult this guide's detailed contracts as needed: [authored fragment](#supported-graph-and-authored-information),
   [projection identities and snapshots](#derived-diagram-projections--tranche-02),
   [case/application views](#case-information-and-focused-application--tranche-03), and
   [validated source anchors](#validated-original-source-anchors--tranche-06).

The tranche headings retain implementation history and detailed contracts; they
are not a required sequential tutorial. Manual original-source coordinate
construction has been superseded by the checked anchor constructors. Repeated
export calls are handled in the local example below, without a new public SDK
export abstraction. The foundational experimental SDK implementation phase is closed.

Both the API and `yuho.authoring/v0.1-experimental` JSON format are experimental.
There is no migration or long-term compatibility promise. Unsupported format
versions are rejected at `/documentFormat`. The
[JSON schema](../schema/authoring-v0.1-experimental.schema.json) specifies the
supported serialized fields; semantic validation is performed by the SDK.

## Current API map

Import **`Yuho.Authoring`** for all entries below. The public record accessors are
available from that facade; no implementation imports or lexer tokens are needed.

| Caller task | Operations and accessors |
| --- | --- |
| Construct or load editable input | `AuthoringDocument`, `LawDefinition`, `LawNode`, `LawEdge`, `CaseAssertion`, `Assessment`, `Analysis`; `decodeDocument` / `encodeDocument` |
| Attach original sources | `SourceRecord`, `sourceAnchorCodePoints` / `sourceAnchorBytes`, `SourceRef`; `sourceText`, `assertionSources`, `assessmentSources` |
| Select explicitly and edit | `selectAssessment`, `editLawNode`, `editLawEdge`, `editCaseAssertion`; `documentAnalyses`, `analysisId`, `analysisAssessments`, `assessmentId`; add retained alternatives by updating `documentAssessments` with explicit distinct IDs, then validate |
| Check draft/readiness | `validateDocument`, `validateAnalysis`; `documentValid`, `analysisReady`, `validationDiagnostics`, `openInputs`; diagnostic `diagnosticCode`, `diagnosticObjects`, `diagnosticLocation` |
| Compile and evaluate | `compileAnalysis`, `evaluateAnalysis`; `compiledSnapshot`, `compiledRequirements`, `evaluationCompilation`, `evaluationReport`, `evaluationSnapshot` |
| Inspect selected input results | `reportRequirements`; `observationNode`, `observationRule`, `observationOccurrence`, `observationAssessment`; `assessmentClassification`, `assessmentReason`; `observationComputed`, `observationEvaluation`, `observationSkipReason` |
| Inspect conclusions and guard behaviour | `reportConclusion`, `reportRules`, `reportExceptions`; `ruleBranchReason`, `exceptionEvaluation`, `exceptionComputed`, `exceptionSkipReason` |
| Retain context and project | `snapshotId`, `snapshotDocument`, `snapshotAnalysis`; `projectAuthored`, `projectEvaluation`, `projectEvaluationOn`, `projectionData`, `projectionSnapshot` |
| Recover provenance | `inspectAssessment`, `inspectionAssessment`, `inspectionSelected`, `inspectionApplications`, `inspectionResolution`, `resolvedAssertions`; `resolveProjectedObject`, `recoverOriginalSource`, `excerptText` |
| Compare compatible runs | `compareAnalyses`, `projectComparison`; `comparisonAssessments`, `comparisonChanged`, `comparisonUnchanged`, `comparisonConclusionChanged` |
| Select and export a view | `lawOccurrenceView`, `caseView`, `applicationView`; `viewIncludedNodes`, `viewOmittedNodes`, `viewIncludedEdges`, `viewOmittedEdges`, `viewNodeBindings`, `viewEdgeBindings`; encoders below |
| Explain a requirement without graph joins | `focusRequirement`, `AuthoredRequirement`, `RequirementOccurrence`; `explanationSelected`, `explanationAlternatives`, `explanationDependencies`, `explanationAncestors`, `explanationRules`, `explanationExceptions`; `explanationView`, `defaultExplanationOptions` |

An authored input definition, its structural occurrence, a selected assessment,
and a run observation have separate identities. Supplied classification,
selection, computed consequence and evaluation/skip state are separate fields.
`observationAssessment` gives the selected assessment for that occurrence; array
order among `documentAssessments` does not select anything. A selected guard can
still be skipped. Narrative edits do not revise supplied classifications.
Law-record edits can make comparisons incompatible, even when only a label changed.

## Export recipe

These outputs serve different purposes; keep their filenames distinct:

| Artifact | API | Role |
| --- | --- | --- |
| `pending.document.json` | `encodeDocument` | Editable authored interchange; reload with `decodeDocument`. |
| `pending.application-report.json` | `encodeRecord (evaluationReport result)` | Object-linked results, not a diagram-view JSON file. |
| `pending.projection.json` | `encodeProjection` | Complete derived snapshot, authorship, observations and mappings. |
| `pending.law.bindings.json`, `pending.case.bindings.json`, `pending.application.bindings.json` | `encodeRecord view` | Included/omitted objects, rendered IDs and edge-index mappings for that particular view. |
| `pending.law.view.json`, `.view.xml`, `.svg` | `encodeProjectionLegacyJson`, `encodeProjectionLegacyXml`, `encodeProjectionSvg` | Dedicated law-occurrence reference exports, including the represented guard. |
| `pending.case.view.json`, `pending.application.view.json` (and `.view.xml`, `.svg`) | `encodeViewJson`, `encodeViewXml`, `encodeViewSvg` | Generic encoders for an explicitly constructed case or application view. |

The JSON/XML views use the legacy semantic-graph format, whose single status
field cannot carry the complete state distinctions. The complete projection and
bindings supply that contract. SVG is a readable reference view. None is a
lossless substitute for the authored document. Original source anchors and
generated kernel spans stay separate in the complete projection.

Here is a **caller-local** recipe using only the public facade. It consumes one
existing evaluation; projecting and exporting do not rerun the evaluator. The
independent [hurt consumer](../examples/authoring-consumer/Hurt.hs) uses the same
two encoder paths in its local `exportLaw` / `exportView` helpers.

```haskell
{-# LANGUAGE OverloadedStrings #-}
module ExportRecipe (exportRun) where

import Control.Monad (forM_, unless)
import qualified Data.ByteString as BS
import System.Directory (createDirectoryIfMissing)
import System.FilePath (takeDirectory)
import Yuho.Authoring

require :: Show e => Either e a -> IO a
require = either (fail . show) pure

exportRun :: FilePath -> Evaluation -> ApplicationFocus -> IO ()
exportRun stem result focus = do
  createDirectoryIfMissing True (takeDirectory stem)
  let snapshot = evaluationSnapshot result
  BS.writeFile (stem ++ ".document.json") (encodeDocument (snapshotDocument snapshot))
  BS.writeFile (stem ++ ".application-report.json") (encodeRecord (evaluationReport result))
  p <- require (projectEvaluation result)
  require (encodeProjection p) >>= BS.writeFile (stem ++ ".projection.json")
  law <- require (lawOccurrenceView p)
  cases <- require (caseView p)
  application <- require (applicationView p focus)
  let writeView name view encodings = do
        unless (null (validateProjectionView p view)) (fail "invalid view bindings")
        BS.writeFile (stem ++ "." ++ name ++ ".bindings.json") (encodeRecord view)
        forM_ (zip ["view.json", "view.xml", "svg"] encodings) $ \(suffix, bytes) ->
          require bytes >>= BS.writeFile (stem ++ "." ++ name ++ "." ++ suffix)
  writeView "law" law
    [encodeProjectionLegacyJson p, encodeProjectionLegacyXml p, encodeProjectionSvg p]
  writeView "case" cases
    [encodeViewJson p cases, encodeViewXml p cases, encodeViewSvg p cases]
  writeView "application" application
    [encodeViewJson p application, encodeViewXml p application, encodeViewSvg p application]
```

### Two application questions from the same result

For the hurt scenario `05_offence_causation_unresolved`, resolve the selected
causation assessment from the **actual report**, checking that there is exactly
one occurrence in this bounded model. A caller with several occurrences must
also disambiguate by `observationRule` / `observationOccurrence`.

```haskell
let inputId = "f:hurt-caused-by-act"
selected <- case [r | r <- reportRequirements (evaluationReport result),
                     observationNode r == inputId] of
  [r] -> maybe (fail "missing selected assessment") pure (observationAssessment r)
  _ -> fail "expected exactly one causation occurrence"
exportRun "out/pending-selected" result (FocusAssessments [assessmentId selected])
exportRun "out/pending-input" result (FocusInput inputId)
```

`FocusAssessments` answers “why this supplied assessment?” with its cited
assertions/sources, legal target and associated selected-run observation.
`FocusInput` answers “what assessments were retained for this input?” and adds
the unselected alternatives in the analysis scope. Alternatives keep their own
supplied classifications and receive no selected-run computation. Both exports
retain the same complete projection and have separate omission bindings. A
provenance edge does not mean that case material automatically proves an input.
Assertion-card assessment-link counts describe the whole document/current
analysis, not just the assessments included in this focus.

Generate the existing consumer's two views with the pinned setup, then run from
outside the checkout (replace the output directory if desired):

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
cd /tmp
"$consumer_bin" --model hurt --artifacts "$HOME/Downloads/yuho-review/consumer-trial-follow-up/hurt"
```

`hurt-05-selected-application.svg` explains the report-selected assessment;
`hurt-05-application.svg` includes the retained alternatives. Their complete
projections, JSON/XML views and `*.view-bindings.json` companions are under
`data/`. Convert either SVG with `rsvg-convert --output FILE.png FILE.svg`.
The separate `data/hurt-05_offence_causation_unresolved.application.json` is an
evaluation report, while `data/hurt-05-application.view.json` is a diagram view.
Shared provenance can still make the gutter and numbered legend dense; choose
the focus for the question, rather than treating fewer objects as a readability guarantee.

## Focus, reveal and revise

`Yuho.Authoring` re-exports the small `Yuho.Authoring.Interaction` adapter:

```haskell
focusRequirement :: Projection -> RequirementFocus
                 -> Either [AuthoringDiagnostic] RequirementExplanation
explanationView :: Projection -> RequirementFocus -> ExplanationOptions
                -> Either [AuthoringDiagnostic] ProjectionView
```

`AuthoredRequirement inputOrGroupId` resolves within the projection's selected
analysis and actor/context scope. `RequirementOccurrence projectedOccurrenceId`
uses its structural handle; a definition handle or run-observation ID is rejected.
Unknown/out-of-scope focus requests return `IFOCUS` with the request and analysis
IDs. The adapter supports inputs, all/any groups and rules, including identifiable
drafts projected before bindings are complete. It never compiles or evaluates.

The explanation joins the focused `LawNode`, definition handle, occurrence and
optional run observation. It retains citation/source references, the selected
`AssessmentContext`, compatible unselected alternatives, immediate dependencies,
parents and ancestor connections with their original law-edge records. It also
returns the existing selected-analysis rule and exception observations. Exception
attachments stay typed attachments, not extra conjunctive requirements; structural
ancestry is not a claim of causal influence. A group has child dependencies and
computed information, without a supplied assessment.

`contextAssessment` preserves classification, complete reason, issuer, origin,
basis and scope. `contextAssertions` and `contextAssertionLinks` provide case
material and reverse links to its assessments; cross-context provenance is
retained. `contextApplications` distinguishes selection from actual evaluation.
Alternatives retain their supplied classifications and have no attributed run
observation or computed value. Missing bindings, selected unresolved assessments,
evaluated `not_proved`, and selected-but-skipped guards remain distinct.

`contextSourceReferences` / `explanationSourceReferences` contain original
references, not expanded source documents. Use `recoverOriginalSource` with the
same projection to reveal an explicitly chosen reference. It returns the retained
source and an excerpt only for a valid original anchor. Locator-only and unanchored
references remain so; no URL is fetched and no source reliability is inferred.
Generated kernel mappings remain separately accessible in the complete projection.

This is a compact sequence over the supplied section 441 example (in an `IO`
consumer, `require = either (fail . show) pure`):

```haskell
p <- require (projectEvaluation original)
let focus = AuthoredRequirement "remain:unlawful"
explanation <- require (focusRequirement p focus)
view <- require (explanationView p focus defaultExplanationOptions)
-- Inspect contextAssessment / contextAssertions / contextApplications in
-- explanationSelected; list explanationAlternatives without selecting one.
let requestRefs = [ref | ref <- explanationSourceReferences explanation,
                        referenceSource ref == "source:B"]
revealed <- traverse (require . recoverOriginalSource p) requestRefs
-- Opening sources and changing view options leave original's snapshot intact.
expanded <- require (explanationView p focus (ExplanationOptions False ["source:B"]))
alternatives <- require (explanationView p focus (ExplanationOptions True []))
let snapshot = evaluationSnapshot original
    analysisKey = analysisId (snapshotAnalysis snapshot)
candidate <- require (selectAssessment analysisKey "position:E" (snapshotDocument snapshot))
let validation = validateAnalysis candidate analysisKey
unless (analysisReady validation) (fail (show validation))
revised <- require (compileAnalysis candidate analysisKey >>= evaluateAnalysis)
aligned <- require (projectComparison original revised)
-- Encode views using encodeViewJson/Xml/Svg with p, alongside encodeProjection
-- and encodeRecord view. Keep revised exports paired with projectEvaluation revised.
```

This uses the existing edit, validation, evaluation and comparison APIs; there is
no implicit commit, mutable session, background evaluation or new comparison
engine. `projectComparison` retains both observation identities and stable
occurrence alignments for changed **and unchanged** rows, separate flags for
computed/evaluation/reason changes, and assessment-selection/classification
changes. Consumers can highlight those handles on any compatible view. A changed
input need not change the selected conclusion. Incompatible law comparisons and
stale `projectEvaluationOn` attachments retain their existing rejections.

The default `explanationView` begins with the requirement occurrence and result,
then the selected assessment and its reason, then immediate case assertions.
Group views include immediate requirement dependencies. Sources are omitted until
their IDs are explicitly requested in `expandedOriginalSources`; alternatives are
omitted unless `includeAlternativeAssessments` is true. Options are **view state**,
not fields in an authored document. Sources/alternatives never disappear from the
complete projection. Each selection records all inclusion/omission and DOM/index
bindings using the existing view format. Definition and observation objects may
be omitted from this compact rendering while remaining separately identified in
the explanation and complete projection. Limits of four assessments, 64 nodes
and 128 relationships return errors, never truncation. All compatible alternatives
remain available in the explanation even if an expanded reference view exceeds
those limits. Expanded alternatives bind to the separate authored definition;
only the selected assessment links to the evaluated occurrence. Source expansion
must name sources referenced by the focused law or the assessments/case material
included in that view; unrelated or duplicate requests return `ISOURCE`.

No existing format version changes. Explanation records can be inspected or
encoded with `encodeRecord`; they are reports, not a new authoring import format.
The reference driver's interaction trace and highlight overlay are caller-local
records, not a new serialized SDK protocol.

### Run the headless reference interaction

The [driver](../examples/authoring-consumer/InteractionDemo.hs) uses an unchanged
[section 441 authored document](../examples/authoring-consumer/fixtures/section441.document.json)
copied verbatim from the independent original-authoring exercise, SHA-256
`4f9d42f57931a2af80f51f02b9417fa442530452cd23dd734139d36fccddcf9b`.
It retains the published 2020 Revised Edition, bounded modelling scope, synthetic
packet and original P/E/N reasons; no current legal-completeness claim is made.
The same operations run over hurt, retaining the consumer's explicit scope-
acknowledgement gate. Bare SDK compilation has no new admission policy.

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
yuho_checkout=$(pwd)
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
cd /tmp
"$consumer_bin" --interact "$yuho_checkout/examples/authoring-consumer/fixtures/section441.document.json" "$HOME/Downloads/yuho-review/tranche07"
```

The file argument is explicit; the executable does not discover checkout files
at runtime. `data/*.interaction.json` records focus, on-demand source recovery,
alternatives, explicit selection, validation, both snapshots and aligned changes.
`s441-focus.svg` starts with the unresolved requirement and P assessment, rather
than the stipulation packet. Expanded-source and alternative views use the same
snapshot. The revised focused output and existing law-occurrence view use
comparison-derived dashed outlines to mark changed observations; unchanged law
rows retain plain outlines. This overlay is local reference presentation only.
Complete projections, exact view bindings, JSON/XML views and all original data
are retained beside the SVGs. The diagrams remain scrolling reference outputs;
applications own canvas layout, controls and navigation.

From the checkout, verify the driver and its saved outputs with:

```sh
python3 test/interaction_consumer.py "$consumer_bin" --existing-artifacts "$HOME/Downloads/yuho-review/tranche07"
```

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

The law-occurrence reference exports introduced in Tranche 02 show **only the
selected law occurrence tree, including its exception guard**. The later
[case/application views](#case-information-and-focused-application--tranche-03)
provide other selections. Assertions, assessment alternatives, sources, other
law material and annotations remain in the complete projection. The companion
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
Tranche 03 added no further legal model or reference-view family. The second-model
validation below uses these existing operations.

## Second-model validation: voluntary hurt — Tranche 04

[Hurt.hs](../examples/authoring-consumer/Hurt.hs) is an independently authored
public-library example of the retained
[hurt research model](../research/singapore/section-84-pilot/hurt-offence/section323-with-section84.yh).
It constructs ordinary `LawNode`, `LawEdge`, `CaseAssertion`, `Assessment` and
`Analysis` records. It never reads the checkout, constructs Surface tokens/ASTs,
or calls the legacy lowerer. The executable includes all its resources.
The default consumer still runs the cheating workflow; `--model hurt` selects
this separate example.

The hurt rule requires an act, hurt, act-to-hurt causation, and **either** intention
or knowledge. Cheating instead combines deception with an alternative between
two conjunctive forms. Both attach the bounded, acyclic section 84 guard.
No new evaluator semantics or public formats are needed. The saved hurt model
and scenarios are unchanged from `bf29ba84b10448479ae364ab4d4d95db557abc4e`.

### Scope and source boundaries

This is a bounded research model with synthetic supplied classifications, not a
statement of complete or currently applicable criminal law. Three exact scope
assumption IDs are retained as annotations about the selected rule and analysis:

| Retained acknowledgement | Meaning |
| --- | --- |
| `a:outside-section-323A` | Assume the case is outside section 323A. |
| `a:outside-section-334` | Assume the case is outside section 334. |
| `a:post-2022-section-84-expression-applicable` | Assume applicability of the represented post-2022 section 84 expression. |

`lawScope` retains these meanings and the explicit omissions. An annotation also
retains the saved section 323 exception wording; another retains the section 107
burden annotation. None is a computed legal conclusion, temporal selection,
proof-standard assessment, or implementation of section 323A/334 doctrine.

The **legacy** checker requires all declared acknowledgements, rejecting missing
ones with `SFE022`. Native checks execute all three retained missing-acknowledgement
scenarios. The **SDK** checks annotation identities/references and ordinary
structural/binding invariants; it does not interpret free-text scope or require
these model-specific acknowledgement IDs. A focused test establishes that boundary
explicitly. A caller needing a mandatory acknowledgement gate must supply that
policy; copying retained context alone is not such a check.

Law quotations copy only saved excerpts from the retained model. The associated
source record is locator-only, with no invented original statute span or fetched
text. The synthetic case note retains its own original text and an explicit UTF-8
anchor: bytes `[11,60)` recover `Mei reports pain (痛) in her arm after the push.`
Generated kernel text/spans remain in the existing compiler-provenance fields.

### Public workflow and observations

For example, using the data exported by `Hurt`:

```haskell
anchor <- hurtNoteAnchor
let document = hurtDocument anchor
    draftDocument = hurtDraft anchor
-- Missing bindings do not prevent authored case projection.
before <- projectAuthored draftDocument hurtAnalysis
caseDiagram <- caseView before
-- Compilation of draftDocument separately reports thirteen AMISSING diagnostics.

compiled <- compileAnalysis document hurtAnalysis
evaluated <- evaluateAnalysis compiled
projection <- projectEvaluation evaluated
focused <- applicationView projection (FocusInput "f:hurt-caused-by-act")
detail <- inspectAssessment projection
  (hurtAssessmentId "f:hurt-caused-by-act" Proved)
excerpt <- recoverOriginalSource projection anchor
```

These lines describe an `Either [AuthoringDiagnostic]` flow. The consumer uses a
small IO helper to display any diagnostics and write exports. Explicit immutable
document updates select different assessment IDs; all alternatives remain retained.
The causation assessment references three assertions, including Mei's clinic-note
scope as provenance within Alex's incident analysis. No actor relation, evidence
weight or causal inference follows from that reference. A separate weather assertion
has no application link. The draft shows retained-but-unselected links separately
from this unmapped assertion; neither receives a computed status.

Each scenario selects thirteen assessments, including all guard inputs. Unselected
`proved` alternatives keep their classification and provenance without receiving
the selected run's observation. Section 84 assessments are expressly synthetic
assumptions, without fabricated case evidence. The example also revises the case
narrative: stale attachment fails with `PSTALE`, explicit reevaluation preserves
the supplied classifications and computation, and comparison flags referenced
material rather than computed change.

| Scenario | Legacy and SDK conclusion | Main branch reason | Guard |
| --- | --- | --- | --- |
| 01 intention | `satisfied` | `satisfied` | evaluated, `not_satisfied` |
| 02 knowledge | `satisfied` | `satisfied` | evaluated, `not_satisfied` |
| 03 hurt not proved | `not_satisfied` | `requirements_not_satisfied` | skipped |
| 05 ordinary causation unresolved | `unresolved` | `requirements_unresolved` | skipped |
| 06 nature route | `not_satisfied` | `defeated` | evaluated, `satisfied` |
| 11 section 84 unresolved | `unresolved` | `exception_unresolved` | evaluated, `unresolved` |

Native `HurtChecks` independently parses/checks/lowers the unchanged `.yh` model
and each scenario, decodes and validates that request, then evaluates it. An explicit
20-requirement mapping and two-rule mapping compare all input/group statuses,
supplied classifications and unresolved reasons, execution states, branch reasons,
and exception attachment/firing/skip behaviour against the separately constructed
SDK document. Generated IDs, request digests and offsets are not aligned as legal
identities. Handwritten expectations additionally check the table above.

Scenarios **01 → 02** change two selected assessments/classifications and two
input observations; 21 observations, including the overall satisfied conclusion,
remain unchanged. Scenarios **05 → 11** change four selected assessments, with
18 changed and five unchanged observations despite the same unresolved conclusion:
two ordinary observations become satisfied; thirteen guard requirements, its rule
and attachment become evaluated (15); the main rule's reason changes (one).
These are overlapping structural consequences, not 18 independently changed facts.
Original run identities remain separate from stable occurrence alignment.

Repeated `f:unsoundness-time` identifiers are document-local. Pass the correct
projection to inspection, and use snapshot plus occurrence identity for run context.
Native checks resolve this input in both models with distinct scope/occurrences,
and reject a hurt-versus-cheating comparison with `AINCOMPATIBLE`.

### Build, run and review

From the checkout (pinned GHC 9.8.4 and frozen dependencies):

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
cabal v2-test yuho-test --offline -j1 --with-compiler=ghc-9.8.4 --test-show-details=direct
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
python3 test/authoring_consumer.py "$consumer_bin"
python3 test/hurt_consumer.py "$consumer_bin"
make protocols docs
cd /tmp
"$consumer_bin" --model hurt --artifacts /Users/gabrielongtemasek/Downloads/yuho-review/tranche04
```

The two Python checks each execute the consumer in a temporary directory outside
the checkout. The hurt check validates authored/kernel/projection/helper schemas,
all nine JSON/XML/SVG exports, endpoint and inclusion/omission bindings, canonical
states, comparisons and recovery. To verify saved review artifacts as well, add
`--existing-artifacts /Users/gabrielongtemasek/Downloads/yuho-review/tranche04`
to `test/hurt_consumer.py`.

`INDEX.md` in the artifact directory explains the outputs. Six
`hurt-NN_SCENARIO.svg` files show the existing law-occurrence table; the case view
is `hurt-case-before.svg`. `hurt-05-application.svg` focuses on ordinary causation,
including selected unresolved and unselected alternatives with their provenance.
`hurt-11-application.svg` focuses narrowly on the selected unresolved nature-incapacity
assumption; other guard prerequisites remain explicit omissions in its view bindings.
The complete context is retained in `data/*.projection.json`. All six documents,
application reports, kernel requests/results, both comparisons, inspection/excerpt,
revision and diagnostic records are also under `data/`.

Render PNG previews outside the checkout:

```sh
cd /Users/gabrielongtemasek/Downloads/yuho-review/tranche04
for svg in *.svg; do rsvg-convert --output "${svg%.svg}.png" "$svg"; done
```

Use `encodeProjectionSvg` for the law table and `encodeViewSvg` for case/application
cards, with their respective bindings. The complete projection is the full contract;
the legacy JSON/XML view remains a presentation subset. No version change is made.
The SVG actor caption now reads **Scope actor**, preserving its underlying value.
Long reference tables require scrolling; provenance gutters become dense when several
alternatives share sources. Existing focus limits (four assessments, 64 nodes,
128 relationships) remain explicit errors, never truncation.

At the end of Tranche 04, observed friction included repeated record/edge/assessment
construction, manual byte anchors, separate export helpers and caller scope
acknowledgements. Subsequent work added the [ID-addressed editing operations](#editing-and-explicit-caller-acknowledgement--tranche-05),
an explicit consumer acknowledgement check, and [validated anchor constructors](#validated-original-source-anchors--tranche-06).
Manual original-source coordinate construction is no longer required. Repeated
model construction and explicit export calls remain caller work; the current
[export recipe](#export-recipe) shows a local helper. The second model required no
law-specific library branch or builder redesign; omitted doctrines remain out of scope.

## Editing and explicit caller acknowledgement — Tranche 05

The independent consumer now has a third invocation, `--edit-demo`, implemented
in [Editing.hs](../examples/authoring-consumer/Editing.hs). The cheating default
and `--model hurt` remain available. This is an immutable record-editing workflow,
not an editor, patch language, revision service or undo framework.

### Small ID-addressed operations

`Yuho.Authoring` now re-exports [Yuho.Authoring.Edit](../src/Yuho/Authoring/Edit.hs):

```haskell
editLawNode :: Text -> (LawNode -> LawNode) -> AuthoringDocument
            -> Either [AuthoringDiagnostic] AuthoringDocument
editLawEdge :: Text -> (LawEdge -> LawEdge) -> AuthoringDocument
            -> Either [AuthoringDiagnostic] AuthoringDocument
editCaseAssertion :: Text -> (CaseAssertion -> CaseAssertion) -> AuthoringDocument
                  -> Either [AuthoringDiagnostic] AuthoringDocument
selectAssessment :: Text -> Text -> AuthoringDocument
                 -> Either [AuthoringDiagnostic] AuthoringDocument
-- selectAssessment analysisId assessmentId document
```

The three edit helpers locate exactly one typed record, call the supplied update,
and replace it at its existing list position. They preserve the original authored
ID and all other document records. This replaces repeated list scans whose
unknown-ID case could silently do nothing. `ENOTFOUND`, `ETYPE`, `EDUPLICATE` and
`EIDENTITY` identify absent IDs, the wrong record collection, duplicate identities
in the document-wide namespace, and an attempted ID change. Callbacks can change a
node's executable kind or an edge endpoint; **successful addressing is not validation**.
An invalid edited candidate remains available for diagnostics and repair.

`selectAssessment` explicitly replaces the single current binding for that legal
input, preserving its position; if missing, it appends the requested binding.
It retains every alternative assessment. It rejects unknown/wrong-kind IDs,
wrong scope (`ESCOPE`), non-input or out-of-slice targets (`ETARGET`), dangling
existing selections, and multiple existing bindings for that input (`EAMBIGUOUS`).
It never selects by recency, array order or classification. Other missing bindings
can remain in a draft. Neither selection nor editing invokes evaluation.

The helpers do not validate unrelated malformed material, repair it, rename IDs,
or cascade deletion. No deletion helper is introduced. A caller performing direct
record removal must run validation; existing diagnostics identify dangling law,
assessment, annotation or source references. Compilation still rejects invalid drafts.
Appending a new assessment is an ordinary record update followed by
`validateDocument`, whose existing `ADUPLICATE`/reference checks cover conflicts.
Updating the law revision and presentation remains an ordinary record update.

All four helpers are demonstrated for **both hurt and cheating** in the editing
consumer and native checks, including preservation of cheating presentation metadata.
No public serialized format, strict decoder or evaluator protocol changes.

### The structural session

The consumer starts with the unchanged hurt intention scenario. It edits a display
label while retaining `f:act-performed`; fresh evaluation preserves the input/group,
rule and exception computations. The exact snapshot and law fingerprint change.
`compareAnalyses` conservatively rejects this changed law record with `AINCOMPATIBLE`.
`projectEvaluationOn` rejects attaching the old result with `PSTALE`; the old result
remains inspectable using its own snapshot.

A separate copy is prominently labelled **SDK EXPERIMENT**, with revision
`sdk-experiment-any-to-all-v1`. It changes `g:section321-fault` from `any` to `all`.
This deliberately hypothetical exercise is not a proposed interpretation of the
retained law. Intention remains supplied proved and knowledge not proved: the fault
group and ordinary requirements become `not_satisfied`, the main branch reports
`requirements_not_satisfied`, and the exception guard is skipped with no computed
value. Each law version is evaluated independently; no law-version comparison
semantics are added.

```haskell
candidate <- editLawEdge "edge:g:section321-fault/f:knowledge-hurt-likely"
  (\e -> e {edgeTo="draft:disconnected-knowledge"}) experiment
-- validateAnalysis candidate hurtAnalysis exposes the edge/endpoint errors.
-- compileAnalysis candidate hurtAnalysis returns diagnostics, not an artifact.
repaired <- editLawEdge "edge:g:section321-fault/f:knowledge-hurt-likely"
  (\e -> e {edgeTo="f:knowledge-hurt-likely"}) candidate
-- Caller checks analysisReady (validateAnalysis repaired hurtAnalysis).
compiled <- compileAnalysis repaired hurtAnalysis
result <- evaluateAnalysis compiled
projection <- projectEvaluation result
```

The repair exactly restores the preceding experimental document, including list
order and retained authorship. Encoding/strict decoding preserves the repaired
record; reevaluation produces the same kernel response. Invalid drafts are saved
with validation/compile/projection diagnostics and **no evaluated result**.
Authored IDs remain stable through these edits; derived occurrence IDs may change
with the law fingerprint. Stable authored identity is not a guarantee of stable
projection identity across incompatible revisions.

### Case edits, alternative addition and explicit selection

The case branch starts independently from the original law. `editCaseAssertion`
revises `assertion:pain`, retaining its declared Mei/clinic scope and source anchor.
Existing assessment classifications and selections remain untouched. The compatible
comparison flags referenced material, with no changed computed observations.

A record append adds `assessment:hurt:causation-review-v2` as an unresolved
`case_material` assessment with three explicit assertion references. Validation
checks its new identity and references. It is initially unselected: a fresh run
and comparison show no selected-assessment or computed changes. Only a subsequent
`selectAssessment` call activates it. The ordinary causation input becomes unresolved,
the conclusion becomes unresolved, and the guard is selected but skipped.
The focused application view includes this selected assessment and the retained
proved alternative, which has no attributed run observation. A separate authored
draft removes the new binding: its inventory says `missing`, with no computation.
No narrative edit automatically revises a supplied legal classification.

### Consumer acknowledgement guarantee

[Acknowledgements.hs](../examples/authoring-consumer/Acknowledgements.hs) is a small
**consumer-only** admission check. Its explicit inputs are a policy containing
required IDs and a context, and a separate caller acknowledgement list/context.
The hurt workflow passes the three retained scope-assumption IDs explicitly.
`hurtRequiredAssumptions` and `hurtExampleAcknowledgements` are separate explicit
lists; adding a requirement does not automatically acknowledge it for the caller.
It does not derive acceptance from annotations, `retained` state, `lawScope`,
or legal classifications. Acknowledgement accepts a modelling assumption; it does
not establish that assumption's truth or legal adequacy.

`evaluateAcknowledged policy supplied document analysisId` checks the current inputs
before calling the unchanged `compileAnalysis`/`evaluateAnalysis`. Its context
includes law ID, revision and existing law/source fingerprint, analysis ID, selected
target, actor/context scope and reference date. It rejects:

- Each omitted requirement with `ACKMISSING`.
- Entries outside the explicit required set with `ACKUNKNOWN`.
- Repeated acknowledgements with `ACKDUPLICATE`.
- Inapplicable policy/acknowledgement context with `ACKCONTEXT`.
- Empty, duplicate or blank requirement sets with `ACKPOLICY`.

Failure returns separate acknowledgement and SDK diagnostic lists, with no evaluation
or success receipt. Missing acknowledgement never becomes a legal status or graph
node. Successful admission returns an evaluation plus a separate receipt containing
the requirements, supplied acknowledgements, analysis and exact resulting snapshot.
That receipt is not accepted as an input token: every invocation rechecks current
inputs. Narrative revisions can use the same applicable policy but receive new
snapshot receipts; law edits cannot reuse the original law-fingerprint context.
The experimental structural copy is evaluated through bare SDK operations, not
presented as admitted by the retained-model acknowledgement policy.

`--model hurt` now uses this checked operation for all six completed scenarios.
Native checks establish byte-identical kernel requests and responses between bare
SDK and admitted evaluation for all six. The legacy tests separately establish
`SFE022` for the three retained missing-acknowledgement scenarios; this is a specific
acknowledgement-presence comparison, not general frontend acceptance parity.
**Bare `compileAnalysis` retains its previous contract** and does not enforce this
consumer policy. The Tranche 04 description of that SDK boundary still applies.

### Commands and review set

From the checkout:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
cabal v2-test yuho-test --offline -j1 --with-compiler=ghc-9.8.4 --test-show-details=direct
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
python3 test/authoring_consumer.py "$consumer_bin"
python3 test/hurt_consumer.py "$consumer_bin"
python3 test/editing_consumer.py "$consumer_bin"
make protocols docs
cd /tmp
"$consumer_bin" --edit-demo --artifacts /Users/gabrielongtemasek/Downloads/yuho-review/tranche05
```

The Python editing checker also runs outside the checkout, validates existing
authored/kernel/projection/helper schemas and all six JSON/XML/SVG exports, and
checks the session, rejection examples and snapshot/selection distinctions. Add
`--existing-artifacts /Users/gabrielongtemasek/Downloads/yuho-review/tranche05`
to validate the saved review set too. Generate PNGs using the previously documented
`rsvg-convert` loop. `INDEX.md` describes the six named views; `data/` retains every
stage document, valid evaluation, complete projection, inclusion/omission binding,
compatible comparison, diagnostic, acknowledgement input/receipt and inspection.
`editing-session.json` is the compact stage trace. Existing focus limits apply.

The exercise resolved repeated ID-addressed updates and explicit binding replacement.
The later [validated anchor constructors](#validated-original-source-anchors--tranche-06)
replace representative manual source anchors. Export orchestration stays local to
the consumer, as shown in the current [recipe](#export-recipe). There is no new
legal-model ontology, general policy subsystem or graph-editing framework.

## Validated original-source anchors — Tranche 06

`Yuho.Authoring` re-exports `Yuho.Authoring.Source`:

```haskell
sourceAnchorBytes :: SourceRecord -> Integer -> Integer
                  -> Either [AuthoringDiagnostic] SourceRef
sourceAnchorCodePoints :: SourceRecord -> Integer -> Integer
                       -> Either [AuthoringDiagnostic] SourceRef
```

Both use zero-based, half-open ranges in the exact supplied retained text. The
first accepts UTF-8 byte offsets; the second accepts Unicode code-point offsets,
not UTF-16 code units, grapheme clusters or display columns. For example:

```haskell
let source = SourceRecord "source:note" "synthetic" Nothing (Just "é猫\nx")
sourceAnchorCodePoints source 1 2
-- Right (SourceRef "source:note" (Just (TextSpan 2 5 1 3 1 6)))
-- sourceAnchorBytes source 2 5 produces the identical reference.
```

The result is the existing serialized `SourceRef`/`TextSpan`, without a format
change. Lines and columns are one-based; columns count UTF-8 bytes. LF increments
the line and resets the column; CR counts as one byte. Empty ranges, empty retained
text and EOF positions are accepted when otherwise valid. Unicode, whitespace,
combining sequences and line endings are neither normalized nor searched.

External offsets use unbounded `Integer`. Bounds and ordering are checked before
conversion to `Int`; invalid ranges are never clamped, reordered or moved to a
nearby selection. `AANCHORRANGE` identifies the supplied source and input unit
location. `AANCHORBOUNDARY` rejects a byte endpoint within a multibyte code point.
`AANCHORTEXT` rejects a source without retained text, including locator-only
sources. Constructor errors propagate as ordinary source-linked SDK diagnostics.

The code-point path converts exact retained-text prefixes to bytes, then calls
the byte path. Both reuse the current `Compile.byteSpan` coordinate calculation
and `Core.Source.validateSpan` through the existing original-source span adapter.
The exported `byteSpan :: Text -> Int -> Int -> TextSpan` remains unchanged and
**does not validate** its inputs; it is not the recommended original-source constructor.
Original anchors remain separate from generated kernel-source spans.

These constructors require no document, legal model, analysis or projection.
They establish coordinate validity only for the provided source. Document validation
still checks source existence, identities, metadata and graph/binding completeness.
An anchored excerpt is obtained with the existing `recoverOriginalSource` on an
authored/evaluated projection, without URL fetching.

The independent cheating and hurt consumers now construct their original anchors
through `sourceAnchorCodePoints` and handle the `Either` before building their
documents. Their fixture builders accept that reference explicitly; no partial
pattern, unchecked fallback or fabricated anchor conceals a failure. Native checks
compare the resulting stored references with the previous literal values:
cheating `[6,15)` / `TextSpan 6 15 1 7 1 16`, and hurt `[11,60)` /
`TextSpan 11 60 1 12 1 61`. Existing kernel conformance stays unchanged.

### Source replacement is not anchor tracking

The source demo retains `é猫\nx` and an anchor selecting `猫`. Replacing it with
`é犬\nx` leaves that same reference structurally valid and selects `犬`. The older
projection still recovers `猫` from its own snapshot. Attaching its evaluation to
the changed document returns `PSTALE`. Explicit reevaluation preserves supplied
classifications and computed results; comparison flags the changed source material.

Inserting `!` before the original text does not relocate the reference: its old
offsets now split a code point and document validation reports `ASPAN`. A new,
explicit code-point selection can construct a new valid reference. Other source
changes can leave old coordinates valid while selecting unintended text. There is
no quotation-identity, stale-anchor or meaning guarantee, content-addressed anchor,
automatic reanchoring or text search in this tranche.

### Executed setup and compact review artifacts

The [quickstart](authoring-quickstart.md) uses the existing hurt graph as explicitly
supplied authored JSON. Its standalone package imports only `Yuho.Authoring` from
Yuho and is built in an external project with an explicit local package path,
GHC 9.8.4, copied unchanged freeze and the available cache. It attaches a checked
anchor, supplies/selects an assessment, validates/evaluates, inspects/exports,
edits and reevaluates narrative, and actually saves/reloads the authored revision.

```sh
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
python3 test/authoring_quickstart.py "$consumer_bin" --review-dir /Users/gabrielongtemasek/Downloads/yuho-review/tranche06
```

The checker records the exact external build/run commands and logs. It also
generates the anchor demo (`--anchors-demo`), verifies its literal numeric examples,
schemas and source-revision records, and retains representative regenerated views
from both existing consumers. `INDEX.md` identifies the external project, explicit
input, lifecycle outputs and `anchors/` examples. Existing cheating, hurt and
editing checks still apply; no new view family or renderer changes are introduced.
