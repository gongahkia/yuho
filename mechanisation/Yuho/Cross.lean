/-
Cross.lean — v3 mechanisation of the cross-section composition
step of Theorem 6.1; cf. `paper/sections/soundness.tex` Lemma
`lem:soundness-cross` and `paper/sections/semantics.tex`
\S\ref{subsec:semantics-cross-section}.

The lemma covers the two cross-section predicates:

* `is_infringed(n')` — does section `n'` convict under the
  ambient fact pattern?
* `apply_scope(n', F')` — does section `n'` convict under the
  parent-supplied (Catala-style) fact pattern `F'`?

The Z3 backend declares one boolean atom `<sX>_conviction` per
referenced section, *deduplicated by name* — every reference to
section `n'` resolves to the same atom. The lemma asserts that
this atom's truth in any satisfying assignment agrees with the
operational `Statute.convicts` judgement on the same fact pattern.

This file is a *v3 scaffold*. Three layers, mirroring the layout
of `Graph.lean`:

1. Cross-section reference AST (`SectionRef`) and a per-module
   conviction-atom carrier (`CrossSMTModel` extending
   `GraphSMTModel`). Pure data; no proof obligations.
2. The biconditional bundle `CrossSMTModel.satisfies`, asserting
   the per-statute conviction biconditional for every statute
   declared in the module. Statement-only; no proof obligations.
3. The proof of `cross_section_correspondence` and the two
   sister lemmas
   `is_infringed_correspondence` /
   `apply_scope_correspondence`, all kernel-checked.

The "well-founded relation over the inter-section reference
graph" the paper §6.6 boundary statement mentions is *not* needed
at this abstraction level: the dedupe happens inside the Z3
generator (`_conviction_bool(n')` declares the atom lazily and
caches it by name), so by the time we reach the
`CrossSMTModel.satisfies` biconditional bundle, every reference
to section `n'` already resolves to the same atom by hypothesis.
The follow-on work the paper estimates at 2–3 person-months
covers proving that the *Python generator's* dedupe is faithful;
that lives in the oracle-port follow-up, not here.

What remains as a follow-up: a parallel mechanisation showing
that `_conviction_bool`'s lazy declaration in the Python generator
matches the abstract dedupe assumed in this file. That is the
oracle-discharge work tracked in `todo.md`.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs
import Yuho.Graph

namespace Yuho

/-! ## §6-cross-v3 layer 1 — Cross-section reference AST -/

/-- A cross-section reference, as it appears in a guard or
expression. Mirrors §3 of the paper:

* `isInfringed n` — re-uses ambient facts.
* `applyScope n F'` — substitutes a supplied fact pattern.

Operationally both reduce to "does `n` convict under the relevant
fact pattern". -/
inductive SectionRef where
  /-- `is_infringed(n)` — re-uses ambient `F`. -/
  | isInfringed : (sectionNumber : String) → SectionRef
  /-- `apply_scope(n, F')` — substitutes `F'`. -/
  | applyScope  : (sectionNumber : String) → (substituted : Facts) → SectionRef

/-- The operational reduction of a cross-section reference under
an ambient fact pattern and a section lookup table `sigma`
(written `Σ` in the paper's inference rules). Mirrors the
`IsInfringed` and `ApplyScope` rules of \S3. -/
def SectionRef.eval (sigma : String → Option Statute) (F : Facts) :
    SectionRef → Option Bool
  | .isInfringed n   => (sigma n).map (fun s => s.convicts F)
  | .applyScope n F' => (sigma n).map (fun s => s.convicts F')

/-- A finite section table, derived from a `Module` by
section_number lookup. Out-of-module references resolve to
`none`, mirroring the §6.6 boundary statement on cross-library
references. -/
def Module.lookup (mod : Module) (n : String) : Option Statute :=
  mod.statutes.find? (fun s => s.section_number = n)

/-! ## §6-cross-v3 layer 2 — Cross-section SMT model -/

/-- Extended SMT model that carries one conviction atom per
referenced section, on top of the per-element + per-group +
per-exception atoms inherited from `GraphSMTModel`. The Z3
generator emits one such atom (`<sX>_conviction`) per unique
section number reachable from the module under translation. -/
structure CrossSMTModel extends GraphSMTModel where
  /-- The per-section conviction atom assigned by the model.
  Indexed by section number; the dedupe-by-name property of
  `_conviction_bool` in the Python generator is captured here as
  the *single-valued* nature of this function. -/
  convicts : String → Bool

/-- The biconditionals a Z3 model must satisfy to be a satisfying
assignment for an entire `Module`. The cross-section bundle is
strictly stronger than `GraphSMTModel.satisfies` (which is
single-statute): it asserts the per-statute graph + exception
biconditionals for *every* statute in the module, and adds the
per-section conviction biconditional (B3) on top. -/
structure CrossSMTModel.satisfies (m : CrossSMTModel) (mod : Module) : Prop where
  /-- For every statute in the module, the inherited
  graph-level biconditional bundle holds. -/
  graph : ∀ s ∈ mod.statutes, m.toGraphSMTModel.satisfies s
  /-- (B3) Per-section conviction biconditional. The conviction
  atom for `s.section_number` agrees with the operational
  `Statute.convicts` under the model's fact pattern. -/
  convs : ∀ s ∈ mod.statutes,
    m.convicts s.section_number = s.convicts m.facts

