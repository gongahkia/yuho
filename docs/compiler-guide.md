# Inspecting the Yuho compiler

Start here for the source compiler; continue with the [language reference](language-reference.md),
[formal semantics](formal-semantics.md) and [assurance boundaries](assurance.md).
For graph authorship, start with the [Haskell quickstart](authoring-quickstart.md).
For readable typed → explicit binding → proof/presumption projects, see
[source composition](source-composition.md). Its `compose check` is static; its
`compose run` and `compose replay` deliberately evaluate through the existing SDK.
Text and public graph authoring reach existing technical evaluators through distinct
adapters. Neither entrance replaces the semantic graphs, case assertions, explicit
assessments or provenance. The SDK profiles are **not interchangeable language versions**.

## Reproduce a compilation

From the complete checkout, with GHC 9.8.4 and Cabal 3.12.1.0:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
YUHO=$(cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4)
"$YUHO" inspect examples/synthetic/restricted_entry.yh \
  --scenario examples/synthetic/scenario_all_proved.yh
"$YUHO" inspect test/fixtures/typed-authoring/permission.yh \
  --scenario test/fixtures/typed-authoring/permission.yhs --stage checked
"$YUHO" inspect examples/synthetic/presumption_active.yh --stage lowered
python3 test/compiler_inspection.py "$YUHO"
```

`inspect --help` describes the opt-in command. `--stage` accepts `parsed`, `checked`,
`normalized`, `lowered`, or `all` (default). `--output` writes a **new** file and refuses
to overwrite an existing one. Standard output otherwise contains one JSON record;
errors use the existing diagnostic JSON on standard error with exit 1. Inspection
never evaluates a model. A lowered request contains `operation: "evaluate"` because
that is the existing kernel request format, but inspection does not execute it.

The structured envelope is `yuho.compiler-inspection/v0.1-experimental`:

- `fragment`, `evaluated: false`, source paths/byte counts/SHA-256 fingerprints;
- `coordinates`, ordered `stages` with `representation`, `depends_on`, and `data`;
- `unavailable_stages`, with explicit reasons;
- lowered `request`, exact `request_sha256`, and category-specific source-to-kernel
  `mappings` with JSON pointers. These are compilation identities, not run observations.

This is an inspection format, not lossless authored-document interchange or a new
universal IR. Source token starts, retained declarations and actual expression trees
are encoded explicitly; opaque runtime objects and Haskell `Show` output are absent.
Typed parsed output is a declaration overview plus the complete lexer token stream.

## Actual stages and branches

| Input | Parsed | Checked/resolved | Normalized | Lowered |
| --- | --- | --- | --- | --- |
| Direct proof `model` | `Surface.Model` declarations, references and source starts | `Checked` assignments and `Resolved` requirement trees | Structural fields of existing `CoreProgram`, on the **diagram branch** | Existing `lowerChecked` request |
| Ground `typed-rules-model` | `RawModel` declarations and parser-built `FiniteExpr` | Existing `TypedFiniteProgram`, with structural and ground-input presence checks | No separate pre-execution normalization stage | Existing `encodeTypedFiniteRequest` |
| `presumption-program` | Program, base file references and registration tokens | Existing proof checking, presumption decoder/validator and registration target index | Existing presumption Core view requires results; unavailable before evaluation | Existing registered request, including its base proof request |

Proof lowering consumes `Checked` directly; it does **not** consume `CoreProgram`.
Accordingly, normalized and lowered records both depend on `checked`. Structural
normalization is factored from the existing diagram normalizer; execution observations
are added only by the ordinary evaluated diagram path. `observations: null` means
not evaluated. Supplied classifications remain visible as supplied information.

Requesting an unavailable stage returns `SFI003`. `all` includes only available stages
and describes the unavailable ones. `parsed` runs parsing only; it can inspect a
model with an unresolved reference or no scenario. Later stages reject missing inputs.
No invented child observations or presumption route states appear in inspection.

The presumption pipeline has a different order: `parsed → lowered → checked`.
Preparation checks and lowers its base proof model, then adds registrations; the
existing backend decoder/validator checks that request. Its `checked` record is
therefore a post-lowering registration index. `--stage lowered` exposes preparation
without running that subsequent validation; it does not certify executability.

Round 1 inspection supports direct Section and Synthetic proof bodies without
candidate penalties, ground typed rules (including scalar comparisons, finite groups,
named references, technical negation/cardinality), and presumption programs with
those direct proof bases. Checked typed inspection excludes parameters, quantification,
modules, norms and responsibility routes. Source wrappers/cases, statutory proof
families, SDK JSON inputs and their composition are explicitly unsupported by this
**inspection command**, not necessarily by the language. Use their established
`compile`, `run`, `explain`, diagram or SDK operations. `SFI002` states this boundary.
No claim is made that every other source construct has been inspected in this round.

## Source → backend → observation → diagram

```sh
"$YUHO" compile examples/synthetic/restricted_entry.yh \
  --scenario examples/synthetic/scenario_all_proved.yh
