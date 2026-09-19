# Yuho Lean mechanisation

This Lean 4.10.0 project machine-checks the documented finite Core Yuho semantic fragment. Build it with:

```sh
lake build
```

`Yuho/CoreYuho/` contains the current base, typed-finite and release definitions, theorems, conformance evaluators, registries and axiom audits. The cumulative machine-readable theorem registries contain 79 declarations. `conformance/` retains three independent Haskell/Lean input and result corpora with 95, 2,518 and 33 vectors.

From the repository root, run:

```sh
python3 scripts/verify_core_yuho_theorems.py
python3 scripts/verify_core_yuho_conformance.py
python3 scripts/verify_core_yuho_typed_finite_conformance.py
python3 scripts/verify_core_yuho_v03_conformance.py
```

The machine-checked boundary does not include the Haskell parser/compiler, filesystem module resolution, diagrams, factual truth, legal interpretation, source currency or corpus correctness. See the public [mechanisation guide](../docs/mechanisation.md) and [assurance statement](../docs/assurance.md).
