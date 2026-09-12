# TypedBooleanFacts-v1

**Status:** Normative technical specification for the third bounded Haskell kernel fragment, 12 September 2026. It does not establish evidential sufficiency, legal correctness or implementation refinement.

## Scope and identity

`TypedBooleanFacts-v1` is a third closed discriminator under `yuho.kernel-protocol/v1`, `yuho.kernel-input/v1` and `yuho.kernel-result/v1`. It inherits the complete, validated, finite acyclic registry, root selection, source/span policy, recursive Boolean requirements, alternative branches and registered `is_infringed` exception guards from [AcyclicGuardedExceptions-v1](ACYCLIC-GUARDED-EXCEPTIONS-V1.md). The existing Boolean and exception variants remain independently versioned and byte-stable. Canonical IR v1.2 is untouched.

The `facts` map is keyed by **globally unique executable leaf IDs**. Each value is a *typed leaf binding*: an asserted Boolean for that one leaf, not a general proposition, evidence item, shared real-world fact identity or legal-review record. Distinct leaf IDs are not equated because their descriptions resemble each other. Exact IDs are required; no normalized-name fallback, implicit registry or target-local override exists. The map is total over every leaf in the entire supplied registry, including unreachable rules and branches that will not execute, and has no extra keys.

Only the binding's `value` participates in Boolean evaluation. There are no proof states, proof thresholds, confidence values, evidential sufficiency calculations, presumptions, rebuttal, arbitrary typed values, temporal applicability, jurisdictional rule selection, penalties, outcomes, dispositions, new source syntax, authenticated evidence provenance or section 84/CPC rules.

## Closed wire records

The request envelope and registry are the exception fragment's closed shape. Its `fragment` is exactly `TypedBooleanFacts-v1`. Each fact-map value is a closed object with required `type: "bool"` and JSON Boolean `value`. Optional fields are `burden`, `standard_of_proof` and `provenance`. A `leaf` requirement alone may additionally contain optional, nonempty, closed `declared_metadata`, whose fields are `burden` and `standard_of_proof`. Groups cannot declare metadata.

| Field | Shape and allowed values | Effect |
|---|---|---|
| `type` | Required literal `bool`. | Validates the wire type; no coercion. |
| `value` | Required JSON `true` or `false`. | The sole Boolean evaluation input. |
| `burden` | Closed object requiring `holder: prosecution\|defence` and `kind: unspecified\|legal\|evidential`. | Binding annotation checked against a leaf declaration when one exists. `unspecified` records an unclassified legacy label; it is not inferred to be legal or evidential. |
| `standard_of_proof` | `beyond_reasonable_doubt\|balance_of_probabilities`. | Binding annotation checked against a leaf declaration when one exists. `prima_facie` is unsupported. |
| `provenance` | Nonempty closed object with optional `source_label`, `recorded_date`, `jurisdiction`. | Trace annotation only. |

`source_label` is nonempty UTF-8 text of at most 256 bytes; `jurisdiction` is nonempty UTF-8 text of at most 64 bytes. `recorded_date` is a real zero-padded `YYYY-MM-DD` Gregorian date. These strings retain their exact bytes after UTF-8 decoding; they are not normalized to determine a judgment. `source_label` is **descriptive only**: it is neither an authenticated authority, stable source-registry reference nor legal-review record. Stronger evidence provenance requires a later versioned model. Provenance date and jurisdiction are validated but never compared with policy `reference_date` or used for applicability. Empty burden, `declared_metadata` and `provenance` objects, unknown fields and duplicate JSON keys reject. Existing one-line request-byte, line-draining, 64-container JSON-depth, semantic-node, UTF-8 and source-span limits continue to apply.

Primitive shorthand, string/number/null truthiness, `confidence`, `evidential_status`, `prima_facie` and proof-state constructors are outside this fragment. The migration-only [explicit projection helper](../../rewrite/haskell/test/typed-fixtures/legacy_adapter.py) reports every unsupported field or coercion and labels primitive Boolean projection and unclassified burdens; it is not a production CLI adapter. A future production adapter must likewise report any unsupported or discarded metadata rather than silently losing it.

## Validation and binding algebra

The subprocess bounds and parses the whole JSON line before domain recursion. Typed decoding checks the closed envelope, policy, node count, fact records and leaf declarations, then reuses the exception-fragment source, span, registry and guard decoder. Complete-graph validation checks IDs, total facts, target resolution, source references and acyclicity. Binding validation then visits **all rules and leaves in registry/declaration order**, regardless of Boolean value, reachability or whether a branch would run. For each leaf it checks burden before standard. No rule evaluation begins until all checks succeed.

Each declared field is checked independently:

| Leaf declaration | Bound fact field | Binding result |
|---|---|---|
| Absent | Absent | `not_declared`; valid. |
| Absent | Present | `not_declared`; valid and retained as an untested annotation. |
| Present | Exactly equal, including burden holder **and** kind | `matched`; valid. |
| Present | Absent or different | Whole request rejects with `KINV007`. |

