/-
Cross.lean — v4 mechanisation of the cross-section composition
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

v4 (this file) refactors the v3 satisfies bundle to use
*qualified* atom names for the exception bicond and adds a
constructive `Generator.canonicalCrossModel` witness. v3
inherited `GraphSMTModel`'s single `excFires : String → Bool`
indexed by *raw* exception labels, which is unsound for
multi-statute modules where two statutes share a raw label
(e.g. both s299 and s300 carry a "consent" exception with
different guards). v4 replaces this with a per-statute,
per-exception bicond keyed on `Generator.exceptionAtomName`'s
qualified `<sX>_exc_<label>_fires` strings, matching the
Python generator's atom-naming convention exactly.

Layers, mirroring the v3 layout but with the v4 refactor in
place:

1. Cross-section reference AST (`SectionRef`) and a per-module
   conviction-atom carrier (`CrossSMTModel` extending
   `GraphSMTModel`). Pure data; no proof obligations.
2. The biconditional bundle `CrossSMTModel.satisfies`,
   asserting per-statute element-tree biconditionals,
   per-statute qualified-atom exception biconditionals, and
   the per-section conviction biconditional for every statute
   declared in the module. Statement-only; no proof
   obligations.
3. The proof of `cross_section_correspondence` and the two
   sister lemmas
   `is_infringed_correspondence` /
   `apply_scope_correspondence`, all kernel-checked. Their
   signatures are unchanged from v3 (they only consume the
   `convs` field, which is preserved verbatim).
4. v4 addition: `Generator.canonicalCrossModel` plus the
   constructive discharge `canonical_cross_satisfies`,
   exhibiting a satisfying assignment for any module + facts
   pair under the section-number-uniqueness invariant.

The "well-founded relation over the inter-section reference
graph" the paper §6.6 boundary statement mentions is *not* needed
at this abstraction level: the dedupe happens inside the Z3
generator (`_conviction_bool(n')` declares the atom lazily and
caches it by name), so by the time we reach the
`CrossSMTModel.satisfies` biconditional bundle, every reference
to section `n'` already resolves to the same atom by hypothesis.

v5 follow-ups still in scope:

* **Cross-library `apply_scope`.** The case-law differential
  testing already restricts to in-module sections; this is a
  v5-stretch item, not a release blocker. The
  `apply_scope_correspondence` `hcoincide` hypothesis is the
  current discharge mechanism.
* **Python-side faithfulness.** Showing that the Python
  generator's `_conviction_bool` lazy declaration matches the
  abstract dedupe assumed by `m.convicts : String → Bool`'s
  single-valued nature. Tracked under `todo.md`'s
  *Generator-emit consolidation* and *Python-side
  faithfulness, structural diff* bullets.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs
import Yuho.Graph
import Yuho.Generator

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

/-- The biconditionals a Z3 model must satisfy to be a
satisfying assignment for an entire `Module`. The v4 refactor
inlines the per-statute element-tree biconditionals (leaf /
allOf / anyOf — these are atom-shape statements that don't
depend on the statute) and replaces v3's raw-label `excFires`
bicond with a *qualified-atom* version keyed on
`Generator.exceptionAtomName`'s `<sX>_exc_<label>_fires`
strings. The qualified-atom shape disambiguates exceptions
that share a raw label across two statutes (e.g. both s299
and s300 carrying a "consent" exception); without
qualification, the v3 bundle was unsatisfiable on any module
with a duplicate raw label.

The four families:

  * (B1.leaf / B1.allOf / B1.anyOf) — the element-tree
    biconditionals, identical to `GraphSMTModel.satisfies`.
  * (B2-q) — the qualified-atom exception biconditional, the
    v4 fix.
  * (B3) — the per-section conviction biconditional, unchanged
    from v3.
