# Core Yuho Mechanisation v0.1

Status: machine-checked finite semantics for the documented technical-status fragment. This report does not claim that the complete compiler, parser, legal corpus, diagrams or legal interpretations are verified.

## Mechanised boundary

The Lean 4 namespace `Yuho.CoreYuho` is the formal counterpart of `Yuho.CoreYuho.Semantics`. It uses the repository-pinned Lean 4.10.0 toolchain. The definitions are in:

- [`Syntax.lean`](../../mechanisation/Yuho/CoreYuho/Syntax.lean): `Status`, finite requirement and definition syntax, scoped keys and exception instances, candidate branches, presumption states, allegations and half-open temporal intervals;
- [`Semantics.lean`](../../mechanisation/Yuho/CoreYuho/Semantics.lean): three-valued operations, structurally recursive requirement evaluation, ordered finite definition evaluation, exception defeat, scoped lookup, presumption derivation, pointwise case evaluation and temporal selection;
- [`Theorems.lean`](../../mechanisation/Yuho/CoreYuho/Theorems.lean): the proofs listed in the theorem registry;
- [`Conformance.lean`](../../mechanisation/Yuho/CoreYuho/Conformance.lean): the independent evaluator for retained cross-language vectors.

`Status` has exactly `satisfied`, `notSatisfied` and `unresolved`. `allStatus` and `anyStatus` use the truth tables in the Core language report, including satisfied and not-satisfied empty-list identities. A primitive environment is a finite-name lookup. The total evaluator models a checked program whose primitive inputs are complete; the optional evaluator represents a missing-input refusal.

A definition graph is an ordered finite list with an explicit `orderedAcyclic` predicate: each derived dependency must already be available and declaration identities cannot repeat in the available prefix. Its evaluator is structurally recursive over that list. Normalized participation, attempt and candidate-penalty guards use the same requirement and candidate-branch operations; the mechanisation does not duplicate their surface declarations.

An exception instance carries one `(actor, role, context, instance)` key. Its guard receives only the environment at that key. Cases are lists of allegation-local evaluations and have no aggregate result constructor. Temporal containment is exactly `effectiveFrom <= date` and, for a closed upper bound, `date < effectiveTo`; module versions and `supersedes` are record fields that containment does not inspect.

Filesystem module lookup, `.yh` parsing, source locations, Haskell checker implementation, SVG layout, narrative evidence, legal-source authority and Singapore-law correctness remain outside this mechanised core.

## Theorem inventory

The machine-readable inventory is [`core-yuho-theorems-v0.1.json`](../../mechanisation/core-yuho-theorems-v0.1.json). Its `mechanically_proved` rows are checked against real compiled declarations by [`TheoremRegistry.lean`](../../mechanisation/Yuho/CoreYuho/TheoremRegistry.lean) and `scripts/verify_core_yuho_theorems.py`.

The main theorem groups are:

| Group | Principal declarations | Result |
|---|---|---|
| Three-valued algebra | `andStatus_comm`, `orStatus_comm`, `andStatus_assoc`, `orStatus_assoc`, `andStatus_idempotent`, `orStatus_idempotent` | Commutativity, associativity and idempotence. |
| Finite groups | `allStatus_empty`, `anyStatus_empty`, `allStatus_notSatisfied_domination`, `anyStatus_satisfied_domination`, `allStatus_unresolved_exact`, `anyStatus_unresolved_exact`, `allStatus_permutation_invariant`, `anyStatus_permutation_invariant` | Identities, domination, exact unresolved propagation and permutation invariance. |
| Requirement and definitions | `requirement_evaluator_total`, `requirement_dependency_locality`, `requirement_lookup_stability`, `finite_definition_evaluator_total`, `finite_definition_evaluation_deterministic` | Total finite evaluation for complete inputs, determinism and transitive-input locality. Termination follows from accepted structural recursion. |
| Exceptions | `exception_defeat_table`, `exception_instance_isolation`, `candidate_branch_exception_isolation`, `nonselected_branch_cannot_transfer` | Exact defeat table and selected actor/context/instance noninterference. |
| Presumptions | `presumption_result_total`, `presumption_state_exactly_one`, `presumption_separate_from_offence` | One deterministic state among active, inactive, rebutted and unresolved, without constructing an offence result. |
| Cases | `allegation_equals_independent_evaluation`, `allegation_private_input_isolation`, `case_reordering_preserves_results`, `case_has_no_aggregate_status` | Pointwise evaluation, private-input isolation and presentation-order-only permutation. |
| Time | `temporal_success_unique`, `temporal_boundary_half_open`, `temporal_version_metadata_irrelevant`, `temporal_gap_has_no_success`, `temporal_overlap_has_no_success` | Unique successful relation, exact boundaries, metadata irrelevance and rejection of zero/multiple matches. |

