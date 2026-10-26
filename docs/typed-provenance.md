# Complete typed provenance (experimental v0.1)

This opt-in projection connects checked source authority to actual typed execution
records. It adds no evaluator, arithmetic operator, legal inference or sentencing
selection. Its domain is the existing checked-dependency plan: native typed models
(including selected typed-case allegations), in-memory technical templates, and
selected SDK typed v0.3 analyses. Scoped definitions and exact quantitative
computations in those components retain their existing meanings.

An ordinary typed model uses the same readable checked-project wrapper as
[checked dependencies](checked-dependencies.md); it may have one component and no
bindings or candidates. Source models and scenarios remain independent files.
Existing proof, exception, presumption and temporal SDK projections remain
separate supported contracts. This projection does not claim their evaluation
records have been translated into the new graph.

## Public workflow

```sh
yuho provenance inspect project.yh
yuho provenance trace project.yh
yuho provenance run project.yh --output new-provenance-directory
yuho provenance inspect-artifact new-provenance-directory/artifact.json
yuho provenance trace-artifact new-provenance-directory/artifact.json
yuho provenance replay new-provenance-directory/artifact.json --output new-replay-directory
yuho provenance explain new-provenance-directory/artifact.json --focus 'EXACT_NODE_ID'
yuho provenance replay new-provenance-directory/artifact.json --focus 'EXACT_NODE_ID' --output new-focused-directory
```

Select `EXACT_NODE_ID` from the complete projection's `nodes[].identity`. IDs are
opaque; do not parse labels or split IDs on punctuation. `inspect` checks sources
and returns `mode: checked_not_evaluated`. It never evaluates an expression.
`inspect-artifact` decodes and statically checks the saved embedded document; it
does not recompute the saved execution digest. `trace`, `run`, `explain` and
`replay` execute the accepted evaluator or replay the retained artifact and verify
its execution authority. Structured trace/explanation does not require rendering.

Publication creates six files atomically in a new directory:

| File | Meaning |
| --- | --- |
| `artifact.json` | Existing immutable dependency artifact, including quantitative/scoped authority when present |
| `provenance.json` | Complete supported typed projection, all nodes/edges and retained old complete projection/report/source map |
| `focus.json` | Exact included/omitted partitions and semantic-to-SVG ID bindings |
| `view.json` | Native semantic graph of the chosen subset |
| `view.xml` | The same graph and observation states |
| `view.svg` | The same graph rendered by the existing native renderer |

The old `compose run/replay` eight-file export is unchanged. The new export does
not replace its `report.json`, `projection.json`, `view-bindings.json` or
`source-map.json` contracts: the old complete projection (including its report and
source map) remains under `provenance.json.retained`.

## Typed evidence and identity

Every node has an explicit category, structural identity components, evaluation
state, optional technical state, authority, and original record. Structural IDs
use the accepted length-prefixed injective encoding; display labels never join
objects. Component snapshot, source digest, root/path/bindings and ordered ground
arguments qualify execution records. Filter-read identity also includes the
authored aggregate member ID: two members using one filter have two evaluations.

The projection preserves:

* Exact retained source documents and UTF-8 declaration spans; imported owner and
  host use-site are separate records. Byte columns remain one-based.
* Checked declarations, original SDK objects and component-local original SDK
  sources. SDK source references are independently validated against retained
  source bytes. Locator-only records have no invented quotation or file span.
* Original shared definitions, uses and actual occurrence records; independent
  selected native and SDK classifications, reasons and scope.
* Every actual eager `FiniteRead`, typed ground tuple/scalar/reference input, and
  expression/rule/proposition backend observation, including unselected ports.
* Exact quantitative inputs, member decisions, operand order, intermediate values
  and root values. Quantitative integers remain decimal strings.
* Original bindings, authorisation references, actual observation ports,
  conversions, generated slot facts and candidate availability.

Edges have closed category signatures. Source links, checked lowering, selected
input, actual operand read, reference expansion, rule resolution, conversion and
candidate guards remain distinct relationships. The complete retained report
supplies full priority, rule, input and source metadata beyond graph labels.

The graph retains actual eager reads in `all(F,U)=F`. Those reads do not claim
that every operand is decisive for the final value. Coordination edges describing
component execution are not substitutes for read-level causal edges. Conflict
origins come from accepted conversion records, never equal names/statuses.
Unavailable ports have no fabricated observation or unresolved value. The public
finite evaluator is eager; component-unavailability is currently an internal
engine control tested separately, not a new authorable skip construct.

