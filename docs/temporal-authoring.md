# Experimental temporal expression selection

Read the [quickstart](authoring-quickstart.md) first, then the
[SDK API map](authoring-sdk.md#current-api-map). This opt-in profile uses the same
public `Yuho.Authoring` facade. It selects among authored expressions; it does
not determine which law applies to an incident.

## Format and admitted composition

`yuho.authoring/v0.5-experimental` is a `TemporalDocument`: an identified legal
work, two to 64 `TemporalExpression` records, wrapper original sources, scope
limitations and caller-reviewed assumptions. Each expression embeds a complete
v0.1 `AuthoringDocument`, its selected analysis ID, explicit version label,
effective interval, expression-source and effective-date-evidence references,
and optional `temporalSupersedes` metadata. Embedded document/source namespaces
are independent: the same primitive ID can appear in different versions.
There is no file lookup or `.yh` generation in this SDK path. Assumption text
is retained context, not an acknowledgement gate or evidence that legal review
has actually occurred.

The [authoring schema](../schema/authoring-v0.5-experimental.schema.json) describes
closed records, including nested sources, assessments and embedded documents.
Unknown fields and duplicate JSON keys fail the public decoder. Semantic
validation is also required; a schema alone cannot establish valid intervals,
source anchors, executable structure or complete selected bindings.
Only v0.1 proof trees are admitted. Linked definitions, typed expressions,
registered presumptions and nested temporal wrappers are not mixed into v0.5.
Older profile decoders, snapshots and execution semantics are unchanged.

## Selection and validation

Intervals are `[temporalEffectiveFrom, temporalEffectiveTo)`: inclusive start,
exclusive end; `Nothing` means open end. JSON dates require the complete four-digit `YYYY-MM-DD` spelling and use the
existing Haskell temporal calendar parser (`%F`), not string comparison. Legacy
file tokens still retain their established lexical behaviour; the SDK does
not accept surrounding whitespace or expanded-year strings as JSON dates. Expressions are sorted by start,
as in the legacy loader; declaration order is retained in authorship. Adjacent
intervals must meet exactly. Reversed/empty intervals, gaps, overlaps, duplicate
IDs, an open interval before a later expression, malformed dates and unknown
analyses are refusals. No expression is invented before or after authored
coverage. `Nothing` conduct date fails explicitly; a date with no match fails.
`supersedes` is descriptive and need not identify another local expression;
it neither overrides interval membership nor establishes legal lineage.

`validateTemporalDocument` checks all embedded documents structurally, all
wrapper identities/references/anchors and intervals. Missing assessments may
remain in an embedded draft; `selectTemporalExpression` and authored projection
do not invent computed statuses. `compileTemporalAnalysis` requires executable
completeness of the selected analysis and delegates kernel limits/checks to
`compileAnalysis`. Non-selected analyses are never compiled or evaluated
implicitly. All candidates' reference/identity/structure errors still fail.
Wrapper size is limited to one MiB and 64 expressions; embedded documents keep
their existing authored, occurrence, depth and kernel limits. Views refuse more
than 64 cards or 128 connections rather than truncating.

```haskell
import Yuho.Authoring

-- temporal :: TemporalDocument, constructed with public records or decoded
-- from explicitly supplied bytes. A conduct date is always an explicit input.
run temporal = do
  selection <- selectTemporalExpression temporal (Just "2024-01-01")
  compiled <- compileTemporalAnalysis temporal (Just "2024-01-01")
  evaluated <- evaluateTemporalAnalysis compiled
  projection <- projectTemporalEvaluation evaluated
  view <- temporalReferenceView projection TemporalSetView
  svg <- encodeTemporalViewSvg projection view
  pure (selection, temporalEvaluationSelection evaluated,
        evaluationReport (temporalEvaluationProof evaluated), svg)
```

`encodeTemporalDocument` / `decodeTemporalDocument` provide deterministic
save/reload. `recoverTemporalSource document ref` recovers an exact anchored
excerpt from wrapper originals; use `recoverOriginalSource` on
`temporalSelectedProjection` for embedded law sources. Locator-only references
remain locators. No URLs are fetched. Anchors describe retained extracts,
including explicitly labelled whitespace-normalised extracts, not offsets in
an independently downloaded legislative file.

## Conduct date, reference date and provenance

`analysisReferenceDate` remains the selected proof analysis's kernel-policy
date. It is retained and may differ from conduct date. It neither participates
in interval matching nor is overwritten by selection. Publication, revision,
commencement, retrieval and reviewer acceptance dates are different concepts.
A source locator or scope note can retain those details; the SDK does not infer
effective boundaries from them. Existing model-bundle date records are
provenance/validation data and are not used as an executable selector.

`TemporalSelection` retains wrapper/work, supplied date, selected complete
expression and interval, underlying analysis, exact `TemporalSnapshot`,
underlying proof snapshot ID and (after compilation) SHA-256 of compiled request
bytes. The temporal snapshot hashes the entire wrapper, conduct date, selected
expression and evaluator profile. It retains non-selected versions too.
The underlying `ApplicationReport`, occurrences and generated compiler/source
mappings retain their independent proof snapshot. Generated spans are never
original statute anchors. Multiple versions may have similar labels and IDs;
use expression ID plus embedded document identity, never a bare label, to
identify the original version. Embedded projection object IDs are scoped by
their projection/document; matching ID strings alone do not justify merging
objects across versions.

Two dates in the same interval produce separate temporal snapshots, potentially
the same underlying proof snapshot/request. Crossing a boundary selects another
embedded document. Revising an interval, source, assessment or law creates a
new retained snapshot. `projectTemporalEvaluationOn document date result`
rejects any mismatch with its retained wrapper or date. Source expansion/focus
only creates derived views. It does not edit or reevaluate anything.

Do not use `compareAnalyses` to bypass its existing law-compatibility check.
Historical-version executions remain separate structured results. A structural
or computed difference is not a legal causal/counterfactual claim.

## Complete projection and bounded exports

`encodeTemporalProjection` emits
`yuho.temporal-projection/v0.5-experimental` (see the
[projection schema](../schema/temporal-projection-v0.5-experimental.schema.json)).
It retains the selection snapshot with **every** embedded authored alternative,
plus `temporalProjectionProof`, the selected proof's unchanged complete
projection, and a combined node/edge set linking date → interval/expression →
selected result → actual proof occurrence. Date cards and result-summary cards
are explicitly projection-generated; the summary links to the actual selected
report and occurrence, not an extra fabricated kernel trace. Non-selected versions receive no
run observations. Original sources, date-evidence edges and repeated source
references remain independently addressable.

`temporalReferenceView p TemporalSetView` shows the conduct date, all intervals,
selection and result. `TemporalProvenanceView` shows selected expression and
wrapper sources (source expansion is explicit). Views retain exact inclusion
and omission partitions of the combined projection, with stable collision-safe
rendered IDs. `encodeTemporalViewJson`, `encodeTemporalViewXml` and
`encodeTemporalViewSvg` export simplified derived views; save `encodeRecord view`
as the binding companion. The complete projection is the full contract.

For the selected law, use `temporalSelectedProjection p` with the existing
`lawOccurrenceView`, `encodeProjectionSvg`, `encodeProjectionLegacyJson` and
`encodeProjectionLegacyXml`. Save that proof projection and its own bindings:
they intentionally identify the underlying proof projection, not the temporal
companion. The consumer demonstrates distinct filenames for evaluations,
complete projections, diagram JSON and view bindings. Exports are not lossless
authoring interchange. Boundary views are separate executions immediately
before/on the transition; no cross-version observation alignment is implied.

## Executable examples and independent reference

From the checkout, with its unchanged dependency freeze:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
cabal list-bin exe:yuho-temporal-consumer --offline --with-compiler=ghc-9.8.4
```

Run the absolute binary returned above from any directory with an explicit
output directory. [Main.hs](../examples/temporal-consumer/Main.hs) and
[TemporalExamples.hs](../examples/temporal-consumer/TemporalExamples.hs) use only
the public facade. A separate Cabal package can use `packages: . /absolute/yuho`
with `with-compiler: ghc-9.8.4`, the repository's pinned index-state and a copy of
its dependency freeze; no Hackage publication is implied.

```sh
python3 test/temporal_authoring_consumer.py /absolute/path/to/yuho-temporal-consumer
cabal v2-test yuho-test --offline -j1 --with-compiler=ghc-9.8.4 --test-show-details=direct
```

The fictional example switches `A AND B` to `A OR B` at 2024-01-01 with
A proved, B not proved. Before: not satisfied; on/after: satisfied.
`test/fixtures/temporal-sdk` contains independently authored `.yh` expressions
and scenarios. The native comparison additionally represents A AND an always-proved context input
(an identity subgroup matching the legacy conduct/circumstance/fault shape)
and the synthetic
exception required by that grammar; it compares matched requirement
statuses, evaluation/skipping, main/guard branch reasons and final results,
normalising only generated IDs, request digests and source spans. Existing
legacy explanation and penalty snapshots remain unchanged.

The second example represents bounded old/new Penal Code s 24 expressions.
The fixed old source is the 2008 RE published 30 November 2008; the substituted
text is Act 15/2019 s 7, published 4 June 2019. Its 1 January 2020 transition is
supported by [S 849/2019 paragraph 2](https://sso.agc.gov.sg/SL-Supp/S849-2019/Published/20191227?DocDate=20191227)
(the exclusions do not include s 7). The deliberately limited old coverage
starts 2019-01-01 by author choice, **not** as an assertion of old commencement.
The new alternative combines ordinary standards **and** knowledge. Intention
to cause wrongful gain/loss is distinct from completed gain/loss. Primitive
wrongfulness/intention classifications remain synthetic externally supplied
assumptions; this is no complete offence model. Act 15/2019 s 191 concerns other
sections/event histories; its existence does not resolve all savings issues.

Official-source browser extracts and the audit support the bounded text change
and notification date; no digitally authenticated original or exhaustive
incident-specific legal review is claimed. Continuing conduct, retroactivity,
savings, intervening law, applicability and legal currency remain external.
Open-ended authored coverage is no assurance that an expression remains law.
