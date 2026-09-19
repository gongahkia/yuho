# Core Yuho Mechanisation v0.2

Core Yuho v0.2 extends the retained v0.1 mechanisation with finite nominal typing, scalar comparison, explicit three-valued negation, finite quantification, cardinality intervals and explicit rule priority. The implementation is in [`TypedFinite.lean`](../../mechanisation/Yuho/CoreYuho/TypedFinite.lean); it imports the v0.1 three-valued operations rather than defining a second truth algebra.

This is a machine-checked finite semantic model, not an end-to-end proof of the parser, compiler, kernel, diagrams or Singapore-law corpus.

## Executable formal fragment

The Lean namespace `Yuho.CoreYuho.TypedFinite` contains:

- six ordered comparison operators and typed integer, date-ordinal, finite-enum and exact-money values;
- an explicit unresolved scalar value;
- `negateStatus`, `finiteForall` and `finiteExists` over the v0.1 `Status` domain;
- nominal `TypedTerm`, fixed-arity `PredicateSignature` and `PredicateApplication` structures;
- capture-free typed term/application substitution;
- interval-based `atLeast`, `atMost` and `exactly` cardinality;
- establish/defeat rule observations, explicit priority edges, bounded transitive reachability and finite proposition resolution.

The formal model intentionally excludes UTF-8 parsing, source locations, filesystem module loading, JSON/SVG layout, legal sources, narrative evidence and legal interpretation.

The Lean comparison function is total over its raw constructor domain: mismatched scalar constructors, enum types or money currencies return `unresolved`. This is not an accepted surface meaning. The Haskell checker and kernel reject those ill-typed combinations, and the Haskell–Lean comparison claim is restricted to well-typed inputs. Date half-open membership is checked in Haskell as the documented composition of `>=`, `<` and three-valued `all`; it is covered by surface and protocol fixtures but is not a separate Lean comparison constructor in v0.2.

## Theorem inventory

[`core-yuho-theorems-v0.2.json`](../../mechanisation/core-yuho-theorems-v0.2.json) registers 25 mechanically proved properties. [`TypedFiniteTheoremRegistry.lean`](../../mechanisation/Yuho/CoreYuho/TypedFiniteTheoremRegistry.lean) names every registered declaration and is compiled by `scripts/verify_core_yuho_theorems.py`.

| Group | Principal theorems |
|---|---|
| Comparisons | `comparison_deterministic`, `comparison_total` |
| Negation | `negation_involution` |
| Quantification | `forall_deterministic`, `exists_deterministic`, `forall_expansion_agrees`, `exists_expansion_agrees`, `forall_permutation_invariant`, `exists_permutation_invariant` |
| Typed substitution | `substitution_preserves_well_typed_application` |
| Cardinality | `countStatus_permutation_invariant`, `cardinality_permutation_invariant`, `cardinality_deterministic`, `cardinality_total`, `cardinality_mutually_exclusive`, `atLeast_satisfied_boundary`, `atMost_satisfied_boundary` |
| Priority | `priority_resolution_deterministic`, `acyclic_priority_graph_resolution_deterministic`, `higher_satisfied_defeat_wins`, `unresolved_higher_blocks_lower`, `incomparable_satisfied_conflict`, `unrelated_proposition_is_irrelevant` |
| Isolation retained from v0.1 | `exception_instance_isolation`, `allegation_private_input_isolation` |

Determinism and totality theorems state that the executable Lean functions return a unique constructor for each finite input. Termination follows from Lean-accepted structural recursion and the explicit fuel bound in priority reachability. The general priority-graph determinism theorem assumes the documented acyclicity predicate; semantic outcome lemmas currently cover the exact two-rule conflict cases. Full arbitrary-graph semantic characterization beyond determinism is boundedly conformance-tested, not universally proved.

`TypedFiniteAudit.lean` prints the axioms of representative theorems. No Core Yuho v0.2 source contains `sorry`, `admit`, a project axiom or a skipped theorem. Lean may report standard logical implementation axioms such as `propext` or `Quot.sound` for library extensionality/simplification proofs; those are part of Lean's standard trusted basis, not Yuho assumptions.

## Independent Haskell–Lean conformance

[`core-yuho-v0.2.json`](../../mechanisation/conformance/core-yuho-v0.2.json) is retained under schema `yuho.core-conformance-v0.2`. It contains 2,518 input-only vectors:

- all status assignments to `forall` and `exists` domains of size 0–4;
- `at-least`, `at-most` and `exactly` for every such assignment and thresholds 0–5;
- integer comparison matrices plus representative date, enum, money and unresolved operands;
- ordered and incomparable rule pairs;
- complete priority chains, diamonds, unresolved-higher and conflict graphs;
- typed substitutions;
- selected-key actor and allegation isolation.

The Python orchestrator enumerates and serializes inputs but computes no expected semantic result. Haskell decodes the retained JSON and evaluates it with `Yuho.CoreYuho.TypedFinite`; Lean receives the same input constructors through generated `GeneratedTypedFiniteVectors.lean` and evaluates them with `TypedFiniteConformance.lean`. Canonical result bytes must match. Unknown schema or vector kinds fail closed.

Run both retained boundaries and both theorem registries with:

```sh
make verify-core-yuho-conformance
```

The exact v0.2 command is:

```sh
PATH="$HOME/.ghcup/bin:$HOME/.elan/bin:/usr/bin:/bin" \
  python3 scripts/verify_core_yuho_typed_finite_conformance.py
```

At the revision introducing v0.2, the retained v0.2 input SHA-256 is `caf3a961760539aa1bbdafb76bb7b2c084b04ebf2c3617c27703d8c8cc54eed5`; both evaluator result files have SHA-256 `bc91ed000aa184379f865c745fbebe1a2f23ca3574849acaf937674d9157cca1`.

## Trusted computing base

Trusted components are the Lean 4.10.0 kernel, elaborator and standard library; GHC 9.8.4 and the authoritative Haskell implementation; Cabal/Lake and the operating system; the input enumerator, JSON decoders/encoders and JSON-to-Lean serializer; and the byte-comparison orchestrator. A defect in the enumerator can omit a case, but it does not provide expected results to either evaluator.

Mechanically proved:

- the registered finite Lean definitions and theorem statements above;
- resolution of every `mechanically_proved` registry entry to a compiled declaration.

Boundedly tested:

- Haskell–Lean agreement on all 2,518 v0.2 vectors and the retained 95 v0.1 vectors;
- surface parsing/checking/lowering for the typed fixtures;
- full finite priority chain/diamond behavior;
- protocol rejection, explanations and deterministic diagrams.

Not verified:

- a general surface-to-Core type-preservation theorem;
- a universal Haskell-to-Lean refinement theorem;
- parser, module filesystem resolver, kernel decoder or SVG layout correctness;
- completeness or legal correctness of any Singapore-law model;
- evidence quality, factual truth, legal applicability or judicial outcomes.

The justified claim is: **Core Yuho v0.2 has machine-checked semantics for its documented finite typed-status operations, with independent bounded Haskell–Lean conformance testing.**