/-! ## §6-cross-v3 layer 3 — The correspondence theorems

Three theorems, all kernel-checked:

* `cross_section_correspondence` — the abstract per-section
  bicond (Lemma 6.4').
* `is_infringed_correspondence` — specialisation for the
  ambient-facts variant.
* `apply_scope_correspondence` — specialisation for the
  substituted-facts variant.

The substantive content is in the operational `SectionRef.eval`
definition (which threads the right fact pattern per constructor)
and in the `convs` field of `satisfies` (which asserts the bicond
holds for every in-module section).
-/

/-- **Lemma 6.4' (cross-section correspondence).** For every
statute `s` in a module `mod` and every satisfying assignment
`m`, the model's conviction atom for `s.section_number` agrees
with the operational `Statute.convicts` judgement under the
model's fact pattern. -/
theorem cross_section_correspondence
    (m : CrossSMTModel) (mod : Module) (h : m.satisfies mod)
    (s : Statute) (hmem : s ∈ mod.statutes) :
    m.convicts s.section_number = s.convicts m.facts :=
  h.convs s hmem

/-- **Lemma 6.4'.IsInfringed.** The model's conviction atom for
the referenced section agrees with the operational
`SectionRef.eval` under the *ambient* fact pattern. -/
theorem is_infringed_correspondence
    (m : CrossSMTModel) (mod : Module) (h : m.satisfies mod)
    (n : String) (s : Statute)
    (hlookup : mod.lookup n = some s)
    (hname : s.section_number = n) :
    some (m.convicts n) = (SectionRef.isInfringed n).eval mod.lookup m.facts := by
  -- LHS: `some (m.convicts n)`. RHS reduces (by `SectionRef.eval`'s
  -- isInfringed branch + `hlookup`) to
  -- `some (s.convicts m.facts)`. Then `cross_section_correspondence`
  -- (after relating index `n` to `s.section_number` via `hname`)
  -- closes the per-statute conviction bicond.
  show some (m.convicts n) = (mod.lookup n).map (fun s' => s'.convicts m.facts)
  rw [hlookup, Option.map_some']
  congr 1
  have hmem : s ∈ mod.statutes :=
    List.mem_of_find?_eq_some (l := mod.statutes) hlookup
  rw [← hname]
  exact cross_section_correspondence m mod h s hmem

/-- **Lemma 6.4'.ApplyScope.** Symmetric to
`is_infringed_correspondence`, but the conviction is judged under
a *parent-supplied* fact pattern `F'` rather than the ambient
`m.facts`.

Important caveat: the SMT atom `m.convicts n` is constrained
against `m.facts` by the `convs` field of `satisfies`. To match
`apply_scope`'s substituted facts, we either need a separate atom
indexed by `(n, F')` (which the Python generator does *not* emit
— it dedupes by section number alone) OR we restrict the lemma
to fact patterns where the conviction value coincides. The Z3
generator handles this by re-asserting the conviction
biconditional for `n` under `F'` only when `apply_scope` is used
*at the top level*; nested `apply_scope` calls are flagged by the
linter as cross-library and rejected.

We therefore state this lemma under the **fact-coincidence
hypothesis** `s.convicts F' = s.convicts m.facts`, which the
linter discharges in practice. The *unrestricted* version of this
lemma is the cross-library case the paper §6.6 boundary statement
explicitly puts out of scope. -/
theorem apply_scope_correspondence
    (m : CrossSMTModel) (mod : Module) (h : m.satisfies mod)
    (n : String) (F' : Facts) (s : Statute)
    (hlookup : mod.lookup n = some s)
    (hname : s.section_number = n)
    (hcoincide : s.convicts F' = s.convicts m.facts) :
    some (m.convicts n) = (SectionRef.applyScope n F').eval mod.lookup m.facts := by
  show some (m.convicts n) = (mod.lookup n).map (fun s' => s'.convicts F')
  rw [hlookup, Option.map_some']
  congr 1
  have hmem : s ∈ mod.statutes :=
    List.mem_of_find?_eq_some (l := mod.statutes) hlookup
  rw [hcoincide, ← hname]
  exact cross_section_correspondence m mod h s hmem

/-! ## §6-cross-v3 follow-ups

What is *not* covered by this file:

1. **Oracle discharge for `_conviction_bool` dedupe.** The
   Python generator's lazy declaration is assumed faithful here
   (the single-valued `convicts : String → Bool` field of
   `CrossSMTModel` encodes that assumption). Discharging this
   assumption requires porting `_conviction_bool` into Lean and
   proving its caching is sound. Tracked in `todo.md` as the
   oracle-port bullet.

2. **Cross-library case for `apply_scope`.** When the referenced
   section is *not* in the module, the conviction atom is
   unconstrained. Per §6.6 of the paper, we treat this as out of
   scope; the case-law differential testing of
   \S\ref{subsec:case_law_diff} stays within same-module fact
   patterns to honour the theorem's restriction.

3. **Recursive cross-section references.** A statute `s_a`
   referencing `s_b` referencing `s_a` would, in the operational
   semantics, require a fixed-point construction. The Python
   linter rejects such cycles (mirroring the defeats-acyclicity
   invariant for exceptions); this file inherits that rejection
   as an unspoken hypothesis. A v4 extension could mechanise the
   linter's acyclicity check directly. -/

end Yuho
