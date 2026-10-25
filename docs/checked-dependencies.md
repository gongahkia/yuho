# Checked dependency plans (experimental v0.1)

A checked project connects actual typed observations to declared technical
conditions or authored candidate guards. It coordinates existing evaluators;
it does not decide legal proof, guilt or a sentence. The existing
`computed-project` and computed-input v0.1 contracts remain separate.

```
yuho compose check project.yh
yuho compose run project.yh --output new-directory
yuho compose check project.yh --against saved/artifact.json
yuho compose check saved/artifact.json
yuho compose replay saved/artifact.json --output another-new-directory
```

`check` parses, resolves, checks all primitive inputs, scopes, policies, terms,
limits and the complete dependency DAG without evaluating components. `run`
loads each exact source once. Replay checks and re-executes only the embedded
immutable document; it reads no live model/scenario/import files. Attachment
checking rejects any changed retained byte, including a same-status reason edit.

A project begins:

```yuho
checked-project plan:example version "yuho.dependency-plan/v0.1-experimental" {
 source origin locator "urn:fictional:example";
 scope scope:a actor person:a context event:i {
  identity person:a nominal role:person;
  identity event:i nominal role:event;
 }
 component supplier profile native-typed model "supplier.yh" scenario "facts.yh" scope scope:a {
  nominal person as role:person;
  nominal event as role:event;
  entity local:person as person:a;
  entity local:event as event:i;
 } rationale "Explicit fictional entity correspondence";
 // Additional components, bindings and candidates follow here.
}
```

Each component explicitly maps actual local entities/types to project identities.
A native standalone model receives a plan-owned scope manifest. A native case
requires `entry allegation ID` and an exactly matching actual case/allegation
scope. An SDK producer uses `profile sdk-typed-v0.3 model "source.json" entry
analysis ID`; its actual selected local scope and kernel mappings are retained.
SDK contexts need not be entities: the explicit selected analysis/project scope
and rationale authorise that context correspondence. The actor still needs a
real typed entity map. These are authored modelling assertions, not certified
world identities. Cross-scope casts are unsupported.

A recipient typed model declares a hole:

```yuho
dependency-condition in:qualification type technical-condition;
requirement q:recipient = all(ownCriterion(local:person,local:event),condition(in:qualification));
```

A hole cannot be directly classified in a scenario or run unbound. Only a checked
plan supplies execution-generated facts; source files are never rewritten.
`condition` is reserved within a template declaring holes. Ordinary models keep
their existing grammar. The private `dep_template_type`, `dep_template_entity`
and per-slot generated predicate identities are protected only when lowering
actually creates condition-hole helpers. In a component without holes, those
spellings remain authored identities and undergo normal nominal/entity mapping.
This also applies to in-memory SDK templates and selected typed SDK producers.
A no-hole native model may declare and classify an ordinary typed predicate
named `condition`, such as `condition(person,event)`. Its ordinary nominal,
arity and input-completeness rules still apply; no dependency input is generated.
With holes, `condition(slot)` remains the reserved source form and may only
receive its value through a checked binding.
A binding is explicit:

```yuho
bind link:qualification from supplier . proposition p:qualified
 to recipient . condition in:qualification
 mapping "yuho.proposition-support/v1"
 rationale "Technical support, including absence of support, not factual falsity"
 refs origin;
```

Whitespace around the structural `.` is required. It is not a guessed split of
an identifier containing dots. Named expression ports use `expression q:name`
and `yuho.condition-identity/v1`. This policy preserves evaluated T/F/U. Resolved
proposition ports use `proposition p:name` and `yuho.proposition-support/v1`:
established→T; defeated/not_established→F; unresolved/conflict→U. The original
state, contributing rules, priorities and conflict ancestry remain available.
F for not_established means technical support absence. Neither policy creates
an evidential assessment. Parameter-aggregated propositions cannot be consumed
as actor-local ports in this version; existing standalone evaluation is unchanged.

An unavailable source has no truth value. It blocks required consumers and
produces a not_evaluated record, rather than an unresolved backend observation.
The initial typed adapters are eager and cannot author a skipped producer; the
internal unavailable coordination model is tested separately. Missing actual
promised rows are errors. Existing strong logic still handles U, for example
`all(F,U)=F`, while retaining actual conflict ancestry from the dependency cone.

Candidates have independent guards and retain all terms and modality:

```yuho
candidate candidate:example scope scope:a guard supplier . expression q:gateway
 mapping "yuho.condition-identity/v1" modality may
 rationale "Fictional technical candidate only" refs origin {
  life-imprisonment term:example;
 }
```

