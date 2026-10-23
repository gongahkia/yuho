# Readable source authoring for computed composition

`yuho compose` connects one checked, grounded `.yh` typed expression to one
primitive input in a separately authored fictional proof or presumption model.
It uses the existing [computed-input SDK](computed-input-bindings.md); no Haskell is needed
to author or run the projects below. The full language is broader than this adapter.
For compilation stages of the component programs, start with the
[compiler guide](compiler-guide.md), then the [language reference](language-reference.md).

## Run a complete project outside the checkout

With the pinned GHC 9.8.4 / Cabal 3.12.1.0 setup and available dependency cache:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
YUHO=$(cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4)
PROJECTS=$(mktemp -d)
cp -R examples/source-composition/proof "$PROJECTS/proof"
cp -R examples/source-composition/presumption "$PROJECTS/presumption"
cd "$PROJECTS"
"$YUHO" compose check proof/true.project.yh
"$YUHO" compose run proof/true.project.yh --output proof-true
"$YUHO" compose run proof/false.project.yh --output proof-false
"$YUHO" compose run proof/unresolved.project.yh --output proof-unresolved
"$YUHO" compose run presumption/active.project.yh --output active
"$YUHO" compose run presumption/computed-rebuttal.project.yh --output rebuttal
"$YUHO" compose run presumption/dominance.project.yh --output dominance
"$YUHO" compose run presumption/skipped.project.yh --output skipped
"$YUHO" compose replay proof-true/artifact.json --output replay
"$YUHO" compose check proof/true.project.yh --against proof-true/artifact.json
```

Every output directory must be new; its parent must exist. Failed checks return the
existing JSON diagnostic on stderr and exit 1. Success returns JSON on stdout.
`compose --help` describes the commands. Existing `run`, `compile`, `inspect` and
`diagram` commands retain their component-program contracts; use `compose` for this
project declaration, not an automatic input-format guess.

The [proof project](../examples/source-composition/proof/true.project.yh) includes
separate model, scenario and case-text files. `actor:one` and `actor:two` are both
labelled **Alex**, with independently supplied ground tuples. The selected tuple
uses actor one; no matching by display label occurs. The fictional source quote
“Recorded condition” also labels two different proof inputs.
Legacy fixture identifiers such as `f:no-authorization` remain distinct identities;
the new fixture labels that target “Fictional technical target condition”. Its
explicit mapping is not a claim that a true permission relation proves its absence.

| Project (under the copied directory) | Typed result | Downstream result / route |
| --- | --- | --- |
| `proof/true.project.yh` | satisfied | satisfied |
| `proof/false.project.yh` | not_satisfied | not_satisfied |
| `proof/unresolved.project.yh` | unresolved | unresolved |
| `proof/integer-boundary.project.yh` | 35 > 35: not_satisfied | not_satisfied |
| `proof/integer-above.project.yh` | 36 > 35: satisfied | satisfied |
| `proof/integer-unknown.project.yh` | unresolved integer comparison | unresolved |
| `presumption/active.project.yh` | satisfied trigger | active; satisfied |
| `presumption/inactive.project.yh` | not_satisfied trigger | inactive; not_satisfied |
| `presumption/unresolved.project.yh` | unresolved trigger | unresolved; unresolved |
| `presumption/rebutted.project.yh` | satisfied trigger | rebutted; not_satisfied |
| `presumption/dominance.project.yh` | satisfied trigger | rebutted; satisfied through direct target proof |
| `presumption/skipped.project.yh` | satisfied trigger | active; unresolved ordinary requirement, exception guard not evaluated |
| `presumption/computed-rebuttal.project.yh` | satisfied rebuttal | rebutted; not_satisfied |
| `presumption/computed-rebuttal-false.project.yh` | not_satisfied rebuttal | active; satisfied |

These are fictional technical exercises, not legal permission findings. The integer
variant uses dimensionless exact integers; it adds no measurement or unit semantics.

## Declaration and static contract

The small addition is a **project entry point**; component model/scenario syntax is
unchanged. Declarations appear in this order:

```yh
computed-project workflow:true {
 source-model "relationship.yh";
 source-scenario "true.yh";
 source-analysis analysis:typed rule typed-rule expression q:relationship
   actor actor:one context event:fictional;
 destination-model "proof.yh";
 destination-scenario "direct.yh";
 destination-analysis analysis:proof rule o:entry input f:no-authorization
   actor actor:one context event:fictional;
 binding binding:true mapping "yuho.technical-status-to-proof/v1"
   unresolved not_determined
   rationale "I authorise this technical conversion, not a judicial proof finding.";
 label actor:one "Alex";
 label actor:two "Alex";
 assertion assertion:record for q:relationship source "case.txt";
}
```

The analysis IDs **declare** the SDK analysis contexts for this invocation; the
model, scenario, rule and expression names **resolve** existing source declarations.
A source actor must name a concrete entity. Actor and context must match exactly
across the binding. Scope is explicit author admission, not inferred from the
predicate's first argument, a label or case text. Predicate argument order and
entity identity remain independent of display labels.

For a `presumption-program` destination, omit `destination-scenario`: its existing
`base-scenario` owns the direct inputs. An override is rejected. Existing trigger
and rebuttal leaves are resolved through their original declarations. Binding to
one of these inputs does not change the registration's target or its conditions.

Zero or more `label` and `assertion` declarations may follow the binding. Labels
must name distinct existing typed objects. An assertion names an existing **single
primitive predicate expression** and retains the exact supplied text as a case
assertion supporting its selected assessment. It cannot silently support an entire
group or scalar calculation. Assertions do not change classifications.

References are regular, non-symlink sibling files. Model/scenario names end in
`.yh` or `.yhs`; case text may use another suffix. Absolute paths, traversal,
URLs and module imports are refused. Each source file is at most 65,536 bytes;
existing parser, typed SDK, proof SDK and bridge limits apply as well. Binding IDs
use the existing lexer identifier syntax and the public 128 UTF-8 byte ceiling;
strings and retained text may contain Unicode. This adds no formatter or comment
round-trip promise.

### Admitted translation subset

- **Typed source:** one named requirement, one unparameterised establishing rule
  whose body refers to that requirement, one proposition. Concrete nominal entities,
  relationship-kind predicates with typed positional arguments, explicitly supplied ground classifications,
  exact integer values, `compare(left,gt,right)`, `compare(left,eq,right)`, and finite
  `all(...)` / `any(...)` bodies are admitted. Every needed tuple/value must be present.
- **Proof destination:** the existing checked `Synthetic` restricted-entry form,
  including its main requirement tree and exception guard. This is intentionally
  narrower than all `.yh` proof families. Its existing fixed model metadata and
  category checks still apply; start from `proof.yh` in the example, not an arbitrary
  statutory family. One v0.1 primitive input is supplied by the binding.
- **Presumption destination:** the existing `presumption-program` around that same
  synthetic proof form, with 1–16 explicit registrations and effective trigger and
  rebuttal leaves. It lowers to v0.4 through the accepted public SDK.
- **Not admitted:** parameters, quantifiers, negation, cardinality, priorities,
  norms, modules/imports, multiple named requirements/rules/propositions, nested named
  references, noninteger values, other comparison operators, statutory proof-family
  adapters, penalties, linked definitions or temporal/mixed-profile destinations.
  The adapter rejects these constructs; it never erases them to fit the SDK.

All destination classifications except the one bound input remain mandatory,
including rebuttal classifications and skipped guard inputs. A directly selected
assessment for the bound input conflicts **even if its status agrees**. Missing
information is not converted to unresolved. A supplied unresolved typed reason is
retained separately from the declared destination reason (`not_determined` or
`external_decision_pending`).

## Authority, lowering and immutable replay

`compose check` parses and statically checks current sources, builds SDK documents,
compiles the typed analysis without evaluation, and validates the bridge plan.
It returns `yuho.source-composition-check/v0.1-experimental` with `evaluated: false`.
A checked plan is not a computed observation.

`compose run` authorises **fresh evaluation of the exact current checked sources**.
It evaluates the typed SDK analysis, calls public `makeComputedInputBinding` on the
actual selected expression observation, checks it against the pinned plan, then
calls `executeComputedInputWith`. Destination execution uses the existing proof or
registered-presumption backend. The adapter computes no truth table or derivation.

The explicit policy maps satisfied → `Proved`, not_satisfied → `NotProved`, and
unresolved → `Unresolved(declared reason)` as **technical input conversion**. The
report retains the original typed observation and reason, rationale, scopes, source
snapshot, destination snapshot and generated execution overlay. Technical false is
not factual absence; neither conversion nor rebuttal state establishes legal proof
or evidential sufficiency. A rebutted route withdraws support, and independent direct
proof can still satisfy the target. Global derivations remain evaluated even when a
downstream exception guard is skipped.

`artifact.json` is the existing `yuho.computed-input/v0.1-experimental` artifact,
not a new unified language format. It embeds the complete translated component
documents, exact source texts, binding and selected snapshot identities. Replay
reevaluates those immutable embedded inputs; it does **not** follow live `.yh` paths
or pretend to load a saved backend result. `check --against` demands equality with
the fresh source plan and returns `SFCSTALE` if it differs. Even a same-status comment
or case-text revision changes the retained source snapshot. Original evaluations
remain independently inspectable. Copying an unchanged project directory preserves
identities because source locators are sibling basenames rather than absolute paths.

No original destination file receives a generated assessment. The report explicitly
identifies the bridge-generated assessment and execution-only overlay. The new
project format does not create a general `.yh` ↔ SDK round-trip guarantee: arbitrary
SDK annotations, presentations and alternatives cannot be authored through it.

## Source mappings and diagrams

Each run writes distinct files:

| File | Role |
| --- | --- |
| `artifact.json` | Saved inputs and explicit binding; authority for replay |
| `report.json` | Both evaluations, named observation, conversion, snapshots, overlay and presumption derivations |
| `source-map.json` | Versioned source hashes and original declaration anchors |
| `projection.json` | Complete existing combined projection, native component projections and validated navigation |
| `view-bindings.json` | Included/omitted projected objects and connections |
| `view.json`, `view.xml`, `view.svg` | Existing compact reference diagram, not lossless authoring interchange |

The diagram follows typed expression → computed observation → explicit binding →
generated assessment → primitive input → downstream result. Presumption routes and
effective values remain separate. Full case/source material is in the companion
projection rather than expanded before the requested chain. The existing renderer
can make the complete chain tall; this round does not change its layout.

`source-map.json` uses `yuho.source-composition-map/v0.1-experimental`. Original
anchors use zero-based half-open UTF-8 byte offsets and one-based lines/byte columns.
LF advances the line; CR counts as a byte. The old parsers retain token starts, not
ends: this adapter anchors the **whole declaration line**, including the whole
requirement line for inline children. It does not fabricate precise operand extents.
Case assertions retain their entire explicitly supplied source text. The source map
and embedded sources distinguish these anchors from generated kernel spans and from
an independently authenticated legal quotation. Locator-only original sources remain
locator-only; no URLs are fetched.

Typed declaration locations come from actual parser-retained declaration tokens.
Assessments resolve by predicate plus ordered entity tuple. Positional argument
roles become `argument-1`, etc.; only the relationship category shared with the SDK
is admitted. Other source predicate categories are rejected. Inline children receive deterministic generated
SDK expression IDs and their own **actual backend** observations; these are not
original named source declarations. The source root keeps its `q:` identity.
Proof law-node rule IDs use authored offence/exception IDs (`o:entry`,
`x:emergency-rescue`); source execution rule names (`r:entry`, etc.) remain citations.

Cross-component navigation is delegated unchanged to the repaired computed-input
projection contract. A source identity coinciding with `rule:0` never justifies a
navigation edge; category, occurrence and snapshot mappings determine correspondence.

## Evidence and assurance boundary

```sh
# At the checkout, after building:
cabal v2-test yuho-test yuho-sdk-test --offline -j1 \
  --with-compiler=ghc-9.8.4 --test-show-details=direct
