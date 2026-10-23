# Executable language workbench

Read the [compiler guide](compiler-guide.md), this page, then the
[machine contract](machine-interface.md). All six exercises under
[examples/language-workbench](../examples/language-workbench) are fictional technical
models. Their assertions/classifications are authored inputs, not automatic evidence
assessment. Stable Synthetic grammar identifiers do not make the examples statutory
models. The sixth reuses the original fictional Round 2 source pattern.

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
YUHO="$(cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4)"
# Copies the sources and executes all documented cases outside the checkout:
python3 test/machine_workbench.py "$YUHO" --output /tmp/yuho-workbench-new
```

`cases.json` is a hand-specified table of 19 outcomes, source/scenario paths, view
choices and inspection availability. The runner executes check, compile, run,
inspection (or its expected refusal) and JSON/XML/SVG diagrams, or composition's
complete exports, for each case. It compares the machine payload to the direct CLI,
checks deterministic compilation, validates machine schemas and tests no-overwrite.
`--output` must name a new directory. Existing historical fixtures/expected responses
are never regenerated. Python's test harness additionally needs `jsonschema`; the
example subprocess client itself needs only the standard library.

## Six source entrances

Set `W=examples/language-workbench` at the checkout. These commands are representative;
[cases.json](../examples/language-workbench/cases.json) enumerates every executed
variant. `--scenario` remains separate from law/model structure.

| Exercise and actual command | Backend and independently specified outcomes | Graph and source exercise |
| --- | --- | --- |
| `yuho run "$W/01-requirements/law.yh" --scenario "$W/01-requirements/defeated.yhs"` | SuppliedProofStatus-v1: all main conditions proved, both exception conditions proved → defeated/not_satisfied. Other scenarios give satisfied/unresolved. A partial assignment fails AND but satisfies the alternative OR model | `inspect ...` has parsed/checked/structural Core/lowered stages; `diagram ... --view trace --format svg --output NEW.svg` exposes requirements and exception. Quote spans in the kernel are generated; original `.yh` declarations are in inspection |
| `yuho run "$W/02-definitions/case.yh"` | TypedFiniteRules-v1 per allegation: one shared compound `q:common = all(available(...), inspected(...))` is referenced by `q:one` and `q:two`, then two rules. Allegation one: satisfied/not_satisfied; allegation two: not_satisfied/unresolved | `diagram ... --view case ...`. Each allegation independently evaluates the complete grounded model; no aggregate case truth. This is native named-expression reuse, not an assertion of SDK v0.2 occurrence equivalence. Case inspection is refused; the runner also inspects and diagrams the underlying shared law with the complete `law-input.yhs` scenario |
| `yuho run "$W/03-typed/law.yh" --scenario "$W/03-typed/36.yhs"` | TypedFiniteRules-v1: explicit `permitted(actor:one,resource:room)` and exact `measured > threshold`. 34/35/36 → not_satisfied/not_satisfied/satisfied; unresolved scalar → unresolved | `inspect ...`; `diagram ... --view trace ...`. Separate actor:two classification cannot supply actor:one. Numeric values are dimensionless externally normalised integers; no physical-unit claim |
| `yuho run "$W/04-presumptions/active.yh"` | RegisteredPresumptionDerivations-v1: active + direct not_satisfied → effective satisfied. Rebutted → effective not_satisfied; direct-proof dominance → effective satisfied despite rebutted route | `inspect ...` order parsed→lowered→checked; `diagram ... --view trace ...`. Registration/trigger/rebuttal/direct/effective distinctions are retained. A rebutted route does not prove factual falsity |
| `yuho run "$W/05-temporal/law.yh" --scenario "$W/05-temporal/boundary.yhs"` | Native temporal selector → SuppliedProofStatus-v1. 2023-12-31 selects AND/not_satisfied; 2024-01-01 and 2024-01-02 select OR/satisfied | `diagram ... --view trace ...` retains selected temporal provenance. Before/after model quotes are fictional. Temporal wrapper inspection is refused; normal execution remains supported. Native run is a proof result, not a complete SDK temporal-selection record |
| `yuho compose run "$W/06-composition/true.project.yh" --output NEW_DIRECTORY` | TypedFiniteRules-v1 → explicit technical mapping → SuppliedProofStatus-v1. True/false/unresolved retain the corresponding downstream technical states | Complete combined/component projections, original source anchors, separate snapshots and bindings plus reference views. Two same-labelled actors remain distinct IDs. `unsupported.project.yh` attempts a typed destination and fails SFC002 |

For native diagrams, supply all three flags (`--view`, `--format`, `--output`) and
retain any listed `--scenario`. These are simplified graph exports, not lossless SDK
authoring interchange or complete projection bindings. Composition exports do include
complete projections and inclusion/omission bindings. The workbench deliberately uses
the correct native entry point for each form instead of forcing them into compose.

## Implementation and assurance map

| Construct | Parser/checker/lowering/backend evidence | Scope of assurance |
| --- | --- | --- |
| Proof AND/OR, explicit exception | Surface.Parser / Surface.Check / Surface.Compile; CoreYuho.Normalize on the diagram branch; SuppliedProofStatus.Evaluate | Native fixture outcomes, old bytes, protocol tests; Lean `Requirement.evaluate`, `requirement_evaluation_deterministic`, `allStatus_unresolved_exact`, `anyStatus_unresolved_exact` concern their named finite semantics |
| Shared named expressions, scoped cases | Surface.TypedFinite; CoreYuho.TypedFinite; TypedFiniteRules.Run | Case isolation and shared-reference tests; no new theorem about case loading or SDK equivalence |
| Ground relationships and integers | Surface.TypedFinite; TypedFiniteRules.Run.decodeTypedFiniteRequest; CoreYuho.TypedFinite | Exact boundary tests; Lean `compareScalar`, `comparison_deterministic`; nominal scope/provenance translation is tested, not proved |
| Operative presumption | Surface.Presumption; Presumption.Decode/Validate/Resolve/Evaluate/Run | Route/direct/effective checks; Lean `derivePresumption`, `presumption_result_deterministic`, `presumption_separate_from_offence` do not prove source translation |
| Temporal wrapper | Surface.Temporal; Temporal.Interval; selected ordinary source pipeline | Half-open boundary/native-SDK conformance tests. No theorem of legal applicability |
| Explicit computed binding | Surface.Computed; Authoring.ComputedInput and its qualified projection correspondence | Round 2 independent SDK comparisons plus machine equality. No new evaluator, no proof of translation or legal sufficiency |
| Machine control / Python | Yuho.Machine delegates to existing CLI or public artifact decoder/validator | Closed request schemas, process/file/error tests and deterministic outputs. No new mechanised claim |

Exact Lean file links and the limits of Haskell/Lean vector conformance are in the
[compiler assurance section](compiler-guide.md#what-is-proved-tested-and-still-unproved).
The new interface does not increase the extent of those proofs.

The tests exercise irrelevant-entity independence (expression/rule/proposition fields
unchanged), actor replacement (distinct tuple, independent classification), deterministic
compilation, missing versus unresolved, and strict integer boundaries. Source edits
may change digests and mappings even when computed statuses are unchanged; those
hashes are not normalised away as if old results were attachable.

For the admitted composition overlap, native `SourceCompositionChecks` constructs
independent public-SDK references and prints `source-composition-parity` records.
Pass the native test log as `--sdk-evidence LOG` to the machine/workbench runner to
compare machine-executed `.yh` outcomes with those references, including requirements,
branches/skips, trigger/rebuttal and direct/effective route states. All paths share
existing evaluator code; CLI/machine paths also share lowering. Equality is bounded
regression evidence, not independent proof of the compiler. Source/complete-projection
identities are also checked against saved replay without flattening categories.

## Interpretation and limits

Conjunction, actor-scoped classifications, reusable definitions, rebuttable routes
and temporal editions resemble modelling problems in the existing
[Singapore research index](../research/singapore/CORPUS-INDEX.md). These fictional
examples add no statutory corpus and establish no general Singapore criminal-law
coverage, current applicability, rebuttal sufficiency or human-author usability.

Ordinary native execution, inspection, source composition and Haskell authoring have
different admission boundaries. Arbitrary statutory-family translation, general
cross-backend chaining, parameterised source composition and universal JSON/source
round trips remain unsupported. Source comments are retained as exact text where
specified, but there is no comment-preserving formatter. Native layouts can be large;
complete composition records are available independently of compact reference layouts.

This is development against the current checkout. The accepted distribution archive
and manifest are not refreshed by these commands. Release-manifest failures must be
reported separately from semantic tests; a passing workbench is not release readiness.

Native diagrams now use the [v0.2 observation contract](diagrams.md): skipped
guards are explicit, numeric operands remain visible, and presumption traces
separate direct support, global derivations, effective values and downstream
execution. Cards wrap all text and size from their content; routing lanes and
canvas bounds follow the actual graph. Dense graphs can still need zooming.
These remain simplified native views, while composition exports retain complete
projections and bindings. Historical v0.1 examples in docs/artifacts are retained
as recorded evidence rather than silently regenerated.
