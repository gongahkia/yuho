# RegisteredPresumptionDerivations-v1

This seventh closed `yuho.kernel-input/v1` and `yuho.kernel-result/v1` fragment derives **technical support for effective leaf satisfaction** from a finite registry of source-linked, rebuttable registrations. It inherits [SuppliedProofStatus-v1](SUPPLIED-PROOF-STATUS-V1.md), including complete status assignments, typed annotation checks, exceptions, penalty selection and validated penalty terms. Supplied `proved`, `not_proved` and reasoned `unresolved` classifications remain unchanged. A registration never supplies a new proof-status constructor.

The kernel does not assess evidence, authenticate a source or issuer, allocate or shift burdens, establish legal proof, apply a Singapore presumption, decide an outcome or sentence, or choose among penalty terms. A source hash checks bytes against the request, not legal authority. Multiple technical routes are not automatically independent legal grounds. This fragment is a synthetic, jurisdiction-neutral calculation; doctrine-specific registration requires separate legal review.

## Closed request and validation

The request is the sixth variant with fragment discriminator `RegisteredPresumptionDerivations-v1` and a required `presumptions` array, which may be empty. Each registration has exactly `presumption_id`, `target_leaf_id`, `source_id`, `span`, `trigger`, and `rebuttal`. `presumption_id` is unique across all semantic IDs in the request. Target and condition references are exact executable leaf IDs in the complete registry. `source_id` resolves to a hash-checked input source; the registration span is a valid UTF-8 byte/display span in it. All condition spans lie within their registration span and inherit its source. These links are descriptive provenance, not authenticated authority.

A condition has a required `kind` and `span`, plus exactly one of:

| Kind | Additional field | Technical meaning |
|---|---|---|
| `leaf_effective` | `leaf_id` | Read the referenced leaf's **effective** satisfaction. |
| `all_of` | `members` with at least two ordered children | False/not-satisfied if any child is N; otherwise U if any child is U; otherwise S. |
| `any_of` | `members` with at least two ordered children | S if any child is S; otherwise U if any child is U; otherwise N. |

Children are evaluated and traced in authored order even when an earlier child determines the result. A condition root is depth 1; maximum depth is 16. Every registration and condition node counts toward `policy.max_nodes` (1–1024). The existing 1,048,576-byte request, 64-container JSON-depth, source/span and 4,096 expanded penalty-occurrence limits continue to apply. All fixed objects reject unknown and duplicate keys. The complete rule, assignment, penalty, term and presumption registries are validated before evaluation, including unreachable registrations and false branches. Empty or singleton condition groups reject rather than normalize.

Recognized irrebuttable rules, burden shifts, direct-status predicates, negation and other unsupported condition constructors reject with `KCAP001`. A missing rebuttal is a malformed request, not an irrebuttable presumption. Arbitrary expressions, ambient lookup, normalized names, confidence thresholds, authority predicates and current-clock access are outside the wire contract.

For each registration with target `t`, the effective-leaf graph has edge `t → x` for **every** leaf `x` referenced in either condition. Self, two-node, longer and rebuttal-mediated cycles reject the whole model as `KINV006` with `graph_kind=effective_leaf`. Missing targets or condition leaves are `KINV005`. This graph is separate from the rule-level exception DAG: supplied classifications feed presumption resolution, which feeds rule evaluation, which feeds exceptions, then penalty selection and term association. No downstream result feeds a presumption condition. The closed graph is resolved before any root judgment; source order affects presentation, not effective values.

## Derivation and effective-satisfaction algebra

`S`, `N`, and `U` below mean `satisfied`, `not_satisfied`, and `unresolved`. Both trigger and rebuttal conditions are fully evaluated and traced for every registration.

| Trigger | Rebuttal | Route state |
|---|---|---|
| N | S, N or U | `inactive` |
| U | S | `rebutted` |
| U | N | `unresolved` |
| U | U | `unresolved` |
| S | S | `rebutted` |
| S | U | `unresolved` |
| S | N | `active` |

For a target leaf, direct S yields effective S. Otherwise any active route yields S. Otherwise direct U or any unresolved route yields U. Otherwise the result is N. Every route is evaluated, including when direct S already determines the target. Active routes are reported in that case without claiming they were necessary causes. Rebutted and inactive routes add neither positive nor negative support. A satisfied rebuttal removes only its own route; it does **not** prove the opposite proposition, erase direct proof or erase another route. If the trigger is N, its route is inactive even when the rebuttal is S, though both traces remain complete.

