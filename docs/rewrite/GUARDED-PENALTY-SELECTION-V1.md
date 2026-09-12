# GuardedPenaltySelection-v1

**Status:** Implemented technical kernel fragment, 12 September 2026. This document specifies a closed `yuho.kernel-input/v1` and `yuho.kernel-result/v1` variant. It does not change Canonical IR v1.2 or its hashes.

## Scope and meaning

This fragment inherits [TypedBooleanFacts-v1](TYPED-BOOLEAN-FACTS-V1.md), including the validated acyclic registry, exact total Boolean leaf bindings, same-context registered exception targets, final branch status, source identity, traces and `KINV007` annotation checks. It adds **selection of statutory penalty declaration IDs** on final-true branches. A selected ID is an applicable *candidate declaration under these Boolean rules*. It is neither a statutory punishment term or range nor a sentence imposed by a court. It does not decide conviction, punishment, disposition or outcome. [Singapore Courts' charge guide](https://www.judiciary.gov.sg/criminal/representing-yourself-mentions-court/reading-charges) distinguishes prescribed ranges from the punishment chosen for a case; the [Chief Justice's 2022 sentencing address](https://www.judiciary.gov.sg/news-and-resources/news/news-details/chief-justice-sundaresh-menon-keynote-address-delivered-at-the-sentencing-conference-2022) describes judicial sentencing discretion. Both were accessed 12 September 2026 for terminology only; neither reviews Yuho's model.

No imprisonment, fine, caning, death, minimum, maximum, unit, currency, sentence combination, proof state, temporal applicability, jurisdictional selection, negation, arbitrary expression, environment, outcome substitution or fact override belongs to this fragment. Validated punishment payloads belong to a prospective `PenaltyTerms-v1`; their selection alone would still not sentence anyone.

## Closed request and validation

The request is the [fourth closed variant](../../rewrite/haskell/schema/request.schema.json). Every provision requires `penalties`, possibly `[]`. Each declaration has exactly `penalty_id`, `source_id`, `span`, and `guard`. Its zero-based array position is `declaration_index`; its containing provision supplies `declaring_provision_path`. `penalty_id` is a globally unique qualified semantic ID beginning `pen:`. The only guards are `{"kind":"unguarded"}` and `{"kind":"leaf_true","leaf_id":"f:example"}`. A `leaf_true` ID is exact and globally resolved to an executable leaf in the same rule and inherited branch requirements. No penalty term fields are accepted.

Decoding bounds the input line at 1,048,576 bytes, JSON depth at 64 and policy semantic IDs at 1–1,024. The fragment counts penalty declarations as semantic nodes. A second deterministic cap rejects more than **4,096 expanded branch/declaration occurrences across the complete registry** with `KDEC002`, before result construction. Fixed objects reject unknown and duplicate keys; recognized unsupported punishment terms and guard constructors reject with `KCAP001`. Existing source-byte, UTF-8, span, date, fact, ID and DAG checks run before selection. The entire registry is validated, including unreachable or false rules and target-rule penalties.

After typed and graph validation, each declaration's source must exist and match its declaring rule, and its span must lie inside the containing provision's span. Every guarded declaration must have at least one inheriting executable descendant, and its leaf must occur in the inherited requirement tree of **every** such descendant. Missing or out-of-scope guards reject with `KINV008`: a sibling, unrelated provision, dependency target, another rule or ambient value cannot supply the leaf. An unguarded declaration with no executable descendant is valid and inert. A guarded declaration with none rejects; universal quantification over an empty descendant set is not accepted. This strict scope rule asks model authors to place a conditional declaration at the lowest shared provision whose executable descendants all contain the guard.

Validation produces resolved declaration/branch uses before evaluation. Selection receives that validated index and an evaluated root trace; it never resolves raw names or reads a fact map again. The root and dependency targets share the identical typed bindings, Boolean projection, reference date, policy and validated DAG. A target's own penalty declarations are validated but never selected automatically for the requested root.

## Selection algebra

Only final-true root executable branches are eligible. For each declaration inherited on each such branch, an unguarded declaration selects. `leaf_true` selects exactly when its already evaluated leaf trace value is true. An expected leaf trace that is absent or duplicated is `KERR001`, an internal consistency failure, never a false guard. All eligible declarations accumulate; no first-match, priority, lexicographic winner or sentence arithmetic exists.

| Final branch state/reason | Guard observation | Selection trace result |
|---|---|---|
| `true` / `satisfied` | unguarded | `selected`, guard `not_evaluated` |
| `true` / `satisfied` | `leaf_true` trace `true` | `selected`, guard `true` |
| `true` / `satisfied` | `leaf_true` trace `false` | `guard_false`, guard `false` |
| `false` / `requirements_failed` | any | `branch_requirements_false`, guard `not_evaluated` |
| `false` / `defeated` | any | `branch_exception_defeated`, guard `not_evaluated` |
| `unresolved` / `guard_unresolved` | any | `branch_unresolved`, guard `not_evaluated` |

Unresolved skip is tested at a pure internal boundary. Total Boolean bindings and a validated closed DAG currently make unresolved unreachable from a valid wire request. An exception-defeated branch selects nothing even if its ordinary leaf traces are true. If one sibling is eligible and another is defeated, false or unresolved, only the eligible sibling contributes supports.

A declaration applies along its own provision ancestry. Ancestor declarations are inherited, sibling declarations are isolated, and direct and inherited declarations accumulate. Each selected `penalty_id` appears once, with **all** eligible supporting branch occurrences. Each support records its own `direct` or `inherited` origin. In the current executable-leaf branch construction, an ancestor with executable children is not itself a branch; one declaration being direct on one path and inherited on another is representable in the result but not presently reachable from a valid request.

`KSEL001` is a non-fatal warning exactly when at least two *selected guarded* declarations from the **same declaring provision** have distinct guard leaf IDs on one or more identical eligible branch paths. It reports every overlapping path, the penalty IDs in declaration order and distinct guard IDs in their first declaration order. Unguarded plus guarded, repeated same-guard declarations, different declaring provisions and selections on disjoint paths do not warn. The warning changes neither the technical root judgment nor the selected ID set. With global Boolean leaf IDs and strict scope, the disjoint-path condition is tested at the pure overlap boundary as well as stated here.

## Result and trace

The [fourth closed result variant](../../rewrite/haskell/schema/result.schema.json) retains the typed rule, branch, exception/dependency and fact-observation results. `selected_penalties` holds unique selected records with ID, source/span, declaring path, index, guard and ordered `supporting_branches` (`branch_id`, `path`, `origin`, `guard_result`). `penalty_selection_trace` has one occurrence for every declaration inherited by every root executable branch, including skipped cases, with branch ID/path, source/span, origin, final status/reason, guard result and closed outcome. No trace is fabricated for an absent declaration. `selection_warnings` holds structured `KSEL001` observations, separate from fatal diagnostics.

Selected records follow provision-tree declaration order; supports follow executable branch order; selection traces follow branch order and then ancestor-to-descendant declaration order; warnings follow declaring provision order. JSON mapping keys are canonically sorted but never control list order. A raw malformed JSON line may not reveal its fragment, so the pre-dispatch `KDEC001/002` rejection retains the existing generic result envelope; successfully decoded fourth-fragment rejections have the fourth envelope and empty selection arrays.

`KPROT001` covers protocol/version errors; `KDEC001/002` malformed or bounded decoding; `KINV001–008` facts, IDs, spans, model graph, metadata and penalty scope; `KCAP001` unsupported constructors or term payloads; `KERR001` internal evaluation inconsistency. Rejection carries no selected candidates or partial root judgment. Valid overlap uses `KSEL001` warning severity and stage `select_penalties`.

## Examples, migration and assurance

For a satisfied branch with true `f:rash`, both an unguarded `pen:base` and `leaf_true(f:rash)` declaration `pen:rash` select. If its exception target defeats the branch, neither selects; the trace says `branch_exception_defeated`. Two distinct true guards on the same branch keep both IDs and add `KSEL001`. A root declaration guarded by a leaf found only in one of two executable sibling paths is invalid `KINV008`, even if the other path is false.

The [GP01–GP49 synthetic cases and proof-neutral vectors](../../rewrite/haskell/test/penalty-fixtures/PROOF-VECTORS.json) exercise these rules. GP30–GP33 are **synthetic s304A migration probes**, never a reviewed representation of that provision. A [migration-only adapter](../../rewrite/haskell/test/penalty-fixtures/legacy_adapter.py) maps legacy path/index and guard names to explicit IDs and reports unmappable names or excluded term payloads.

Intentional Python divergences are exact leaf-ID lookup rather than normalized/ambient lookup; Boolean trace values rather than Python truthiness; missing guards as invariant rejection rather than false; source/tree ordering rather than lexicographic reconstruction; path-specific `KSEL001` rather than broad `YRTP001`; no outcome-target substitution or punishment payload; and stable IDs with explicit support paths. These are technical choices for this named fragment, not universally correct legal doctrine.

The proposed proof correspondence relates a future reference selector to the production evaluator **only after successful closed-input validation**: equal root branch status/reason and leaf traces imply equal selected-ID set, ordered supports, occurrence traces and overlap warnings under the stated order rules. The vectors are proof-neutral examples and rejection classifications, not a theorem, refinement proof, formal verification or legal review. Proof-tool selection remains open.
