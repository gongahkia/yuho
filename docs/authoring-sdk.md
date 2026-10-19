# Experimental graph-authoring SDK — Tranche 01

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
Editors, rendering changes, shared-graph execution, additional backends,
evidence weighing, penalty authoring, sensitivity and broader model comparison
remain outside this tranche.