-/
structure CrossSMTModel.satisfies (m : CrossSMTModel) (mod : Module) : Prop where
  /-- (B1.leaf) Per-leaf-element biconditional. -/
  leaf : ∀ e : Element,
    m.groupTruth (.leaf e) = m.facts e.name
  /-- (B1.allOf) Per-`all_of`-group biconditional. -/
  allOf : ∀ gs : List ElementGroup,
    m.groupTruth (.allOf gs) = gs.all m.groupTruth
  /-- (B1.anyOf) Per-`any_of`-group biconditional. -/
  anyOf : ∀ gs : List ElementGroup,
    m.groupTruth (.anyOf gs) = gs.any m.groupTruth
  /-- (B2-q) Per-statute, per-exception biconditional with
  *qualified* atom name. The v4 refactor: `m.excFires` is now
  indexed by `<sX>_exc_<label>_fires` matching the Python
  generator's atom-naming convention, so two statutes sharing
  a raw label do not collide. -/
  excQualified : ∀ s ∈ mod.statutes, ∀ x ∈ s.exceptions,
    m.excFires (Generator.exceptionAtomName s x)
      = decide (x.label ∈ Exception.firedSet s.exceptions m.facts)
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

/-! ## §6-cross-v4 layer 4 — Canonical cross-section model

v4 (this layer) closes the abstract module-level oracle on
the **single-statute singleton-module** path the same way
v5's `Generator.canonicalSMTModel` /
`canonicalGraphModel` closed the single-statute SMT / Graph
oracles. We exhibit a constructive
`Generator.canonicalCrossModel` from any `(mod, F)` pair and
prove the singleton-module discharge unconditionally; the
multi-statute discharge requires structural induction over
the module's statute list under the linter's
section-number-uniqueness invariant and is tracked as v5
follow-up below.

The construction is unconditional in `mod` shape:

  * `facts`        — the supplied ambient `F`.
  * `groupTruth`   — operational `ElementGroup.eval F`,
                     identical to `canonicalGraphModel`.
  * `excFires`     — qualified-atom map: for each (s, x) pair
                     in the module, the qualified atom name
                     `<sX>_exc_<label>_fires` maps to the
                     corresponding `firedSet` membership; all
                     other strings default to `false`. Built
                     by structural recursion over the module's
                     statutes (no `Id.run` / `for`-loop;
                     keeps the proof tractable in core Lean
                     without Mathlib helpers).
  * `convicts`     — looks up the section by number and
                     returns `s.convicts F`; out-of-module
                     references default to `false`.
-/

namespace Generator

/-- Search a single statute's exception list for the entry
whose qualified atom name matches `atomName`. Returns
`some firedSet-membership` on a hit, `none` on miss.
Structural recursion over `excs`. -/
def crossExcFiresInExceptions
    (s : Statute) (excs : List Exception)
    (F : Facts) (atomName : String) : Option Bool :=
  match excs with
  | []        => none
  | x :: rest =>
    if Generator.exceptionAtomName s x = atomName then
      some (decide (x.label ∈ Exception.firedSet s.exceptions F))
    else
      crossExcFiresInExceptions s rest F atomName

/-- Search a list of statutes for an exception whose
qualified atom name matches `atomName`. Iterates statutes,
delegating per-statute search to
`crossExcFiresInExceptions`. Returns `some` on a hit,
`none` on miss. Structural recursion over `statutes`. -/
def crossExcFiresInStatutes
    (statutes : List Statute) (F : Facts) (atomName : String) : Option Bool :=
  match statutes with
  | []        => none
  | s :: rest =>
    match crossExcFiresInExceptions s s.exceptions F atomName with
    | some b => some b
    | none   => crossExcFiresInStatutes rest F atomName

/-- For a fixed module + facts pair and a *qualified* atom
name, recover the `firedSet`-membership Bool. Returns
`false` when no match is found (the atom is unconstrained
under the v4 bundle in that case). Wraps
`crossExcFiresInStatutes` with a `getD false` default. -/
def crossExcFires (mod : Module) (F : Facts) (atomName : String) : Bool :=
  (crossExcFiresInStatutes mod.statutes F atomName).getD false