Registrations are not first-match rules and have no priority. Structurally identical registrations with distinct IDs remain distinct source-ordered routes. They are not deduplicated or warned about by the kernel; such duplicate modeling needs migration and legal review before doctrinal use. Reordering registrations may change result-array order, never the ID-indexed route states or effective satisfaction.

For example, if `f:target` is supplied `not_proved`, a trigger condition is S, and its rebuttal is N, the route is active and the **effective technical satisfaction** is S. The supplied status remains `not_proved`. If that route is later rebutted, the target falls back to direct N unless another active or unresolved route affects it. A second active route keeps effective S. None of these results asserts factual truth, legal proof or a legal burden outcome.

## Downstream behavior and result

Requirements use effective leaf satisfaction under the existing full-trace three-valued `All`/`Any` and alternative-branch rules. Registered exception targets use the same complete supplied statuses, effective map, date, policy and validated rule graph. All true exception guards still apply, true still dominates unresolved while unresolved traces remain visible, and branch-scoped defeat remains distinct from ordinary failure. Penalty guards read already evaluated effective leaf traces; only final-S root branches support selection. Unresolved guards skip with `guard_unresolved`. Validated penalty terms remain selection-inert.

The seventh result retains root/rule/branch, exception, selected-penalty, term and warning structures. Its source-ordered `presumption_derivations` includes **every** registration, even when the target rule is not evaluated. Each record gives registration ID, target ID, source/span, complete nested trigger and rebuttal traces and final values, route state, target direct projection and target effective satisfaction. Each evaluated leaf's ordered `proof_observations` retains the original supplied status and assignment source, and adds separate `direct_satisfaction`, `effective_satisfaction`, `active_presumption_ids`, and contributing `unresolved_presumption_ids`. The last list is populated only when direct N and an unresolved route make the effective result U; unresolved routes remain in `presumption_derivations` even when direct U already determines uncertainty. An active route may appear despite direct S. No `proof_status: presumed` or `proof_status: rebutted` is emitted.

Arrays preserve registry and authored child order; canonical JSON sorts object keys only. A rejection has `status=rejected`, one structured diagnostic and empty rules, derivations, selections, selection traces and warnings. Pre-dispatch malformed JSON uses the existing generic rejection envelope because its fragment may be unreadable.

| Code | Class |
|---|---|
| `KPROT001` | Protocol-version rejection. |
| `KDEC001/002` | Malformed shape/JSON or request-resource rejection under existing stream conventions. |
| `KINV002` | Duplicate or colliding presumption semantic ID. |
| `KINV003` | Source/span or condition-containment failure. |
| `KINV005` | Missing registration source, target or condition leaf. |
| `KINV006` | Complete effective-leaf graph cycle, with deterministic `graph_kind`. |
| `KCAP001` | Recognized unsupported presumption feature. |
| `KERR001` | Internal inconsistency after validation. |

The [RD cases](../../rewrite/haskell/test/presumption-fixtures/CASES.json), [manifest](../../rewrite/haskell/test/presumption-fixtures/MANIFEST.json), and [proof-neutral vectors](../../rewrite/haskell/test/presumption-fixtures/PROOF-VECTORS.json) specify synthetic examples, graph edges, input bindings, route states, trace structure and rejection classes. Tests and vectors establish bounded implementation behavior and determinism. They are not a proof of Haskell/reference correspondence, evidence sufficiency or legal correctness. The earlier six response variants retain their own wire bytes and semantics.

Legacy `@presumed`, exception `rebuts`/`undercuts`, case-law burden shifts and optional/Boolean runtime values do not automatically map to registrations. Migration must report missing target identity, authority review, ambiguous trigger or rebuttal conditions, duplicate-looking routes, loss of prose and unsupported burden effects. No real Singapore provision is a normative fixture for this fragment; the Singapore Courts-hosted *Jumaat* case brief is explanatory material, not the judicial opinion or an executable rule package. Jurisdiction-specific legal review, authenticated provenance, outcomes and sentencing are separate work.
