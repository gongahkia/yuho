/-
CrossDeep.lean — v9 mechanisation layer: lift cross-section
references into the element-tree leaf algebra.

Boundary statement (v8 → v9). v8 (`Cross.lean` lines 798–953)
mechanises the linter's `CrossRefGraph.acyclic` invariant as a
decidable Bool predicate, then proves
`acyclic_canonical_cross_satisfies` under the v4 abstraction in
which `Statute.elements` is a leaf-fact-only tree and
cross-section references only appear in exception guards. The
v8 acyclicity hypothesis is structurally explicit but does no
recursion-termination work yet — the v8 layer's `Element.eval`
never calls `Statute.convicts` recursively.

This v9 module ships a forward-looking extension: an augmented
element tree `ElementDeep` whose leaves include a `crossRef`
constructor, and an evaluator `ElementDeep.eval` whose
`crossRef` branch recursively consults `Statute.convicts` on
the referenced section. Termination is delivered via an
explicit `fuel : Nat` parameter — bounded above (in any sound
caller) by the number of statutes in the module, which is the
linter-enforced acyclicity ceiling on the cross-reference
graph's longest path.

Concretely, v9 ships:

1. `ElementDeep` — a four-constructor element tree
   (`fact` / `crossRef` / `allOf` / `anyOf`).

2. `ElementDeep.eval` — total `Bool` evaluator parameterised
   by section lookup `sigma : String → Option Statute` and
   `fuel : Nat`. The `crossRef` branch reduces to the v8
   `Statute.convicts` on the referenced section (which itself
   uses only leaf-fact `Element.eval`, so no further fuel is
   consumed by the v8-side call). When `fuel = 0` the
   `crossRef` branch returns `false` — sound under-
   approximation, the same default `Element.eval` applies to
   a missing fact via `Facts.empty`.

3. `ElementGroup.toDeep` — lift the v4–v8 `ElementGroup` into
   `ElementDeep` (always emits a `crossRefFree` tree because
   the surface library carries no cross-ref leaves in element
   trees today).

4. `Statute.deepBody_compat` — conservative-extension theorem:
   for any statute and any positive fuel, the v9 deep
   evaluator on `s.deepBody` agrees with the v4–v8
   `Statute.elementsSatisfied`. Establishes that the v9
   layer adds capacity without perturbing any existing v4–v8
   correctness claim.

The `Cross.lean` v9 follow-up note (lines 931-953) frames the
remaining work — well-founded recursion driven by the v8
acyclicity invariant, and a `crossRef`-bearing strengthening of
`acyclic_canonical_cross_satisfies`. This file ships the AST +
the conservative-extension bridge that v9 needs as its base camp.

This module is purely additive: it imports `AST` / `Facts` /
`Eval` only, and does not perturb the v4–v8 satisfies bundles
in `Cross.lean`.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval

namespace Yuho

/-! ## §6-cross-v9 layer 1 — Augmented element tree -/

