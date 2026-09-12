# SuppliedProofStatus-v1

**Status:** Implemented technical `yuho.kernel-input/v1` and `yuho.kernel-result/v1` fragment, 12 September 2026. It extends [PenaltyTerms-v1](PENALTY-TERMS-V1.md) without altering Canonical IR v1.2 or the first five wire variants.

## Meaning and boundary

Each `facts` entry binds one exact globally unique executable leaf ID to a **supplied**, externally assigned classification. The leaf ID identifies a proposition in this technical model; similar descriptions or issuer labels do not merge propositions. The kernel validates and composes classifications. It does not assess evidence, calculate discharge of a burden, infer factual truth, derive presumptions, adjudicate rebuttal, choose a sentence, or determine conviction, acquittal or disposition. `satisfied` and `not_satisfied` are technical projections, not legal outcomes.

The only supplied status constructors are closed objects: `{"kind":"proved"}`, `{"kind":"not_proved"}`, and `{"kind":"unresolved","reason":"not_determined"}` or `{"kind":"unresolved","reason":"external_decision_pending"}`. `not_proved` does not mean factually false. `unresolved` is a valid supplied semantic classification, never a substitute for invalid input. Bare strings, Boolean aliases, confidence, probabilities, thresholds, arbitrary reasons, `presumed` and `rebutted` are outside this fragment. Recognized `presumed` and `rebutted` constructors receive `KCAP001`.

## Closed input and validation

The sixth request keeps the fifth request's protocol, full registry, typed leaf declarations, exceptions, penalties, terms, policy, sources and root selection. Its `fragment` is `SuppliedProofStatus-v1`. Every `facts` value is a closed record with required `proof_status` and `status_source`; it has **no** `value` or `type`. Optional `burden`, `standard_of_proof` and descriptive `provenance` retain the [typed Boolean metadata](TYPED-BOOLEAN-FACTS-V1.md) shapes and enums. The map is total for all executable leaves in the complete registry, including unreachable rules and dependency targets, and rejects extra keys. Matching is by exact leaf ID only.

`status_source` is closed and requires `assignment_id`, `source_id`, `span`, `origin` and `issuer_label`. Assignment IDs are globally unique and cannot collide with graph, penalty or term semantic IDs. `source_id` resolves to one hash-checked input source; its UTF-8 span must agree with source byte positions and display positions. `origin` is exactly `external_assertion` or `synthetic_fixture`. `issuer_label` is nonempty descriptive text bounded to 256 UTF-8 bytes; assignment and source IDs are bounded to 128 UTF-8 bytes. Hash checking establishes input consistency, **not authentication**. Neither the source record nor issuer label proves authority or reliability. Stronger provenance needs a later versioned model.

Validation precedes evaluation: bounded JSON and closed-shape decoding; checked sources, spans and semantic IDs; total leaf binding and whole-registry acyclic target validation; declared burden/standard equality; assignment identity/source/span checks; penalty ID/guard scope and 4,096 expanded-occurrence checks; every penalty term tree (including unselected and unreachable declarations); then pure rule evaluation and root-only selection. Existing JSON-depth 64, request-byte 1,048,576, `max_nodes` 1–1,024 and term-depth 16 limits remain. A declared burden or standard must be supplied and exactly match for `proved`, `not_proved` and `unresolved` alike. Mismatch is `KINV007`, with no judgment. A successful metadata match means only that annotations agree; it does not mean a burden was discharged.

Malformed JSON, missing fields, unknown fields and resource failures retain the existing `KDEC001/002` or closed-field `KINV004` conventions. `KINV010` covers duplicate/colliding assignment IDs and well-shaped invalid status-source references or spans. Existing `KINV001–009` continue to cover missing/extra leaf IDs, graph, metadata, penalty and term invariants. Unsupported presumption/rebuttal constructors are `KCAP001`; `KERR001` denotes an impossible post-validation inconsistency. A rejection has no partial rule result, selected declaration or term. Invalid input never becomes semantic `unresolved`.

## Technical satisfaction algebra

| Supplied status | Projection |
|---|---|
| `proved` | `satisfied` (`S`) |
| `not_proved` | `not_satisfied` (`N`) |
| `unresolved` with either reason | `unresolved` (`U`) |

For two members, the complete strong-Kleene tables are:

| A | B | All | Any / alternative branches |
|---|---|---|---|
| S | S | S | S |
| S | N | N | S |
| S | U | U | S |
| N | S | N | S |
| N | N | N | N |
| N | U | N | U |
| U | S | U | S |
| U | N | N | U |
| U | U | U | U |

Fold recursively in source order. Inherited direct requirements use `All`. Evaluate **every** child and retain all requirement-tree traces even when the aggregate is already determined. A definition-only rule stays explicitly definition-only and does not become vacuously satisfied. An executable rule is S if any branch is S, otherwise U if any branch is U, otherwise N.

An exception guard is evaluated only after ordinary branch requirements are S. Its registered target's final S/N/U is the guard's S/N/U, using the identical complete status binding map, reference date, policy and validated graph. Evaluate all guards in declaration order. Every S guard fires and defeats the branch to N; any S dominates U while the U guard and dependency trace remain visible. With no S, any U makes the branch U; all N leaves it S. A failed ordinary requirement and an exception defeat have distinct reasons. Missing targets, cycles and unsupported guards reject; they do not yield U.

Only final-S **root** branches support penalty candidates. N, defeated and U branches select none. A penalty guard reads its existing evaluated leaf trace: S selects, N skips as `guard_not_satisfied`, and U skips as `guard_unresolved`. An `Any` may make a branch S while a different guarded leaf is U, so this skip is reachable. There is no binding reevaluation during selection. Ancestor inheritance, sibling isolation, selected-ID deduplication, ordered supports and path-specific non-fatal `KSEL001` are unchanged. Dependency-target penalties are not automatically selected. Term trees never affect status, guards or selection.

## Result, order and assurance

The sixth closed result uses `satisfied|not_satisfied|unresolved` for root, rules, branches, requirement traces, target/guard traces and selection traces. Each evaluated rule adds source-ordered `proof_observations` for every leaf occurrence: rule/branch/path/leaf IDs, original supplied status and reason, separate satisfaction projection, complete `status_source`, burden/standard check (`matched|not_declared`) and optional descriptive provenance. Branch reasons distinguish requirements not satisfied, requirements unresolved, exception defeat and exception unresolved. Selection traces distinguish guard not satisfied, guard unresolved and branch-level skips. The selected record alone carries its validated canonical term. Mapping-key sorting does not reorder branch, exception, observation, support, term-child or selection lists.

The [PS01–PS72 synthetic cases](../../rewrite/haskell/test/proof-fixtures/CASES.json) and [proof-neutral vectors](../../rewrite/haskell/test/proof-fixtures/PROOF-VECTORS.json) cover supplied constructors and reasons, all pairwise tables, requirement edges, dependency propagation, term association, rejection classes, trace order and canonical responses. They test this declared technical algebra on validated closed inputs. They do **not** prove Haskell/reference correspondence, evidence sufficiency, doctrinal correctness or legal outcomes. No theorem prover has been run for this fragment, and proof-tool selection remains open.

`PresumptionRules-v1` needs a separately reviewed applicable derivation graph, authority/source references and burden-shift rules. Rebutting one presumption does not prove the opposite proposition; another route could still establish it. Legacy `@presumed`, exception `rebuts` and case-law burden-shift fields are migration evidence, not executable sixth-fragment states. The [migration contract](MIGRATION-CONTRACT.md) records intentional differences from Python and Lean.