Unselected SDK assessments may appear as **authored** objects. Only selected
assessments have execution-selection edges. In-memory templates retain structured
authority with no fabricated physical source span. Original legal sources and
hypothetical assessments are not independently authenticated by this projection.

## Complete and focused contracts

`projectTypedProvenance` includes all promised records for the admitted domain.
Unknown evidence categories, invalid source spans, conflicting identities,
dangling/incompatible edges and oversized outputs refuse. Full structured limits
are 65,536 nodes, 262,144 edges and 32 MiB encoded projection. There is no silent
truncation. Construction remains subject to the accepted evaluator's input and
execution limits.

A focused view contains the selected node's ancestors plus its descendants,
computed separately. It does not descend from each ancestor into unrelated
siblings. Its included/omitted node and edge lists partition the complete domain;
visible edges have both endpoints included. Every SVG binding is generated by the
same injective ID encoder used by the renderer. A focus is a viewing subset, not a
minimal causal proof. Full records remain in `provenance.json`. Revising a source changes the whole
execution/projection authority. Independent scopes retain their own selected
input and calculation records; snapshot-qualified graph IDs are not promised to
remain stable across different whole-plan executions.

Rendering refuses above 512 nodes or 2,048 edges. Choose a narrower target or use
structured `trace`/`explain`; an oversized graph is never labelled complete after
truncation. The complete six-file publication is limited to 32 MiB; saved artifacts
must fit the existing 8 MiB decoder bound. Existing output directories are never
overwritten. Graph labels, states, source citations and scopes are textual as well
as coloured. Detailed reasons and exact records remain machine-inspectable.

## SDK and validation

Use the public `Yuho.Authoring.Provenance` with `Yuho.Authoring.Dependency`:

```haskell
checked    <- checkDependencyPlan authoredDocument
execution  <- executeDependencyPlan checked
projection <- projectTypedProvenance execution
focus      <- focusProvenance projection (Just actualNodeId)
explanation <- explainProvenance projection actualNodeId
files      <- exportTypedProvenance projection (Just actualNodeId)
```

These operations return `Either DependencyDiagnostic`. Checked projections and
focus constructors are opaque. Public accessors are ordinary functions, not record
field labels; external record-update syntax cannot bypass checked construction. `validateTypedProvenance execution submittedJSON`
regenerates from the opaque authoritative execution and requires exact equality,
including records and edges; mere endpoint existence is insufficient.
`validateProvenanceFocus` checks the exact root, projection, partitions and DOM
bindings. Source recovery remains available through
`dependencyComponentSources`/`recoverDependencyReference`, with an explicit
component namespace. See `test/ProvenanceClient.hs` for a public consumer.

The new formats are `yuho.typed-provenance/v0.1-experimental`,
`yuho.typed-provenance-focus/v0.1-experimental` and
`yuho.typed-explanation/v0.1-experimental`. JSON schemas describe structure;
semantic source/edge/partition validation requires the SDK validators.

## Machine interface

Request/response `v0.3-experimental` is opt-in and accepts only
`dependency-yh` or `dependency-artifact-json`. Operations are `inspect`, `trace`,
`explain` (requires `focus`) and `provenance` (requires new `output`, optional
`focus`). For example:

```json
{"format":"yuho.machine-request/v0.3-experimental","input_kind":"dependency-yh","operation":"provenance","path":"project.yh","output":"new-output"}
```

Both request-file and stdin transports share the checked implementation. Current
source and embedded artifact kinds are enforced separately. Failure emits one
structured response, `success: false`, no successful exports and
`source_authority: not_validated`; requested authority is explicitly separate.
Existing machine v0.1/v0.2 requests, original artifacts, kernel outputs and old
native graph encodings retain their meanings.

## Assurance and boundaries

Nine abstract Lean properties establish partition/subset, endpoint, distinct
scope/occurrence and authored-versus-observation properties under stated identity
assumptions. Independent finite focus vectors compare production traversal and
partition results with an external oracle and Lean. They do not prove parser,
source resolver, compiler, serializer or renderer refinement. Permanent tests
check actual source bytes, ground tuples, read ledgers, scoped isolation, filter
occurrences, conflicts, unavailable work, tampering, omission partitions and
JSON/XML/SVG correspondence. Geometry tests are separate from semantic tests.

No new legal inference, proof sufficiency, court disposition or sentence is
computed. Candidate availability remains a technical state of an authored
candidate. Cross-profile universal provenance and a graphical editor are outside
this version.
