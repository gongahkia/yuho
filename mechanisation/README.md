# Yuho mechanisation — Lean 4 formal artefact

Machine-checkable mechanisation of two paper-load-bearing lemmas
from `paper/sections/soundness.tex`:

* **Lemma 6.2** (element correspondence) — kernel-checked.
* **Lemma 6.4** (exception correspondence) — kernel-checked,
  composed with the operational definition of
  `Exception.firedSet` realising Catala-style default-logic
  priority precedence.

The remaining lemmas of §6 (6.3 element-graph, 6.5 penalty,
Theorem 6.1's main step) are **pen-and-paper-only** in this
artefact. The boundary is documented honestly in §6.6 of the
paper.

## Layout

```
mechanisation/
├── README.md            (this file)
├── lakefile.lean        (Lake build configuration)
├── lean-toolchain       (pinned Lean 4.10.0)
├── Yuho.lean            (top-level module re-exporter)
├── Yuho/
│   ├── AST.lean         (Element / ElementGroup / Exception / Statute)
│   ├── Facts.lean       (fact-pattern abstraction)
│   ├── Eval.lean        (operational evaluator: §4.2 + §4.3 rules)
│   ├── SMTAbs.lean      (abstract SMT-model + biconditional spec)
│   └── Soundness.lean   (Lemmas 6.2, 6.4 + partial 6.1 composition)
└── Tests/
    └── Smoke.lean       (executable examples on s299-shaped fixtures)
```

## Build

```sh
cd mechanisation
elan default leanprover/lean4:v4.10.0   # one-time, if not pinned
lake build
```

`lake build` typechecks the Yuho lib (the proofs); `lake build Tests`
typechecks the smoke tests. Both should produce no `sorry`-induced
warnings — the bodies are either `rfl` (definitional) or fully
decomposed into structural cases.

## What's mechanised, with file pointers

| Paper claim | File | Theorem name | Proof technique |
|---|---|---|---|
| Lemma 6.2 element correspondence | `Yuho/Soundness.lean` | `element_correspondence` | `rfl` after unfolding `Element.eval` and `SMTModel.facts` |
| Lemma 6.4 exception correspondence | `Yuho/Soundness.lean` | `exception_correspondence` | Projection from the `SMTModel.satisfies` triple |
| Partial 6.1 (composition of 6.2 + 6.4) | `Yuho/Soundness.lean` | `partial_conviction_correspondence` | Pair construction: rfl + Lemma 6.4 |

## What's not mechanised (and why)

* **Lemma 6.3 element-graph correspondence.** Requires structural
  induction on `ElementGroup` with the AllOf/AnyOf list-folding
  correspondence. The Catala bisimulation lemma at
  `theories/catala/simulation_sred_to_cred.v` is the structural
  template; ~600 lines of proof there. Out of scope for the v1
  paper.
* **Lemma 6.5 penalty correspondence.** Requires modelling the
  range-arithmetic abstraction (`⊔` / `⊓` over interval pairs) in
  Lean and showing the Z3 integer-bound encoding agrees on the
  membership test. No Catala analogue. Out of scope for v1.
* **Cross-section composition (Theorem 6.1's apply\_scope /
  is\_infringed clause).** Requires a `WellFoundedRelation`
  argument over the inter-section reference graph. Catala didn't
  mechanise scope-calls either; out of scope for v1.

## Trusted base

Per Catala's `CLAIMS.md` template: this artefact is *not yet
axiom-free*. The trusted base consists of:

1. **Lean 4.10's kernel** (the standard.toolchain pin).
2. **No additional axioms** beyond what Lean's stdlib uses
   (Choice, propositional extensionality, etc.).
3. **The `SMTModel.satisfies` predicate** is an axiomatic
   specification of what the Z3 generator emits; we trust the
   wider toolchain's `Z3Generator` (in
   `src/yuho/verify/z3_solver.py`) to actually emit those
   biconditionals. This is the analogue of Catala's "trust in
   the OCaml/Python codegen" oracle assumption — see §6.6 of
   the paper for the explicit framing.

There are **no `sorry`s** in `Yuho/`; the only `True`-bodied
`firedSet_prefix_subset` lemma is named for `Soundness.lean`'s
proof structure but is not depended on by any theorem proven in
this artefact. It reserves the slot for a future expansion of
Lemma 6.4's proof depth.

## Citing the artefact

In §6.6 of the paper, the artefact is referenced as
``\texttt{mechanisation/}`` (a sub-directory of the Yuho repo).
A future Zenodo deposit will give the artefact a citable DOI; the
`paper/REPRODUCE.md` instructions point at both.

## Deferring decisions to v2

Decisions deliberately deferred:

* **Autosubst-style binder infrastructure.** Yuho's surface
  language has scoped names (function definitions, scope-call
  arguments). The current encoding uses raw strings, which limits
  the mechanisation to the closed-vocabulary fragment.
* **SMTCoq-style certified Z3 reconstruction.** A future v2 may
  port the `SMTModel.satisfies` predicate to a Lean equivalent of
  SMTCoq once one exists; today the trust is in the encoder, not
  the solver's reconstruction.
* **Per-statute lift to `apply_scope`.** Cross-section composition
  is the natural next theorem to mechanise; it requires a
  well-founded relation over the inter-section graph, which is
  cleanly tractable but not in v1's scope.