/-- Constructive canonical CrossSMTModel: bundles the v5
canonical graph-side fields (`groupTruth`) with the v4
qualified-atom `excFires` and the per-section `convicts`
lookup. -/
def canonicalCrossModel (mod : Module) (F : Facts) : CrossSMTModel where
  facts := F
  groupTruth := fun g => g.eval F
  -- The inherited `excFires` field uses *qualified* atom
  -- names under v4. Raw-label callers that previously
  -- consulted `excFires "consent"` should switch to
  -- `excFires (exceptionAtomName s x)` per the v4 doc-comment.
  excFires := crossExcFires mod F
  convicts := fun n =>
    match mod.lookup n with
    | some s => s.convicts F
    | none   => false

end Generator

/-! ### Per-exception admittance helper

The discharge of `excQualified` reduces to: when `(s, x)` is
the unique exception in the singleton-module shape, the
canonical search returns the corresponding `firedSet`
membership. We prove this for the head-match case, which
suffices for the singleton-module discharge. -/

/-- When the head exception's qualified atom matches the
target, the search returns the head's firedSet membership. -/
private theorem crossExcFiresInExceptions_head_match
    (s : Statute) (x : Exception) (rest : List Exception)
    (F : Facts) (atomName : String)
    (hmatch : Generator.exceptionAtomName s x = atomName) :
    Generator.crossExcFiresInExceptions s (x :: rest) F atomName
      = some (decide (x.label ∈ Exception.firedSet s.exceptions F)) := by
  unfold Generator.crossExcFiresInExceptions
  rw [if_pos hmatch]

/-- When the head statute's first matching exception is the
target `(s, x)`, the module-level search returns the head's
firedSet membership. -/
private theorem crossExcFiresInStatutes_head_match
    (s : Statute) (rest : List Statute) (x : Exception)
    (F : Facts)
    (hExcMatch :
      Generator.crossExcFiresInExceptions s s.exceptions F
        (Generator.exceptionAtomName s x)
        = some (decide (x.label ∈ Exception.firedSet s.exceptions F))) :
    Generator.crossExcFiresInStatutes (s :: rest) F
        (Generator.exceptionAtomName s x)
      = some (decide (x.label ∈ Exception.firedSet s.exceptions F)) := by
  unfold Generator.crossExcFiresInStatutes
  rw [hExcMatch]

/-- **Singleton-module helper.** For a singleton module
`⟨[s]⟩` whose unique exception list is `[x]`, the
canonical `crossExcFires` returns the firedSet membership
of `x.label`. -/
private theorem crossExcFires_singleton_singleton_exc
    (s : Statute) (x : Exception) (F : Facts)
    (hExc : s.exceptions = [x]) :
    Generator.crossExcFires ⟨[s]⟩ F (Generator.exceptionAtomName s x)
      = decide (x.label ∈ Exception.firedSet s.exceptions F) := by
  unfold Generator.crossExcFires
  -- First rewrite s.exceptions to [x] in the inner search, then
  -- apply the head-match helpers. The conclusion's
  -- `Exception.firedSet s.exceptions F` is preserved literally.
  have hExcMatch :
      Generator.crossExcFiresInExceptions s s.exceptions F
        (Generator.exceptionAtomName s x)
        = some (decide (x.label ∈ Exception.firedSet s.exceptions F)) := by
    have h := crossExcFiresInExceptions_head_match s x [] F
      (Generator.exceptionAtomName s x) rfl
    -- h : crossExcFiresInExceptions s [x] F ... = some (decide (... s.exceptions ...))
    rw [← hExc] at h
    exact h
  rw [crossExcFiresInStatutes_head_match s [] x F hExcMatch]
  rfl

/-! ### Singleton-module discharge

For a single-statute module `⟨[s]⟩`, the canonical cross
model satisfies the v4 bundle unconditionally. This is the
direct analogue of v5's `canonical_smt_satisfies` /
`canonical_graph_satisfies` lifted to the cross-section
bundle.

The multi-statute case requires structural induction over
the statute list and a stronger uniqueness invariant on
qualified atom names; tracked as v5 follow-up. -/

