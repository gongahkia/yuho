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
│   ├── Soundness.lean   (Lemmas 6.2, 6.4 + partial 6.1 composition)
│   ├── Graph.lean       (Lemma 6.3 element-graph correspondence, v2)
│   ├── Cross.lean       (Lemma 6.4' cross-section composition, v3)
│   ├── Penalty.lean     (Lemma 6.5 penalty correspondence + G8/G14, v4)
│   └── Generator.lean   (verified Z3-generator spec + canonical
│                         models — discharges the conviction-layer
│                         oracle assumption, v5)
└── Tests/
    └── Smoke.lean       (executable examples on s299-shaped fixtures)
```

## Build

```sh
cd mechanisation
elan default leanprover/lean4:v4.10.0   # one-time, if not pinned
lake build         # typechecks the Yuho lib (9 modules + theorems)
lake build Tests   # typechecks the smoke tests with native_decide
```

**Verified status as of 2026-04-28:** both `lake build` and
`lake build Tests` pass under Lean 4.10.0 with no `sorry`s and no
linter warnings.

## What's mechanised, with file pointers

| Paper claim | File | Theorem name | Proof technique |
|---|---|---|---|
| Lemma 6.2 element correspondence | `Yuho/Soundness.lean` | `element_correspondence` | `rfl` after unfolding `Element.eval` and `SMTModel.facts` |
| Lemma 6.3 element-graph correspondence | `Yuho/Graph.lean` | `element_graph_correspondence` | Well-founded recursion on `sizeOf g` + list-folding sub-lemmas |
| Lemma 6.4 exception correspondence | `Yuho/Soundness.lean` | `exception_correspondence` | Projection from the `SMTModel.satisfies` triple |
| Lemma 6.4' cross-section composition | `Yuho/Cross.lean` | `cross_section_correspondence` + `is_infringed_correspondence` + `apply_scope_correspondence` | Field projection + `find?`-monotonicity |
| Lemma 6.5 penalty correspondence (incl. G8/G14) | `Yuho/Penalty.lean` | `penalty_correspondence` | Structural induction on `Penalty` with leaf + combinator cases |
| Conviction-layer oracle discharge (v5) | `Yuho/Generator.lean` | `canonical_smt_satisfies` + `canonical_graph_satisfies` | Direct construction; both `rfl`-style after unfold + finite induction on element-list |
| Unconditional Lemma 6.2 / 6.3 / 6.4 (no oracle) | `Yuho/Generator.lean` | `element_correspondence_unconditional` etc. | Application of canonical-satisfies to the original lemmas |
| Penalty well-formedness (v6) | `Yuho/Penalty.lean` | `Penalty.wellFormed` + `PenaltySMTModel.satisfiesWF` | Bool-valued recursive predicate; mechanises the linter's sentinel-propagation + non-empty-`orBoth` invariant |
| Penalty-layer oracle discharge (v6) | `Yuho/Generator.lean` | `canonical_penalty_satisfies` + `canonical_penalty_satisfies_wf` + `penalty_correspondence_unconditional` | Footprint as input parameter; leaf-shape canonical constructors auto-discharge witness |
| Cross-section qualified-atom refactor (v6) | `Yuho/Cross.lean` | `CrossSMTModel.satisfies` (refactored) + `Generator.canonicalCrossModel` + `canonical_cross_satisfies_singleton_singleton_exc` | `excFires` re-keyed on `<sX>_exc_<label>_fires`; singleton-module discharge kernel-checked |
| Cross-section multi-statute discharge (v7) | `Yuho/Cross.lean` | `canonical_cross_satisfies` | Structural induction over `mod.statutes` under qualified-atom-name + section-number uniqueness invariants (linter-enforced) |

## Trusted base

This artefact is **not** axiom-free. The trusted base consists of:

1. **Lean 4.10's kernel** (the `lean-toolchain` pin).
2. **No additional axioms** beyond what Lean's stdlib uses
   (Choice, propositional extensionality, quotient types).
3. **Residual oracle scope (post-v7):** A single item.
   - The claim that the Python `Z3Generator`
     (`src/yuho/verify/z3_solver.py`) emits exactly the
     biconditional shape `Generator.encodeStatute` specifies.
     This is now **narrower** than the prior oracle assumption:
     the Lean spec is the verified target, and
     `make verify-bulk-contrast` exercises the Python generator
     against the operational evaluator on every encoded statute
     as a differential check. Tightening this to a structural
     diff against the Lean spec is the residual gap.

What v5 changed: the prior trust assumption — "*some* SMTModel
satisfies the bicond bundle" — has been **discharged** for the
conviction layer. `Yuho/Generator.lean` exhibits constructive
`canonicalSMTModel` and `canonicalGraphModel`, proves they
satisfy the bundle on every fact pattern, and exports the
unconditional forms of Lemmas 6.2 / 6.3 / 6.4 as application
corollaries.

What v6 changed: extended the discharge to the §6.5 penalty
layer (via `Generator.canonicalPenaltyModel` +
`Penalty.wellFormed`) and the single-statute case of the
cross-section bundle (via `Generator.canonicalCrossModel`
with qualified-atom-name `excFires`). The §6.5 leaf-shape
canonical footprint constructors auto-discharge the witness
on the leaf cases; the `cumulative` / `orBoth` cases take a
user-supplied footprint with admittance proof. The
cross-section refactor fixes a v3 raw-label collision: two
statutes with a shared exception label (e.g. both s299 and
s300 carrying a `consent` exception) now route to distinct
qualified atoms `299_exc_consent_fires` /
`300_exc_consent_fires`, matching what `Z3Generator` already
emits in `src/yuho/verify/z3_solver.py`.

What v7 changed: lifted the cross-section discharge from the
singleton-module case to arbitrary `mod.statutes` via
structural induction. `canonical_cross_satisfies` takes the
linter-enforced qualified-atom-name uniqueness invariant and
section-number uniqueness invariant as explicit hypotheses,
and discharges the bundle constructively. Smoke tests in
`Tests/Smoke.lean` exhibit the discharge on a two-statute
fixture (`s299WithConsent + s378NoExc`). With v7, the
abstract module-level oracle is no longer a residual: every
linter-clean module produces a satisfying assignment by
construction.

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