No theorem contains `sorry`, `admit`, a project axiom or a placeholder declaration. `Audit.lean` runs `#print axioms` for principal theorems. Group permutation and temporal uniqueness report no axioms. Proofs using function/list extensionality or simplification report Lean's standard `propext` and `Quot.sound`; no project-specific or unsound axiom is declared. The Lean kernel and elaborator remain trusted.

## Independent Haskell–Lean conformance

[`core-yuho-v0.1.json`](../../mechanisation/conformance/core-yuho-v0.1.json) uses schema `yuho.core-conformance-v0.1`. It retains 95 input vectors:

- 20 binary/empty `all` and `any` truth-table vectors;
- 8 representative branch/guard aggregates;
- all 27 assignments of `all(a, any(b,c))`;
- 6 normalized definition chain/diamond or checked-fixture projections;
- 10 exception combinations;
- all 9 presumption trigger/rebuttal assignments;
- 4 actor/instance/input isolation vectors;
- 3 independent multi-allegation cases;
- 8 temporal boundary, gap, overlap and metadata vectors.

The Haskell executable decodes the JSON fail-closed and evaluates it through `Yuho.CoreYuho.Semantics`. Lean receives the same inputs through generated [`GeneratedVectors.lean`](../../mechanisation/Yuho/CoreYuho/GeneratedVectors.lean) and independently evaluates them with `Yuho.CoreYuho.Conformance`. The generator contains inputs only—never expected results. The orchestrator compares canonical result bytes and retained Haskell and Lean outputs.

The generator/orchestrator and JSON-to-Lean serialization are part of the test trust boundary: a bug could omit or alter a vector. They cannot make unequal evaluator outputs compare equal without also compromising the byte comparison. Representative `origin` labels connect vectors to checked research fixtures, but do not bring those fixtures' legal interpretation into the theorem claim.

Run the entire boundary from the repository root:

```sh
make verify-core-yuho-conformance
```

The underlying exact commands are:

```sh
cd mechanisation && lake build && lake build Tests
python3 scripts/verify_core_yuho_theorems.py
python3 scripts/verify_core_yuho_conformance.py
cd mechanisation && lake env lean Yuho/CoreYuho/Audit.lean
```

## Trusted computing base and claim boundary

Mechanically checked:

- the finite definitions and theorems elaborated by Lean 4.10.0;
- the theorem registry's resolution to declarations in the Lean build.

Independently tested, not proved:

- agreement of the Haskell and Lean evaluators on the 95 retained vectors;
- normalization of representative checked `.yh` fixtures into the tested Core shapes;
- established Haskell kernel and historical-byte regressions.

Trusted:

- the Lean kernel, compiler and standard library;
- GHC and the Haskell implementation;
- the vector enumerator, JSON decoder/encoder, JSON-to-Lean serialization and byte-comparison orchestrator;
- the operating system and build tools.

Unverified or deferred:

- parser/checker correctness and a surface-to-Core type-preservation proof;
- a general Core-to-KernelInput refinement theorem;
- filesystem module resolution, frontend temporal resolution and source-location preservation;
- semantic-diagram completeness or layout correctness;
- legal-source fidelity, legal interpretation, evidence assessment and factual truth;
- any claim of guilt, liability, conviction, acquittal or sentence.

The justified public claim is: **Core Yuho v0.1 has machine-checked finite semantics for its documented technical-status fragment, with independent bounded conformance testing against the authoritative Haskell implementation.**