`KINV007` has `stage=validate`, `severity=error`, the leaf declaration's path and source span, plus stable `rule`, `leaf`, `field`, `expected`, `supplied` and `source_path` parameters. `supplied` is the literal `absent` when missing. Burdens encode as `holder:kind` in diagnostic parameters. A false binding with incompatible metadata rejects just as a true one does. Rejection has no partial rule judgment. A successful `matched` observation means **only** that two annotations agree. It does not mean that evidence proves the leaf or that a burden is discharged.

Unknown closed-object fields remain `KINV004`; malformed JSON, wrong scalar types and resource decoding are `KDEC001/002`; unsupported typed constructors, guard forms and standard values are `KCAP001`; missing/extra facts and graph failures retain their existing invariant codes. Protocol-version errors remain `KPROT001`; evaluation inconsistencies use `KERR001`. None is a valid negative Boolean judgment. A malformed or overlong line that cannot be fragment-dispatched retains the existing generic transport rejection envelope.

## Evaluation, trace and result

After validation, project each typed binding's `value` exactly once to the Boolean map used by the established pure evaluator. Retain the typed binding map and declarations for observations. The validated graph and every registered exception target use the identical bindings, Boolean projection, reference date, deterministic policy and registry. A guard still evaluates only after its branch's ordinary requirements are true. All guards on a satisfied branch are evaluated, all true exceptions are reported, and declaration order controls presentation rather than priority. A defeated branch remains distinguishable from an ordinary requirement failure.

The third closed result variant retains the exception result's root/rule/branch status, ordinary trace, exception observations, dependency edges and ordered diagnostics. Each evaluated rule additionally has `fact_observations`. Each occurrence of an evaluated leaf has `rule_id`, `branch_id`, `leaf_id`, literal `type: "bool"`, Boolean `value`, `burden_check`, `standard_check` and supplied `provenance` when present. Both check fields are exactly `matched` or `not_declared`. Observations follow the existing ordinary trace order, including repeated occurrences on alternative or inherited paths. Unreached rules are still validated but do not acquire invented evaluation observations. Mapping keys use canonical sorted JSON encoding; source-ordered lists are not sorted.

`value` cannot turn false into true through metadata, cannot create `unresolved`, cannot select an exception and cannot change branch aggregation. With total Boolean bindings and a valid closed DAG, accepted wire results are true or false. The pre-existing three-valued exception aggregation remains tested at its internal boundary; this fragment adds no wire uncertainty source. A true kernel result is a **technical Boolean judgment**, not `proved`, `not_proved`, `satisfied_burden` or a criminal outcome.

## Migration, vectors and assurance

The [T01–T53 cases](../../rewrite/haskell/test/typed-fixtures/CASES.json), [manifest](../../rewrite/haskell/test/typed-fixtures/MANIFEST.json), [migration probes](../../rewrite/haskell/test/typed-fixtures/MIGRATION-PROBES.json) and [proof-neutral vectors](../../rewrite/haskell/test/typed-fixtures/PROOF-VECTORS.json) distinguish positive/negative Boolean judgments from malformed, invariant and capability rejections. T53 binds two similarly named but distinct leaf IDs to different values without inferring shared proposition identity. Vectors preserve leaf bindings, declarations, Boolean projection, branch paths and statuses, guard/dependency edges, ordered leaf observations, provenance and invalid-binding classifications. The proposed reference relation is confined to **successfully validated** typed requests and compares Boolean projection, branch/rule judgments, fired exception IDs and essential ordered observations. No theorem prover was run and no implementation-refinement or legal-correctness claim follows from these fixtures.

| Legacy Python observation | Typed fragment decision |
|---|---|
| Non-Boolean primitive values can be truthy. | Boolean records only; no coercion. |
| Typed objects are permissive and `type` may disagree with `value`. | Closed records with required `type: bool` and Boolean `value`. |
| Exact lookup falls back to first normalized-name match. | Exact globally unique leaf IDs only. |
| A supplied burden or standard mismatch can change a true element to false with prose reasoning. | `KINV007` rejects the whole incompatible binding before evaluation. |
| Primitive Boolean facts may omit a declared burden. | Primitive projection is adapter-only; a missing declared annotation rejects. |
| Unknown metadata can be ignored in normalization. | Closed wire objects reject; migration projection reports unsupported fields. |

These are technical fragment rules, not a universal doctrine. The official Singapore Judiciary's [Ma Hongjin case brief](https://www.judiciary.gov.sg/docs/default-source/judgments-docs/ma-hongjin-v-scp-holdings-pte-ltd.pdf) and [PP v GCK case brief](https://www.judiciary.gov.sg/docs/default-source/judgments-docs/pp-v-gck.pdf?sfvrsn=4885c136_2), accessed 12 September 2026, distinguish legal and evidential burdens; they inform labels only and do not validate this evaluator or any jurisdiction-wide rule.
