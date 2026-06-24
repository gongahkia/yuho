# Yuho mechanisation — Lean 4 formal artefact

Machine-checkable Lean 4 mechanisation of Yuho's soundness
correspondence. The v9 artefact covers element, element-graph,
exception, cross-section, and penalty correspondence, plus
generator/canonical-model lemmas and cross-reference/apply-scope smoke
theorems. It builds with 0 `sorry`s under the pinned Lean 4.10.0
toolchain.

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
│   ├── CaseLaw.lean     (executable case-law effect fragment)
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
lake build         # typechecks the Yuho lib modules + theorems
lake build Tests   # typechecks the smoke tests with native_decide
```

**Verified status as of 2026-04-28:** both `lake build` and
`lake build Tests` pass under Lean 4.10.0 with no `sorry`s and no
linter warnings.

## Claim boundary

| Category | Current Yuho claim | Evidence | Boundary |
|---|---|---|---|
| Proved | Element, element-graph, exception, cross-section, and penalty correspondence for the Lean-modeled fragment. | `lake build`, `lake build Tests`, theorem rows below. | Applies to the abstractions encoded in `mechanisation/Yuho/*.lean`, not every parser construct. |
| Tested | Python `Z3Generator` shape matches Lean-side fixtures for retained smoke/full-corpus structural checks. | `make verify-structural-diff`, `make verify-structural-diff-full` when run. | Differential evidence, not a certified compiler proof. |
| Trusted | Lean 4.10 kernel, stdlib axioms, Python AST/Z3 encoder, fixture generator, and corpus selection. | `lean-toolchain`, `scripts/verify_structural_diff.py`, `mechanisation/scripts/generate_fixtures.py`. | Bugs in these layers can invalidate conclusions. |
| Out of scope | Open-textured terms, full precedent-sensitive interpretation, procedural burdens beyond executable metadata guards, rich evidential provenance beyond typed burden metadata, and certified Z3 proof reconstruction. | Listed again under deferred decisions. | These are not proved by the current mechanisation. |

## What's mechanised, with file pointers

| Mechanised claim | File | Theorem name | Proof technique |
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
| Cross-section-reference acyclicity (v8) | `Yuho/Cross.lean` | `CrossRefGraph.acyclic` + `acyclic_canonical_cross_satisfies` | Decidable Bool predicate via `reachableIn` fuel ceiling = `nodes.length`; v4 satisfies bundle re-discharged under the linter-enforced acyclicity hypothesis |
| Deep element-tree base camp (v9) | `Yuho/CrossDeep.lean` | `ElementDeep` AST + `ElementDeep.eval` (fuel-bounded) + `ElementGroup.toDeep` lift + `Statute.deepBody_compat` | Conservative-extension lemma: the v9 deep evaluator agrees with v4–v8 `Statute.elementsSatisfied` on the existing `crossRef`-free surface library at every fuel budget; mutual induction over `ElementGroup` / `List ElementGroup` |
| `applyScope` lift + cross-ref semantics smoke (v9) | `Yuho/CrossDeep.lean` | `ElementDeep.applyScope` constructor + `eval_crossRef_resolves` / `eval_applyScope_resolves` / `_missing` / `_zero_fuel` (six theorems) | Each branch of the `crossRef` / `applyScope` evaluator is pinned to its inference rule (`is_infringed(n)` → ambient-facts `Statute.convicts`; `apply_scope(n, F')` → substituted-facts `Statute.convicts`; out-of-module → `false`; fuel-exhaustion → `false`) by `simp only` after a `sigma`-lookup hypothesis |
| Typed fact burden metadata guard | `Yuho/Facts.lean`, `Yuho/Eval.lean` | `TypedFact.truthWithBurden_untyped_true` + `false` + `matching` + `wrong_burden` + `wrong_standard`; `Element.evalTyped` | Direct computation over runtime-style typed fact metadata: legacy true facts remain true, false facts remain false, matching burden/proof-standard metadata is accepted, and mismatched supplied metadata is rejected; smoke tests cover element-level matching/mismatching/untyped facts |
| Case-law executable effect fragment | `Yuho/CaseLaw.lean` | `CaseEffectKind.requires_false` + `satisfies_true` + `excludes_true` + `fromSurface_*` + `applySurface_*` + `CaseFact.truthWithBurden_*` + `CaseEffect.effectiveFact_*jurisdiction*` + `CourtLevel.*_surface_rank` + `DoctrineRole.*_surface_rank` + `CasePrecedence.*` + `CaseAuthority.keepAfterEffectConflicts_no_bucket_conflict` + `resolveEffectConflicts_keeps_pair` + `materializeEffect_*` + `TreatmentKind.*_surface_*` + `CaseAuthority.resolvedEffectIn_*` lemmas | Direct computation over lower-case surface effect/treatment aliases, normalized effect-fact conflict buckets, same-kind same-fact non-conflict retention, surface court/role precedence ranking, the three runtime-supported effect operators, cumulative non-conflicting effects with declaration-order application, negative-treatment non-adoption, own-effect dominance over adoption, missing-target adoption skip, adopted-effect target remapping and fact/kind preservation, bounded positive-treatment-chain adoption with cycle cutoff and metadata merge, inactive-authority/adoption suppression, jurisdiction-gated burden-metadata guards, concrete precedence ranks, and same-fact conflict selection; smoke tests cover targeted `requires`, surface aliases/ranks, typed burden acceptance/rejection, normalized fact-key conflict selection, same-kind same-fact retention, cumulative non-conflicting effects with declaration-order sensitivity, precedence rank construction/tie-breaking, full-list conflict selection, negative-treatment non-adoption, own-effect dominance, missing-target adoption skip, adopted-effect target remapping and payload preservation, inactive-adopter suppression, transitive adopted effect transfer, cyclic adoption cutoff, adoption burden override, foreign-jurisdiction burden bypass, and overruled-source suppression |

## Trusted base

This artefact is **not** axiom-free. The trusted base consists of:

1. **Lean 4.10's kernel** (the `lean-toolchain` pin).
2. **No additional axioms** beyond what Lean's stdlib uses
   (Choice, propositional extensionality, quotient types).
3. **Residual oracle scope (post-v9):** A single item.
   - The claim that the Python `Z3Generator`
     (`src/yuho/verify/z3_solver.py`) emits exactly the
     biconditional shape `Generator.encodeStatute` specifies.
     This is now **narrower** than the prior oracle assumption:
     the Lean spec is the verified target, and
     `make verify-bulk-contrast` and
     `make verify-structural-diff-full` exercise the Python
     generator against the operational evaluator / Lean-side shape
     checks across the encoded library. A certified compiler proof
     from Python emission to Lean spec remains outside this artefact.

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
* **Richer doctrine and case-law semantics.** The current artefact
  mechanises typed-fact burden metadata guards, lower-case surface
  effect/treatment aliases, normalized effect-fact conflict buckets,
  same-kind same-fact non-conflict retention, surface court/role precedence
  ranking, the executable effect algebra, cumulative non-conflicting effects with
  declaration-order application, negative-treatment non-adoption, reversed-treatment
  inactivation, own-effect
  dominance over adoption, ordered positive-treatment adoption including `applied`,
  positive-treatment non-inactivation,
  missing-target and effectless-target adoption skip,
  adopted-effect target remapping and fact/kind preservation, and bounded positive treatment
  adoption with cycle cutoff and metadata override/fallback/merge,
  inactive-authority/adoption suppression, jurisdiction-gated burden-metadata guards,
  and concrete
  precedence-rank conflict selection,
  not the full precedent graph, open-textured legal terms, or procedural
  burdens.