/-- A "deep" element tree, extending `ElementGroup` with a
`crossRef` leaf carrying a section number. Surface-language
`apply_scope(n, F')` is not modelled here because element trees
in the surface language do not carry substituted-fact arguments
(those live in exception guards, handled by `Cross.lean`'s
`SectionRef` algebra). The `crossRef` constructor reuses ambient
facts (the `is_infringed(n)` shape). -/
inductive ElementDeep where
  /-- Leaf fact, indexed by name (mirrors `Element` /
  `Eval.lean`'s `Element.eval`). -/
  | fact     : (name : String) → ElementDeep
  /-- Cross-section reference to another statute in the module,
  by `section_number`. Evaluates to that statute's
  `Statute.convicts` truth value under ambient facts. -/
  | crossRef : (sectionNumber : String) → ElementDeep
  /-- `all_of` combinator. -/
  | allOf    : List ElementDeep → ElementDeep
  /-- `any_of` combinator. -/
  | anyOf    : List ElementDeep → ElementDeep

/-! ## §6-cross-v9 layer 2 — Lift from `ElementGroup` -/

mutual

/-- Lift a v4–v8 `ElementGroup` into the v9 `ElementDeep`. The
existing surface library carries no `crossRef` leaves in
element trees, so the lift is total and structure-preserving.
The mutual `_list` helper makes the structural-recursion
checker happy on the nested-`List` cases. -/
def ElementGroup.toDeep : ElementGroup → ElementDeep
  | .leaf e   => ElementDeep.fact e.name
  | .allOf gs => ElementDeep.allOf (ElementGroup.toDeepList gs)
  | .anyOf gs => ElementDeep.anyOf (ElementGroup.toDeepList gs)

def ElementGroup.toDeepList : List ElementGroup → List ElementDeep
  | []      => []
  | g :: gs => ElementGroup.toDeep g :: ElementGroup.toDeepList gs

end

/-- Project a `Statute` onto its element-body in `ElementDeep`
form, via `ElementGroup.toDeep`. -/
def Statute.deepBody (s : Statute) : ElementDeep :=
  ElementGroup.toDeep s.elements

/-! ## §6-cross-v9 layer 3 — Fuel-bounded evaluator -/

mutual

/-- Evaluate a deep element tree under a section table `sigma`,
ambient facts `F`, and a `fuel : Nat` budget. The `crossRef`
branch reduces to the v8 `Statute.convicts` on the referenced
section (which itself uses only leaf-fact `Element.eval`, so the
v8-side call consumes no further fuel from this evaluator's
budget). Fuel exhaustion on a `crossRef` returns `false`,
mirroring the sound under-approximation `Element.eval` applies
to a missing fact. -/
def ElementDeep.eval :
    (sigma : String → Option Statute) → Facts → Nat → ElementDeep → Bool
  | _,     F, _,     .fact name      => F name
  | _,     _, 0,     .crossRef _     => false
  | sigma, F, _ + 1, .crossRef sec   =>
      match sigma sec with
      | none   => false
      | some s => s.convicts F
  | sigma, F, n,     .allOf gs       => ElementDeep.evalAll sigma F n gs
  | sigma, F, n,     .anyOf gs       => ElementDeep.evalAny sigma F n gs

/-- All-of over an `ElementDeep` list. -/
def ElementDeep.evalAll :
    (String → Option Statute) → Facts → Nat → List ElementDeep → Bool
  | _,     _, _, []        => true
  | sigma, F, n, g :: rest =>
      ElementDeep.eval sigma F n g && ElementDeep.evalAll sigma F n rest

/-- Any-of over an `ElementDeep` list. -/
def ElementDeep.evalAny :
    (String → Option Statute) → Facts → Nat → List ElementDeep → Bool
  | _,     _, _, []        => false
  | sigma, F, n, g :: rest =>
      ElementDeep.eval sigma F n g || ElementDeep.evalAny sigma F n rest

end

/-! ## §6-cross-v9 layer 4 — `crossRef`-freeness predicate -/

mutual

/-- Whether a deep element tree contains no `crossRef` leaves.
Decidable Bool predicate. -/
def ElementDeep.crossRefFree : ElementDeep → Bool
  | .fact _     => true
  | .crossRef _ => false
  | .allOf gs   => ElementDeep.crossRefFreeList gs
  | .anyOf gs   => ElementDeep.crossRefFreeList gs

/-- List variant — explicit recursion. -/
def ElementDeep.crossRefFreeList : List ElementDeep → Bool
  | []      => true
  | g :: gs => ElementDeep.crossRefFree g && ElementDeep.crossRefFreeList gs

end

/- `ElementGroup.toDeep` always produces a `crossRefFree`
`ElementDeep`. -/
mutual

/-- `ElementGroup.toDeep` always produces a `crossRefFree`
`ElementDeep` (mutual induction). -/
theorem ElementGroup.toDeep_crossRefFree :
    ∀ (g : ElementGroup), (ElementGroup.toDeep g).crossRefFree = true
  | .leaf _   => by
      simp only [ElementGroup.toDeep, ElementDeep.crossRefFree]
  | .allOf gs => by
      simp only [ElementGroup.toDeep, ElementDeep.crossRefFree]
      exact ElementGroup.toDeep_crossRefFree_list gs
  | .anyOf gs => by
      simp only [ElementGroup.toDeep, ElementDeep.crossRefFree]
      exact ElementGroup.toDeep_crossRefFree_list gs

theorem ElementGroup.toDeep_crossRefFree_list :
    ∀ (gs : List ElementGroup),
      ElementDeep.crossRefFreeList (ElementGroup.toDeepList gs) = true
  | []      => by
      simp only [ElementGroup.toDeepList, ElementDeep.crossRefFreeList]
  | g :: gs => by
      simp only [ElementGroup.toDeepList, ElementDeep.crossRefFreeList]
      rw [ElementGroup.toDeep_crossRefFree g]
      rw [ElementGroup.toDeep_crossRefFree_list gs]
      rfl

end

/-! ## §6-cross-v9 layer 5 — Conservative-extension theorem -/

/- **Conservative extension**: on the existing surface library
(no `crossRef` leaves in element trees), the v9 evaluator
agrees with the v4–v8 `ElementGroup.eval` at *every* fuel
budget. Fuel is irrelevant when no `crossRef` is present.
Mutual induction on the `ElementGroup` shape. -/
mutual

/-- Conservative-extension lemma at the `ElementGroup` level. -/
theorem ElementDeep.eval_toDeep_compat
    (sigma : String → Option Statute) (F : Facts) (n : Nat) :
    ∀ (g : ElementGroup),
      ElementDeep.eval sigma F n (ElementGroup.toDeep g)
        = ElementGroup.eval g F
  | .leaf e   => by
      simp only [ElementGroup.toDeep, ElementDeep.eval, ElementGroup.eval,
        Element.eval]
  | .allOf gs => by
      simp only [ElementGroup.toDeep, ElementDeep.eval, ElementGroup.eval]
      exact ElementDeep.eval_toDeep_compat_all sigma F n gs
  | .anyOf gs => by
      simp only [ElementGroup.toDeep, ElementDeep.eval, ElementGroup.eval]
      exact ElementDeep.eval_toDeep_compat_any sigma F n gs

theorem ElementDeep.eval_toDeep_compat_all
    (sigma : String → Option Statute) (F : Facts) (n : Nat) :
    ∀ (gs : List ElementGroup),
      ElementDeep.evalAll sigma F n (ElementGroup.toDeepList gs)
        = ElementGroup.evalAll gs F
  | []      => by
      simp only [ElementGroup.toDeepList, ElementDeep.evalAll,
        ElementGroup.evalAll]
  | g :: gs => by
      simp only [ElementGroup.toDeepList, ElementDeep.evalAll,
        ElementGroup.evalAll]
      rw [ElementDeep.eval_toDeep_compat sigma F n g]
      rw [ElementDeep.eval_toDeep_compat_all sigma F n gs]

theorem ElementDeep.eval_toDeep_compat_any
    (sigma : String → Option Statute) (F : Facts) (n : Nat) :
    ∀ (gs : List ElementGroup),
      ElementDeep.evalAny sigma F n (ElementGroup.toDeepList gs)
        = ElementGroup.evalAny gs F
  | []      => by
      simp only [ElementGroup.toDeepList, ElementDeep.evalAny,
        ElementGroup.evalAny]
  | g :: gs => by
      simp only [ElementGroup.toDeepList, ElementDeep.evalAny,
        ElementGroup.evalAny]
      rw [ElementDeep.eval_toDeep_compat sigma F n g]
      rw [ElementDeep.eval_toDeep_compat_any sigma F n gs]

end

/-- **Top-level v9 conservative-extension headline.** For any
statute `s`, ambient `(sigma, F)`, and any fuel `n`, the v9
deep-evaluator on `s.deepBody` agrees with the v4–v8
`Statute.elementsSatisfied`. Reduces to `eval_toDeep_compat`. -/
theorem Statute.deepBody_compat
    (s : Statute) (sigma : String → Option Statute) (F : Facts) (n : Nat) :
    ElementDeep.eval sigma F n s.deepBody = s.elementsSatisfied F := by
  unfold Statute.deepBody Statute.elementsSatisfied
  exact ElementDeep.eval_toDeep_compat sigma F n s.elements

/-! ## §6-cross-v9 follow-ups

Deferred to a follow-up session:

1. **Well-founded recursion driven by `CrossRefGraph` depth.**
   Replace the explicit `fuel : Nat` parameter with a
   well-founded recursion whose termination measure is the
   topological depth of the cross-reference graph under the
   v8 `acyclic` invariant. At that point the v8 hypothesis
   `g.acyclic = true` becomes load-bearing on the recursion's
   well-foundedness, completing the §6.6 boundary statement.

2. **Recursive crossRef semantics.** The current `crossRef`
   branch reduces to v8 `Statute.convicts`, which evaluates
   the referenced statute under leaf-fact-only semantics —
   non-recursive at the v9 layer. A follow-up extension would
   replace `Statute.convicts F` with a deep `Statute.convictsDeep
   sigma F (n - 1)` call, recursively consulting `sigma` at
   each `crossRef`. Termination falls out of the well-founded
   relation in (1).

3. **`crossRef`-bearing soundness lemma.** Strengthen
   `acyclic_canonical_cross_satisfies` so the canonical model
   discharges the bicond bundle for a module whose statutes
   carry `crossRef` element-leaves, not just leaf-fact-only
   trees. Closes the cross-section dimension of Lemma 6.4'.

4. **`apply_scope` lift.** Add an `applyScope` constructor to
   `ElementDeep` with a substituted-facts argument. Current
   v9 layer covers `is_infringed` only.

The conservative-extension theorem `Statute.deepBody_compat` is
the kernel-checked base camp for those follow-ups: it shows the
v9 layer adds capacity without perturbing v4–v8 correctness on
the existing surface library. -/

end Yuho