/-- **§6-cross-v4 singleton discharge.** For a single-statute
module `⟨[s]⟩` whose exceptions are exactly `[x]` and
whose section_number is unique within the module, the
canonical cross model satisfies the v4 bundle. -/
theorem canonical_cross_satisfies_singleton_singleton_exc
    (s : Statute) (x : Exception) (F : Facts)
    (hExc : s.exceptions = [x]) :
    (Generator.canonicalCrossModel ⟨[s]⟩ F).satisfies ⟨[s]⟩ where
  leaf  := by
    intro e
    simp [Generator.canonicalCrossModel,
          ElementGroup.eval, Element.eval]
  allOf := by
    intro gs
    simp only [Generator.canonicalCrossModel, ElementGroup.eval]
    induction gs with
    | nil => simp [ElementGroup.evalAll, List.all]
    | cons g rest ih =>
      simp [ElementGroup.evalAll, List.all, ih]
  anyOf := by
    intro gs
    simp only [Generator.canonicalCrossModel, ElementGroup.eval]
    induction gs with
    | nil => simp [ElementGroup.evalAny, List.any]
    | cons g rest ih =>
      simp [ElementGroup.evalAny, List.any, ih]
  excQualified := by
    intro s' hs' x' hx'
    -- s' must equal s (singleton list).
    rw [List.mem_singleton] at hs'
    subst hs'
    -- s' = s case. x' must be the unique element of s.exceptions = [x].
    rw [hExc] at hx'
    rw [List.mem_singleton] at hx'
    subst hx'
    -- x' = x case: apply the singleton helper.
    show Generator.crossExcFires ⟨[s']⟩ F
            (Generator.exceptionAtomName s' x')
          = decide (x'.label ∈ Exception.firedSet
                      s'.exceptions F)
    exact crossExcFires_singleton_singleton_exc s' x' F hExc
  convs := by
    intro s' hs'
    rw [List.mem_singleton] at hs'
    subst hs'
    -- s' = s case: lookup returns some s.
    show (match (⟨[s']⟩ : Module).lookup s'.section_number with
          | some s'' => s''.convicts F
          | none     => false)
        = s'.convicts F
    have hlookup :
        (⟨[s']⟩ : Module).lookup s'.section_number = some s' := by
      unfold Module.lookup
      simp [List.find?]
    rw [hlookup]

/-! ## §6-cross-v5 layer 5 — Multi-statute discharge

v4 closed the singleton-module case. v5 (this layer) lifts
the discharge to arbitrary `mod.statutes` by structural
induction over the list, under two linter-enforced
invariants:

  * `hAtomUniq` — qualified-atom-name uniqueness across the
    module: equal atom names imply equal `(statute, label)`.
    This is the conjunction of (a) section-number uniqueness
    (no two statutes in the module share `section_number`)
    and (b) within-statute label uniqueness (no two
    exceptions in `s.exceptions` share `label`). The Python
    linter rejects modules violating either invariant.
  * `hSecUniq` — section-number-implies-statute identity.
    Same root cause as (a) above, exposed as a separate
    field for the `convs` proof's lookup-uniqueness step.

Under both invariants, `canonical_cross_satisfies` exhibits
the constructive discharge of the abstract module-level
oracle for any `(mod, F)` pair. -/

/-- When no exception in the list shares the target's
qualified atom name, the inner search returns `none`. -/
private theorem crossExcFiresInExceptions_no_match
    (s : Statute) (excs : List Exception)
    (F : Facts) (atomName : String)
    (hNoMatch : ∀ y ∈ excs,
                Generator.exceptionAtomName s y ≠ atomName) :
    Generator.crossExcFiresInExceptions s excs F atomName = none := by
  induction excs with
  | nil => rfl
  | cons y rest ih =>
    unfold Generator.crossExcFiresInExceptions
    have hy : Generator.exceptionAtomName s y ≠ atomName :=
      hNoMatch y (List.mem_cons_self _ _)
    rw [if_neg hy]
    exact ih (fun y' hy' => hNoMatch y' (List.mem_cons_of_mem _ hy'))

/-- Within a single statute's exception list, when `x ∈ excs`
and the qualified atom names of distinct exceptions in
`s.exceptions` are distinct (i.e. label uniqueness within
`s.exceptions`), the inner search returns the firedSet
membership for `x.label`. -/
private theorem crossExcFiresInExceptions_eq_of_mem
    (s : Statute) (excs : List Exception) (F : Facts)
    (x : Exception) (hx : x ∈ excs)
    (hLabelUniq : ∀ y ∈ excs,
                  Generator.exceptionAtomName s y
                    = Generator.exceptionAtomName s x →
                  y.label = x.label) :
    Generator.crossExcFiresInExceptions s excs F
        (Generator.exceptionAtomName s x)
      = some (decide (x.label ∈ Exception.firedSet s.exceptions F)) := by
  induction excs with
  | nil => cases hx
  | cons y rest ih =>
    unfold Generator.crossExcFiresInExceptions
    by_cases hyEq : Generator.exceptionAtomName s y
                      = Generator.exceptionAtomName s x
    · -- Head matches the target atom name.
      rw [if_pos hyEq]
      have hyLabel : y.label = x.label :=
        hLabelUniq y (List.mem_cons_self _ _) hyEq
      rw [hyLabel]
    · -- Head doesn't match; recurse on tail.
      rw [if_neg hyEq]
      cases hx with
      | head =>
        -- x is the head, but head doesn't match — contradiction.
        exact absurd rfl hyEq
      | tail _ hxRest =>
        exact ih hxRest (fun y' hy' =>
          hLabelUniq y' (List.mem_cons_of_mem _ hy'))

/-- When the head statute's exception search returns `none`,
the module-level search recurses to the tail. -/
private theorem crossExcFiresInStatutes_skip_head
    (s : Statute) (rest : List Statute)
    (F : Facts) (atomName : String)
    (hNoHead : Generator.crossExcFiresInExceptions s s.exceptions F atomName
                 = none) :
    Generator.crossExcFiresInStatutes (s :: rest) F atomName
      = Generator.crossExcFiresInStatutes rest F atomName := by
  show (match Generator.crossExcFiresInExceptions s s.exceptions F atomName with
        | some b => some b
        | none   => Generator.crossExcFiresInStatutes rest F atomName)
      = Generator.crossExcFiresInStatutes rest F atomName
  rw [hNoHead]

/-- **§6-cross-v5 multi-statute helper.** When `s ∈ mod.statutes`,
`x ∈ s.exceptions`, and the qualified-atom-name uniqueness
invariant holds across the module, the canonical
`crossExcFires` returns the firedSet membership for
`x.label`. -/
private theorem crossExcFires_eq_of_mem
    (statutes : List Statute) (F : Facts)
    (s : Statute) (x : Exception)
    (hs : s ∈ statutes) (hx : x ∈ s.exceptions)
    (hAtomUniq : ∀ s₁ ∈ statutes, ∀ s₂ ∈ statutes,
                 ∀ x₁ ∈ s₁.exceptions, ∀ x₂ ∈ s₂.exceptions,
                 Generator.exceptionAtomName s₁ x₁
                   = Generator.exceptionAtomName s₂ x₂ →
                 s₁ = s₂ ∧ x₁.label = x₂.label) :
    Generator.crossExcFiresInStatutes statutes F
        (Generator.exceptionAtomName s x)
      = some (decide (x.label ∈ Exception.firedSet s.exceptions F)) := by
  induction statutes with
  | nil => cases hs
  | cons s' rest ih =>
    by_cases hsEq : s' = s
    · -- Head equals target statute: inner search hits.
      subst hsEq
      have hLabel :
          ∀ y ∈ s'.exceptions,
            Generator.exceptionAtomName s' y
              = Generator.exceptionAtomName s' x →
            y.label = x.label := by
        intro y hy heq
        have := hAtomUniq s' (List.mem_cons_self _ _) s'
                          (List.mem_cons_self _ _) y hy x hx heq
        exact this.2
      have hInner :
          Generator.crossExcFiresInExceptions s' s'.exceptions F
              (Generator.exceptionAtomName s' x)
            = some (decide (x.label ∈ Exception.firedSet s'.exceptions F)) :=
        crossExcFiresInExceptions_eq_of_mem s' s'.exceptions F x hx hLabel
      unfold Generator.crossExcFiresInStatutes
      rw [hInner]
    · -- Head differs: inner search misses on head, recurse on tail.
      have hsRest : s ∈ rest := by
        cases hs with
        | head => exact absurd rfl hsEq
        | tail _ hsRest => exact hsRest
      have hAtomUniqRest :
          ∀ s₁ ∈ rest, ∀ s₂ ∈ rest,
          ∀ x₁ ∈ s₁.exceptions, ∀ x₂ ∈ s₂.exceptions,
          Generator.exceptionAtomName s₁ x₁
            = Generator.exceptionAtomName s₂ x₂ →
          s₁ = s₂ ∧ x₁.label = x₂.label := by
        intro s₁ hs₁ s₂ hs₂ x₁ hx₁ x₂ hx₂ heq
        exact hAtomUniq s₁ (List.mem_cons_of_mem _ hs₁) s₂
                        (List.mem_cons_of_mem _ hs₂) x₁ hx₁ x₂ hx₂ heq
      have hNoMatch :
          ∀ y ∈ s'.exceptions,
            Generator.exceptionAtomName s' y
              ≠ Generator.exceptionAtomName s x := by
        intro y hy heq
        have hSameStatute :
            s' = s ∧ y.label = x.label :=
          hAtomUniq s' (List.mem_cons_self _ _) s
                    (List.mem_cons_of_mem _ hsRest) y hy x hx heq
        exact hsEq hSameStatute.1
      have hHeadNone :
          Generator.crossExcFiresInExceptions s' s'.exceptions F
              (Generator.exceptionAtomName s x) = none :=
        crossExcFiresInExceptions_no_match s' s'.exceptions F
          (Generator.exceptionAtomName s x) hNoMatch
      rw [crossExcFiresInStatutes_skip_head s' rest F
            (Generator.exceptionAtomName s x) hHeadNone]
      exact ih hsRest hAtomUniqRest

/-- **§6-cross-v5 lookup helper.** Under section-number
uniqueness, `Module.lookup` (a `List.find?` over the
statutes list) returns `some s` for every `s ∈ statutes`. -/
private theorem find?_section_number_of_mem
    (statutes : List Statute) (s : Statute) (hs : s ∈ statutes)
    (hSecUniq : ∀ s₁ ∈ statutes, ∀ s₂ ∈ statutes,
                s₁.section_number = s₂.section_number → s₁ = s₂) :
    Module.lookup ⟨statutes⟩ s.section_number = some s := by
  show List.find? (fun s'' => decide (s''.section_number = s.section_number))
          statutes = some s
  induction statutes with
  | nil => cases hs
  | cons s' rest ih =>
    by_cases hsEq : s' = s
    · -- Head equals target: find? returns head.
      subst hsEq
      show List.find? (fun s'' => decide (s''.section_number = s'.section_number))
              (s' :: rest) = some s'
      simp [List.find?]
    · -- Head differs: must skip head.
      have hsRest : s ∈ rest := by
        cases hs with
        | head => exact absurd rfl hsEq
        | tail _ hsRest => exact hsRest
      have hSecEq_neg : s'.section_number ≠ s.section_number := by
        intro heq
        exact hsEq (hSecUniq s' (List.mem_cons_self _ _) s
                              (List.mem_cons_of_mem _ hsRest) heq)
      have hSecUniqRest :
          ∀ s₁ ∈ rest, ∀ s₂ ∈ rest,
          s₁.section_number = s₂.section_number → s₁ = s₂ := by
        intro s₁ hs₁ s₂ hs₂ heq
        exact hSecUniq s₁ (List.mem_cons_of_mem _ hs₁) s₂
                      (List.mem_cons_of_mem _ hs₂) heq
      show List.find? (fun s'' => decide (s''.section_number = s.section_number))
              (s' :: rest) = some s
      simp [List.find?, decide_eq_false hSecEq_neg]
      exact ih hsRest hSecUniqRest

/-- **§6-cross-v5 multi-statute discharge.** For any module +
facts pair, the canonical cross model satisfies the v4
bundle, under the linter-enforced qualified-atom-name
uniqueness invariant (`hAtomUniq`) and the section-number
uniqueness invariant (`hSecUniq`).

Both hypotheses are decidable on concrete modules and hold
by construction for every linter-clean module in the corpus.
The Python linter rejects modules violating either; this
theorem is unconditional once the linter has approved the
module. -/
theorem canonical_cross_satisfies
    (mod : Module) (F : Facts)
    (hAtomUniq : ∀ s₁ ∈ mod.statutes, ∀ s₂ ∈ mod.statutes,
                 ∀ x₁ ∈ s₁.exceptions, ∀ x₂ ∈ s₂.exceptions,
                 Generator.exceptionAtomName s₁ x₁
                   = Generator.exceptionAtomName s₂ x₂ →
                 s₁ = s₂ ∧ x₁.label = x₂.label)
    (hSecUniq : ∀ s₁ ∈ mod.statutes, ∀ s₂ ∈ mod.statutes,
                s₁.section_number = s₂.section_number → s₁ = s₂) :
    (Generator.canonicalCrossModel mod F).satisfies mod where
  leaf  := by
    intro e
    simp [Generator.canonicalCrossModel,
          ElementGroup.eval, Element.eval]
  allOf := by
    intro gs
    simp only [Generator.canonicalCrossModel, ElementGroup.eval]
    induction gs with
    | nil => simp [ElementGroup.evalAll, List.all]
    | cons g rest ih =>
      simp [ElementGroup.evalAll, List.all, ih]
  anyOf := by
    intro gs
    simp only [Generator.canonicalCrossModel, ElementGroup.eval]
    induction gs with
    | nil => simp [ElementGroup.evalAny, List.any]
    | cons g rest ih =>
      simp [ElementGroup.evalAny, List.any, ih]
  excQualified := by
    intro s hs x hx
    show Generator.crossExcFires mod F
            (Generator.exceptionAtomName s x)
          = decide (x.label ∈ Exception.firedSet s.exceptions F)
    unfold Generator.crossExcFires
    rw [crossExcFires_eq_of_mem mod.statutes F s x hs hx hAtomUniq]
    rfl
  convs := by
    intro s hs
    show (match mod.lookup s.section_number with
          | some s' => s'.convicts F
          | none    => false)
        = s.convicts F
    have hlookup : mod.lookup s.section_number = some s :=
      find?_section_number_of_mem mod.statutes s hs hSecUniq
    rw [hlookup]

/-! ## §6-cross-v5 follow-ups

The multi-statute discharge above is the v5 closure of the
abstract module-level oracle. Extensions deferred to v6+:

2. **Cross-library case for `apply_scope`.** When the
   referenced section is *not* in the module, the conviction
   atom is unconstrained. Per §6.6 of the paper, we treat
   this as out of scope; the case-law differential testing
   of \S\ref{subsec:case_law_diff} stays within same-module
   fact patterns to honour the theorem's restriction.

3. **Recursive cross-section references.** A statute `s_a`
   referencing `s_b` referencing `s_a` would, in the
   operational semantics, require a fixed-point construction.
   The Python linter rejects such cycles (mirroring the
   defeats-acyclicity invariant for exceptions); this file
   inherits that rejection as an unspoken hypothesis. A v5
   extension could mechanise the linter's acyclicity check
   directly.

4. **Python-side faithfulness.** Showing that the Python
   generator's `_conviction_bool` lazy declaration matches
   the abstract dedupe assumed by the canonical
   `CrossSMTModel.convicts` field. The `make
   verify-structural-diff` harness exercises this on the
   smoke-fixture corpus; full-corpus extension is tracked
   in `todo.md`. -/

end Yuho