python3 test/source_composition.py "$YUHO"
```

`SourceCompositionChecks` compares fourteen source projects to independently authored
public-SDK references, including requirement observations, branch/skip reasons,
trigger/rebuttal values, direct/effective leaves and route states. The CLI regression
copies both projects outside the checkout and tests specified outcomes, deterministic
checking, schema validation, complete bindings, byte-identical artifact replay,
wrong-scope/category/tuple refusals, conflicting direct inputs, UTF-8 source retention,
long IDs and same-status revisions. Existing `ComputedInputRepairChecks` retain the
exact `rule:0` collision, computed rebuttal, Unicode ID and semantic-navigation tests;
source syntax does not bypass the synthetic checker's `f:` leaf-identity boundary.

Parsing, this source-to-SDK translation, source mapping and projections are tested
boundaries, **not mechanically proved translations**. No new Lean theorem is claimed.
The existing backend/formal assurance distinctions in the
[compiler guide](compiler-guide.md#what-is-proved-tested-and-still-unproved) still apply.
These development examples do not change accepted release archive membership or
rights policy. Any release-manifest staleness is reported separately.

For local non-Haskell integration, see the [machine interface](machine-interface.md)
and its standard-library Python consumer. Frozen replay remains an evaluation.

## Failure-safe export publication (Linux)

`compose run` and `compose replay` compute and validate all eight export byte
strings before publication. They write them into a private temporary directory
in the destination's existing parent, then publish the complete directory with
Linux `renameat2(RENAME_NOREPLACE)`. Existing files, directories and links,
including racing destinations, are never replaced. Failed writes or publication
remove only this invocation's temporary directory; the requested destination
remains absent (or retains the unrelated existing/racing entry). Temporary names
start with `.yuho-compose-` and are not committed exports.

The output must name a new directory beneath real, non-symlink ancestors, without
`..` traversal; its parent must already exist. This contract assumes ancestors
are not concurrently renamed/replaced by another actor. It provides atomic
visibility and no replacement on supported Linux filesystems, rather than crash
or power-loss durability. Unsupported platforms/filesystems refuse publication
without a non-atomic fallback. Process termination can leave private staging
files, but cannot expose a partially written requested destination. Success is
reported only after publication; a broken response pipe can leave a complete
published directory without a delivered acknowledgement.