T means eligible, F ineligible, U unresolved (with conflict cause where present),
unavailable not_evaluated. All simultaneous eligible candidates survive. Term
combinators `all-of`, `exactly-one-of`, `one-or-more-of` retain their trees; no
child sentence is selected. Atoms reuse the admitted PenaltyTerms-v1 validation:
life imprisonment, death, bounded term imprisonment, SGD fine and caning, with
explicit endpoint forms. May/shall are metadata outside that frozen term format.

Limits: 16 components, 64 bindings, 32 candidates/scopes, 16,384 expanded
component/term/ledger nodes, 4 MiB retained source input, 8 MiB encoded plan/artifact input and 32 MiB complete
published exports. Existing tighter component limits still apply. Every slot
has one writer; duplicate equal-value writers also fail. All potential edges
are checked for cycles before execution. Canonical component identities break
scheduling ties. No scalar arithmetic, general template instantiation, arbitrary
profile chaining or judicial selection is added.

The eight exports are artifact/report/projection/view-bindings/view JSON/XML/SVG
and source-map. Complete structured evidence includes exact sources, checked and
execution requests, actual eager read occurrences, resolved backend rows,
conversions, generated input mappings, scopes, snapshots and candidate effects.
The focused view shows candidate term summaries and downstream model expression
values, and omits primitive/read detail explicitly listed in its bindings;
projection.json retains it. XML/SVG encode the same focused semantic graph.
The existing deterministic renderer and injective DOM escaping are reused.
Publication uses the existing Linux same-parent staging and atomic no-replace
rename lifecycle. No existing destination, file or symlink is overwritten; handled
failures clean only this operation's staging. No crash-durability guarantee is made.

The public Haskell interface is `Yuho.Authoring.Dependency`: authored records,
a checked in-memory `TechnicalTemplate` builder, existing SDK typed producer
adapter, opaque CheckedPlan/DependencyExecution, check/execute/project,
source recovery, encode/decode/save/replay and `publishDependencyPlan` using the
same atomic no-replace lifecycle as the CLI. It requires no shell or fabricated
source strings. Frozen profiles/encoders are unchanged.

Machine requests opt into `yuho.machine-request/v0.2-experimental` and
`dependency-yh` check/run or `dependency-artifact-json` check/replay. v0.1 stays
closed to these kinds. Responses use v0.2, one JSON object, exit 0/1 and successful
exports only after publication. See the new machine/plan/artifact schemas.

Executable acceptance inputs and independent oracles are in
`test/fixtures/dependency`, `test/checked_dependencies.py` and
`test/DependencyChecks.hs`. C15 retains its qualified gateway/term scope; the
C06-inspired recipient and C10 receipts/SGD100 are explicitly fictional controls.
They do not establish full statutory-domain adequacy or release clearance.

Primitive identities and execution reads use structural predicate/ordered-argument
keys. Punctuation in admitted SDK identifiers cannot substitute one fact for
another; a genuinely missing classification is refused. Legacy printable ground
strings and read `actual_inputs` remain human-readable descriptions. They must
not be parsed or joined as semantic identities. Each read now also exposes
`input_records` under `yuho.typed-read-input/v1`, distinguishing ground predicate
lookups (including the exact classification/reason), requirement references and
scalar operands. The enclosing read supplies component/snapshot/root/path/bindings.
Only actual ground lookups propagate a generated condition's causal ancestry;
eager `all(F,U)=F` still records both evaluated operands.

The new read records are additive to dependency report/projection v0.1. Frozen
kernel and SDK response schemas do not change. Their legacy-compatible execution
digest excludes only this additive, recomputed `input_records` field. Unaffected
saved dependency artifacts retain their execution identity; regenerated exports
include the new records. Previously unsafe executions with wrong values or false
causes fail replay against their old saved execution digest. Re-execution of the
exact original authored document produces the corrected result. Projection/view
validation still checks the full canonical records, including typed inputs.

Machine v0.2 dispatches to explicit current-source or saved-artifact operations,
shared with the CLI. `dependency-artifact-json` never falls through to a live
project check. Static artifact check validates source authority without evaluating
or verifying a syntactically valid execution digest; replay verifies that digest.
Successful effects report the validated authority. Failed v0.2 responses report
`source_authority: not_validated`, with `requested_source_authority` separately;
check failures report no evaluation, while run/replay failures report evaluation
as `not_reported` because evaluation may have preceded an export failure. Failed
responses never declare successful exports. Machine v0.1 behavior is unchanged.
