# Core Yuho mechanisation

The [`mechanisation/`](../mechanisation/) tree is the current Lean 4.10.0 model of Core Yuho’s finite technical semantics. Internal `v0.1`, `v0.2`, and `v0.3` names identify cumulative schema and theorem boundaries used by reproducible checks.

## Theorem inventory

The three machine-readable registries contain 79 theorem declarations:

- 43 base theorems for three-valued groups, finite acyclic evaluation, dependency locality, exception/actor isolation, presumptions, independent cases and half-open temporal selection;
- 25 typed-finite theorems for exact comparisons, negation, typed substitution, quantifier expansion and permutation, cardinality, priority and isolation;
- 11 release theorems for normative applicability, explicit conflicts, absence of inference from missing norms, sanction bounds/shape and actor-attributed routes.

The precise names and source declarations are in [`core-yuho-theorems-v0.1.json`](../mechanisation/core-yuho-theorems-v0.1.json), [`v0.2`](../mechanisation/core-yuho-theorems-v0.2.json), and [`v0.3`](../mechanisation/core-yuho-theorems-v0.3.json). Registry verification fails when a mechanically proved property does not name a built theorem. Audit modules print axioms for the principal declarations. Project proofs contain no `sorry`, `admit`, or project axioms.

## Independent conformance

Three retained input corpora exercise 95, 2,518 and 33 vectors. The Haskell executable evaluates each input through `Yuho.CoreYuho.Semantics`; Lean evaluates the same semantic input through its own definitions. The orchestrators compare canonical result bytes and never calculate one expected result for both implementations.

```sh
(cd mechanisation && lake build)
python3 scripts/verify_core_yuho_theorems.py
python3 scripts/verify_core_yuho_conformance.py
python3 scripts/verify_core_yuho_typed_finite_conformance.py
python3 scripts/verify_core_yuho_v03_conformance.py
```

The versioned construct/conformance registries are retained under [`schema/`](../schema/). The corresponding inputs and Haskell/Lean results are under [`mechanisation/conformance/`](../mechanisation/conformance/).

## Trusted boundary and claims

The trusted computing base includes Lean and its kernel, GHC 9.8.4, the Haskell runtime and frozen dependencies, the vector decoders/generators, the byte-comparison orchestration and the host operating system/filesystem.

Machine checking covers the named finite definitions and theorems. Bounded conformance covers the retained vectors. Parsing, filesystem module resolution, source diagnostics, complete elaboration and lowering correctness, SVG layout, legal interpretation, factual truth, source authenticity and legal currency are not mechanically proved. See [Assurance](assurance.md) for the public claim boundary.