"$YUHO" run examples/synthetic/restricted_entry.yh \
  --scenario examples/synthetic/scenario_all_proved.yh
mkdir -p /tmp/yuho-compiler-guide
"$YUHO" diagram examples/synthetic/restricted_entry.yh \
  --scenario examples/synthetic/scenario_all_proved.yh \
  --view trace --format json --output /tmp/yuho-compiler-guide/proof-diagram.json
```

Use a fresh output path on replay. The proof request delegates to
`SuppliedProofStatus-v1`. Typed requests delegate to `TypedFiniteRules-v1`;
presumptions delegate to `RegisteredPresumptionDerivations-v1`, then the ordinary
proof evaluator uses effective leaf values. Direct proof, effective support and
route states remain different categories. The ordinary `run` command returns
backend observations; `diagram` combines the corresponding authored structure and
computation. Inspection stops before those operations.

The CLI's JSON/XML/SVG diagrams are simplified semantic views. They are **not** the
SDK's complete authored projections or lossless authoring files. Public Haskell
`projectEvaluation`, `projectTypedEvaluation`, `projectPresumptionEvaluation` and
profile-specific projection operations retain richer snapshots, authored identities,
occurrences, sources and inclusion/omission bindings. See the SDK
[export recipe](authoring-sdk.md#export-recipe). CLI inspection JSON cannot be loaded
as an `AuthoringDocument`, and the CLI does not auto-detect SDK profile JSON.

## Executable capability map

The [CLI witness manifest](../test/compiler_capabilities.json) attaches each of the
following source claims to a real command and fixture. The inspection test executes
all entries, from outside the checkout. `@` in that manifest means a checkout-relative
file argument. It is not Yuho source syntax.

| Construct / entrance | Implementation | Executable evidence / boundary |
| --- | --- | --- |
| Section / synthetic proof trees, selected supplied statuses, exceptions | `Surface.Parser`, `Check`, `Resolve`, `Lower`; `SuppliedProofStatus` | Manifest `section`, `proof`; `SurfaceChecks` retains exact independent request/response bytes |
| Ground typed relations and integer thresholds | `Surface.TypedFinite`, `CoreYuho.TypedFinite`, `TypedFiniteRules.Run` | Manifest `typed-ground`, `typed-threshold`; `TypedAuthoringChecks` independently compares graph and source adapters |
| Finite quantifiers, technical negation/cardinality, date/enum/money, priorities | Same typed source pipeline | Manifest `typed-finite`; broader than SDK v0.3; no universal quantity conversion |
| Exact-version typed modules and scoped cases | `Surface.TypedFinite` module/case loaders | Manifest `typed-modules`, `typed-case`; not admitted by checked inspection |
| Norm and responsibility-route metadata elaboration | Typed checker and existing finite rules | Manifest `norms-routes`; no procedural enforcement or automatic legal responsibility |
| Operative presumption registrations | `Surface.Presumption`, `Presumption.Decode/Validate/Run` | Manifest `presumption`; `PresumptionChecks`; not a trigger-AND-not-rebuttal replacement |
| Authored temporal intervals and conduct date | `Surface.Temporal`, shared `Temporal.Interval` | Manifest `temporal`; `TemporalAuthoringChecks`; technical selection, not legal applicability |
| Statutory definitions, participation, attempt, actor-scoped exceptions, abetment | Dedicated `Surface.Definitions/Participation/ActorExceptions/Abetment`, checker/lowerer | Manifest `definitions`, `participation`, `attempt`, `actor-exceptions`, `abetment` checks; corresponding `*SurfaceChecks` in `cabal v2-test yuho-test` execute supplied scenarios; bounded research forms, not a general statutory interpreter |
| SDK graph authorship and complete projections | `Yuho.Authoring` facade and profile modules | Consumer commands below; no parser token construction required |

Public SDK JSON uses strict, explicit profile decoders. These are callable through
Haskell, **not** through `yuho compile <authored.json>`. The kernel executable accepts
kernel request JSON, which is another contract again.

| Authored format / Haskell entrance | What it admits | Reproducible public consumer check |
| --- | --- | --- |
| v0.1 `decodeDocument`, `compileAnalysis` | Proof trees, case assertions, assessments, edits and interactions | `python3 test/authoring_consumer.py "$(cabal list-bin exe:yuho-authoring-consumer)"`; `hurt_consumer.py`, `editing_consumer.py`, `interaction_consumer.py` use the same executable and retained hurt/section 441 fixture |
| v0.2 `decodeDocument`, linked definition operations | Explicit acyclic definition reuse in supported independent scopes | `python3 test/linked_definitions_consumer.py "$(cabal list-bin exe:yuho-linked-definitions)"` |
| v0.3 `decodeTypedDocument`, `compileTypedAnalysis` | Ground nominal tuples and exact integer comparisons | `python3 test/typed_authoring_consumer.py "$(cabal list-bin exe:yuho-typed-authoring)"` |
| v0.4 `decodePresumptionDocument`, `compilePresumptionAnalysis` | Registered derivations over admitted proof models | `python3 test/presumption_authoring_consumer.py "$(cabal list-bin exe:yuho-presumption-consumer)"` |
| v0.5 `decodeTemporalDocument`, `compileTemporalAnalysis` | Temporal wrapper over complete v0.1 proof candidates | `python3 test/temporal_authoring_consumer.py "$(cabal list-bin exe:yuho-temporal-consumer)"` |
| Explicit computed-input integration artifact | One actual named typed observation → authorised proof/presumption input mapping | `python3 test/computed_input_consumer.py "$(cabal list-bin exe:yuho-computed-input)"` |

Each consumer constructs or loads its example under `examples/`, executes its public
API and checks saved documents/projections. Unsupported combinations remain refusals:
these profiles do not imply arbitrary typed definitions, temporal mixed-backend
execution or general result-consuming chaining. See each [profile contract](authoring-sdk.md#current-api-map).

## Diagnostics and coordinates

Existing diagnostic codes are retained. In particular typed expression `SFT003`
(unknown name), `SFT004` (arity) and `SFT005` (nominal argument type) now point at the
retained enclosing declaration token instead of a fabricated line-1 expression token.
Direct predicate requirement errors include the related predicate declaration when
available. Nested expression tokens were not retained by this parser: the location
is the containing declaration, **not** an invented precise operand span. Imported
declaration source-file retention remains a limitation of the older typed loader;
inspection refuses imports rather than claiming those tokens belong to the host.

Source lexer lines/columns are one-based; columns count UTF-8 **bytes**, not code
points, UTF-16 units, tab expansion or display cells. Inspection byte offsets are
zero-based. Only token starts are retained; no AST end span is fabricated. The
source lexer accepts LF and rejects CR. Original-law anchors are a separate SDK
contract, as are generated kernel spans (half-open byte ranges within generated
source text). A compiled quote span is not an original legislative location.

The permanent tests exercise parsing, unresolved names, wrong declaration kind,
predicate arity/type, missing classifications, invalid temporal gaps, unsupported
inspection composition and multibyte locations. Missing classification is an error;
an explicitly unresolved classification is a supplied value.

## What is proved, tested, and still unproved

Lean 4.10.0 proves named finite semantic results, not the source compiler. Exact
references include:

- [`Yuho.CoreYuho.Requirement.evaluate`](../mechanisation/Yuho/CoreYuho/Semantics.lean)
  and [`requirement_evaluation_deterministic`, `allStatus_unresolved_exact`,
  `anyStatus_unresolved_exact`](../mechanisation/Yuho/CoreYuho/Theorems.lean).
- [`Yuho.CoreYuho.derivePresumption`, `applyPresumptions`](../mechanisation/Yuho/CoreYuho/Semantics.lean)
  and [`presumption_result_deterministic`, `presumption_state_exactly_one`,
  `presumption_separate_from_offence`](../mechanisation/Yuho/CoreYuho/Theorems.lean).
- [`Yuho.CoreYuho.TypedFinite.compareScalar`, `comparison_deterministic`,
  `cardinality_deterministic`](../mechanisation/Yuho/CoreYuho/TypedFinite.lean).

The theorem registry is checked by `python3 scripts/verify_core_yuho_theorems.py`;
`make lean` additionally builds the pinned Lean project. Independent finite Haskell/
Lean conformance corpora run through `make conformance`. These are bounded equality
checks, not a proof that parsers, checking, lowering, file resolution, SDK adapters,
inspection serialization or diagram projections preserve semantics in general.

`make test` runs native tests and the inspection CLI suite. `make protocols` checks
existing wire behavior; `make docs` checks links and claims. Existing expected files
are not regenerated by this workflow. Release manifest/archive staleness after source
changes is reported separately; compiler development does not authorise changing
rights/distribution policy or replacing a release candidate.

The executable [language workbench](language-workbench.md) and local
[machine interface](machine-interface.md) extend these command witnesses without
changing their individual admission boundaries or formal assurance claims.
