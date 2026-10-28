# Scoped typed requirement definitions (experimental)

Scoped requirement templates reuse **one authored computation body**. A use has
explicit entity arguments and an explicit scenario-selection policy. The selected
component evaluates it through the existing typed finite evaluator. Sharing a body
never selects another component's facts or reuses its computed result.

```yuho
typed-rules-module example.permission version 1.0.0 {
  export requirement-template q:permitted;
  entity-type person;
  entity-type event;
  predicate allowed(person,event) kind relationship;
  requirement-template q:permitted(var:actor as person,var:incident as event)
    = allowed(var:actor,var:incident);
}
```

Place this module at `modules/example.permission@1.0.0.yh`. In a model:

```yuho
typed-rules-model Authorisation {
  module-root "modules";
  import example.permission version 1.0.0 as authority;
  entity-type person;
  entity-type event;
  entity actor:ada as person;
  entity event:access as event;
  predicate allowed(person,event) kind relationship;
  requirement-use q:access from authority::q:permitted(actor:ada,event:access)
    assessments scenario;
  proposition p:access;
  rule r:access establishes proposition p:access when q:access;
  limitation "Fictional technical illustration; no legal or evidential conclusion";
}
```

A scenario explicitly classifies `allowed(actor:ada,event:access)` as `proved`,
`not_proved`, or `unresolved` with a reason. Missing inputs reject. Templates cannot
be classified as original facts. The body's predicate signatures and nominal
names must agree with the defining source; there is no inferred nominal mapping.

`requirement-template` may also appear locally in a model; local uses omit the
module alias. Imported templates must be exported with the exact declaration kind
and exact module version. Different imported modules may export the same label;
qualified targets retain their different original identities. Nested imports retain
their existing refusal.

## Selection and scope

`assessments scenario` is mandatory. It explicitly selects the current component's
scenario classifications. Two uses of the same exact tuple within that selected
scenario may share its one authored classification, while retaining distinct use
and actual evaluation occurrences. Two classifications for the same primitive
tuple in one scenario reject, even if values agree.

Independent selections use independently selected component/scenario evaluations,
including selected allegations of a typed case. They can share a single model and
module while selecting different facts and results. Actor, context, case,
allegation, project entity mappings, component and use remain qualified identities.
Changing actor A's selection cannot supply actor B's independent occurrence.
A shared case classification retains its original case declaration authority.

This new opt-in source/SDK workflow does not remove `AREUSE` from frozen linked
SDK v0.2. It does not add per-use conflicting fact overrides within one scenario.
Ordinary ground `q:` references and existing separate SDK analyses still work.

## Bounded body and static checks

A template has 1–4 named `var:` nominal formals. Its body uses existing predicates,
all/any/not, finite quantifiers and cardinalities. Ground entity captures, scalar
captures, ground requirement references and nested/recursive template calls are
refused. Compose explicit uses through ordinary named requirements instead. Bound
variables cannot shadow formals or other active variables. Substitution replaces
checked formals with entity constants, preventing capture.

There are at most 64 selected/local templates and 128 explicit use-sites per
model, in addition to existing source, nominal, expression, quantifier, protocol
and dependency-plan limits. Expanded requests undergo the existing independent
protocol validation and complete-input checks before plan execution. Unknown or
private targets, wrong kinds/versions, arity/type errors, duplicate use IDs,
recursive ordinary requirement expansions and excessive cost reject.

## Retained local-template example

[workplace-safety.yh](../examples/typed-finite-templates/workplace-safety.yh) is a
self-contained model of a wholly fictional statute. One local template states the
s 12(1) equipment element for an employer/worker pair and is used once per worker.
A second local template contains a finite `forall` over tasks for the s 14
training element. An ordinary scalar comparison defeats s 12(1) through a
prioritised s 12(3) exception. Its
[scenario](../examples/typed-finite-templates/workplace-safety-scenario.yh)
classifies every expanded ground tuple. From the checkout:

```sh
cabal v2-build exe:yuho --offline -j1 --with-compiler=ghc-9.8.4
yuho=$(cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4)
model=examples/typed-finite-templates/workplace-safety.yh
scenario=examples/typed-finite-templates/workplace-safety-scenario.yh
out=$(mktemp -d /tmp/yuho-templates.XXXXXX)
"$yuho" check "$model" --scenario "$scenario"
"$yuho" run "$model" --scenario "$scenario"
"$yuho" compile "$model" --scenario "$scenario" --output "$out/request.json"
"$yuho" explain "$model" --scenario "$scenario"
"$yuho" diagram "$model" --scenario "$scenario" --view rule --format svg --output "$out/rule.svg"
"$yuho" inspect "$model" --stage parsed
python3 test/requirement_template_example.py "$yuho"
```

Expansion happens before kernel encoding. Each `requirement-use` becomes an
ordinary named requirement whose body has the actual entities substituted, and
no template construct reaches the compiled request. `check` also requires the
scenario, because typed models validate complete ground inputs. Parsed inspection
reports both templates and all four uses. `--stage checked` refuses with
`SFI002`. For ordinary typed models, `--view rule`, `modules` and `trace` currently
emit the same graph content, and only the JSON/XML `view` label differs. The
regression check also confirms that capture, recursion, free variables, arity,
role order, unknown targets, duplicate uses and missing classifications refuse with
their existing codes.

## CLI, SDK and machine

Standalone `yuho check/run MODEL --scenario SCENARIO` uses ordinary typed semantics.
For complete occurrence provenance, select the model/scenario as a `native-typed`
component in a checked-project and use:

```text
yuho compose check project.yh
yuho compose run project.yh --output NEW_DIRECTORY
yuho compose check NEW_DIRECTORY/artifact.json
yuho compose replay NEW_DIRECTORY/artifact.json --output ANOTHER_NEW_DIRECTORY
```

Check is non-evaluating at the plan level. Run evaluates exact retained sources;
replay evaluates only the immutable embedded sources. Existing atomic no-overwrite
publication and eight-file exports apply. `check --against ARTIFACT` rejects live
source revisions, including equal-status changes. Saved static checking does not
claim replay execution.

The public `Yuho.Authoring` facade adds `ScopedBody`, `requirementTemplate`,
`requirementUse` and `inspectScopedDefinitions`. Builders produce readable `.yh`
declarations and refuse identifier interpolation; `Yuho.Authoring.Dependency`
constructs/checks/runs/publishes documents with retained source bundles. Detailed
new evidence types are explicitly available from
`Yuho.Authoring.ScopedDefinitions`, avoiding new generic record-selector names in
the old facade. No private compiler imports are required.

Existing machine v0.2 `dependency-yh` check/run and `dependency-artifact-json`
check/replay expose this workflow. No new request version or input-kind inference
is introduced. Wrong kinds remain errors with no successful exports. Existing
machine v0.1 and computed-input v0.1 are unchanged.

## Provenance and view

Opt-in reports carry `scoped_definitions` in the explicitly versioned
`yuho.scoped-definitions/v0.1-experimental` envelope. Historical reports without
new uses have no extra field. One definition record retains owner, exact version,
declaration/source, UTF-8 source digest, nominal formals and structured original
body. Each use retains actual role bindings and source declaration coordinates.

Each scoped use records component, full scope, exact execution snapshot and
scenario authority. Its evaluation occurrences refer to actual eager read rows,
including root/path/bindings, primitive tuples, classifications and their original
source declarations/snapshots. Selection IDs are structural qualified tuples;
source digests pin exact bytes and are not used as a substitute for scope identity.
Referenced uses remain distinct from direct root evaluation. Skipped components
have no invented observations.

The focused dependency view has a shared authored-definition card, explicit-use
cards and actual occurrence cards. Real selected-use ports connect to existing
conversion/slot/candidate records. Other AST/read detail remains in the complete
projection and source map. JSON/XML preserve the same semantic endpoints; SVG uses
injective DOM identities. These views do not claim broader full typed projection
coverage. Native checked compiler inspection remains narrower: parsed declarations
retain new structures, while unsupported checked inspection stages refuse honestly.

No new Core truth table, proposition resolution, legal-proof policy, judicial
finding or sentence-selection meaning is introduced. Candidate consequences remain
explicit authored technical candidates.
