/-
Graph.lean — v2 mechanisation scaffold for Lemma 6.3
(element-graph correspondence; cf. `paper/sections/soundness.tex`
§6.2, lemma `lem:soundness-graph`).

Lemma 6.3 is the structural twin of Catala's bisimulation lemma:
for every element-tree `Es` in a statute and every satisfying SMT
assignment `M`, the model's group-Bool atom for `Es` agrees with
the operational evaluator's verdict on `Es`. The proof is by
structural induction on `ElementGroup`, with the inductive cases
delegating to a list-folding correspondence on the children.

This file is the *v2 closure* of Lemma 6.3. The contents are
organised in three layers, each layer adding strictly more proof
obligations than the last:

1. The extended SMT model `GraphSMTModel`, which exposes per-group
   truth atoms in addition to per-element facts. Pure data; no
   proof obligations.
2. The biconditional bundle `GraphSMTModel.satisfies`, mirroring
   the four families of biconditionals the Z3 generator emits.
   Statement-only; no proof obligations.
3. The proof of `element_graph_correspondence`, assembled from:
   - the leaf base case (`element_graph_correspondence_leaf`),
   - the list-folding sub-lemmas
     `evalAll_corresp_param` / `evalAny_corresp_param` carrying
     the per-child IH as an explicit hypothesis,
   - well-founded recursion over `sizeOf g` for the structural
     induction step, with `decreasing_by` discharged via
     `List.sizeOf_lt_of_mem` + `omega`.

All three layers kernel-check under Lean 4.10.0 with no `sorry`.

The exception biconditional is preserved unchanged from
`SMTAbs.lean`'s (B2) — Lemma 6.3 does not interact with the
exception layer; it lives entirely inside the element tree.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs

namespace Yuho

/-! ## §6.3-v2 layer 1 — The extended SMT model -/

/-- Extended SMT model that exposes a per-group truth atom in
addition to the leaf-level fact map. The Z3 generator declares
one Bool per `ElementGroup` node it visits (one
`<sX>_elements_satisfied`, one per nested sub-group); this
structure is the abstract image of those declarations. -/
structure GraphSMTModel where
  /-- The fact-pattern encoded by this model (per-leaf truth values). -/
  facts : Facts
  /-- The per-group truth atom assigned by the model. The Z3
  generator emits one such Bool per `ElementGroup` node; here we
  abstract them as a function `ElementGroup → Bool`. -/
  groupTruth : ElementGroup → Bool
  /-- Whether each labelled exception fires under this model. -/
  excFires : String → Bool

/-! ## §6.3-v2 layer 2 — The satisfiability bundle -/

/-- The biconditionals a Z3 model must satisfy to be a *satisfying
assignment* of the constraints emitted for statute `s`. This is
the v2 successor of `SMTModel.satisfies` in `SMTAbs.lean`, lifted
to the per-group atoms required for Lemma 6.3.

The four families are stated as separate fields rather than as a
single `∧` so the proof scripts in this file can project them by
name. The leaf, allOf, and anyOf families together discharge the
generator's element-tree biconditionals; the `exc` family carries
over unchanged from (B2) in `SMTAbs.lean`. -/
structure GraphSMTModel.satisfies (m : GraphSMTModel) (s : Statute) : Prop where
  /-- (B1.leaf) Per-leaf-element biconditional. The Z3 atom
  `<sX>_<elem>_satisfied` is the same as the encoded fact-map
  entry by construction. -/
  leaf : ∀ e : Element,
    m.groupTruth (.leaf e) = m.facts e.name
  /-- (B1.allOf) Per-`all_of`-group biconditional. The group's
  truth atom is the conjunction of its children's atoms. -/
  allOf : ∀ gs : List ElementGroup,
    m.groupTruth (.allOf gs) = gs.all m.groupTruth
  /-- (B1.anyOf) Per-`any_of`-group biconditional. The group's
  truth atom is the disjunction of its children's atoms. -/
  anyOf : ∀ gs : List ElementGroup,
    m.groupTruth (.anyOf gs) = gs.any m.groupTruth
  /-- (B2) Per-exception biconditional, carried over from
  `SMTAbs.lean`. Lemma 6.3 does not interact with this family,
  but we bundle it here so a single `satisfies` predicate covers
  the whole statute. -/
  exc : ∀ label : String,
    m.excFires label = decide (label ∈ Exception.firedSet s.exceptions m.facts)

/-! ## §6.3-v2 layer 3 — Lemma 6.3 itself

The theorem `element_graph_correspondence` decomposes into:

  * the leaf base case (`element_graph_correspondence_leaf`),
  * a list-folding correspondence for `all_of`
    (`evalAll_corresp_param`),
  * a list-folding correspondence for `any_of`
    (`evalAny_corresp_param`),
  * the structural-induction step that ties them together via
    well-founded recursion on `sizeOf g`.

All four are kernel-checked.
-/

/-- **Lemma 6.3 base case (leaf).** For every leaf element `e`
and every satisfying assignment `m`, the group-truth atom for the
leaf agrees with the operational element-evaluator. -/
theorem element_graph_correspondence_leaf
    (m : GraphSMTModel) (s : Statute) (h : m.satisfies s) (e : Element) :
    m.groupTruth (.leaf e) = (ElementGroup.leaf e).eval m.facts := by
  -- LHS: by (B1.leaf), `m.groupTruth (.leaf e) = m.facts e.name`.
  -- RHS: by `ElementGroup.eval`/`Element.eval`, also `m.facts e.name`.
  simp [h.leaf e, ElementGroup.eval, Element.eval]

/-- **List-folding correspondence for `all_of`.** A reusable
sub-lemma: if every member of `gs` satisfies the per-group
correspondence, then `gs.all m.groupTruth` agrees with
`ElementGroup.evalAll gs m.facts`. The hypothesis is the
per-child induction hypothesis the structural-induction step
will eventually supply. -/
theorem evalAll_corresp_param
    (m : GraphSMTModel) (gs : List ElementGroup)
    (ih : ∀ g ∈ gs, m.groupTruth g = g.eval m.facts) :
    gs.all m.groupTruth = ElementGroup.evalAll gs m.facts := by
  induction gs with
  | nil => simp [List.all, ElementGroup.evalAll]
  | cons g rest ih_rest =>
    have hg : m.groupTruth g = g.eval m.facts :=
      ih g (List.mem_cons_self _ _)
    have hrest : ∀ g' ∈ rest, m.groupTruth g' = g'.eval m.facts :=
      fun g' hmem => ih g' (List.mem_cons_of_mem _ hmem)
    simp [List.all, ElementGroup.evalAll, hg, ih_rest hrest]

/-- **List-folding correspondence for `any_of`.** The
`evalAll_corresp_param` mirror — symmetric proof, with `||`
replacing `&&` and `false`/`true` flipped at the empty case. -/
theorem evalAny_corresp_param
    (m : GraphSMTModel) (gs : List ElementGroup)
    (ih : ∀ g ∈ gs, m.groupTruth g = g.eval m.facts) :
    gs.any m.groupTruth = ElementGroup.evalAny gs m.facts := by
  induction gs with
  | nil => simp [List.any, ElementGroup.evalAny]
  | cons g rest ih_rest =>
    have hg : m.groupTruth g = g.eval m.facts :=
      ih g (List.mem_cons_self _ _)
    have hrest : ∀ g' ∈ rest, m.groupTruth g' = g'.eval m.facts :=
      fun g' hmem => ih g' (List.mem_cons_of_mem _ hmem)
    simp [List.any, ElementGroup.evalAny, hg, ih_rest hrest]

/-- **Lemma 6.3 (element-graph correspondence)** — full statement.

For every element-tree `g` in a statute `s` and every satisfying
assignment `m`, the model's group-truth atom for `g` agrees with
the operational element-evaluator's verdict on `g`.

Proof structure: leaf base case closed by
`element_graph_correspondence_leaf`; inductive cases delegate to
`evalAll_corresp_param` / `evalAny_corresp_param` with a per-child
IH supplied by recursion. Structural recursion through the `List`
in `.allOf`/`.anyOf` is handled by well-founded recursion on
`sizeOf g`; `decreasing_by` discharges via
`List.sizeOf_lt_of_mem` + `omega`.

Status: **closed**. Kernel-checks under Lean 4.10.0. -/
theorem element_graph_correspondence
    (m : GraphSMTModel) (s : Statute) (h : m.satisfies s) :
    ∀ (g : ElementGroup), m.groupTruth g = g.eval m.facts
  | .leaf e   => element_graph_correspondence_leaf m s h e
  | .allOf gs => by
      rw [h.allOf gs, ElementGroup.eval]
      exact evalAll_corresp_param m gs
        (fun g' _ => element_graph_correspondence m s h g')
  | .anyOf gs => by
      rw [h.anyOf gs, ElementGroup.eval]
      exact evalAny_corresp_param m gs
        (fun g' _ => element_graph_correspondence m s h g')
termination_by g => sizeOf g
decreasing_by
  all_goals
    simp_wf
    have := List.sizeOf_lt_of_mem ‹_›
    omega

/-! ## §6.3-v2 corollary scaffolding

Once `element_graph_correspondence` is closed, the partial
conviction lemma (currently in `Soundness.lean`,
`partial_conviction_correspondence`) is upgradable to the *full*
conviction correspondence by composing 6.2 + 6.3 + 6.4. We
declare the upgraded statement here so the §6.6 paper claim has a
named target to cite once the `sorry` above is discharged.
-/

/-- **Full conviction correspondence (target).** Statement-only.
Closure depends on `element_graph_correspondence`. -/
theorem full_conviction_correspondence
    (m : GraphSMTModel) (s : Statute) (h : m.satisfies s) :
    m.groupTruth s.elements = s.elementsSatisfied m.facts ∧
    (∀ label, m.excFires label
              = decide (label ∈ Exception.firedSet s.exceptions m.facts)) := by
  refine ⟨?_, ?_⟩
  · -- direct corollary of Lemma 6.3 specialised to `s.elements`
    have := element_graph_correspondence m s h s.elements
    -- `s.elementsSatisfied F` unfolds to `s.elements.eval F`
    unfold Statute.elementsSatisfied
    exact this
  · intro label
    exact h.exc label

/-! ## §6.3-v2 follow-ups

Closing Lemma 6.3 unblocks two adjacent items, which are
intentionally **out of scope for this file**:

1. **Wire `full_conviction_correspondence` into Theorem 6.1.** The
   `Soundness.lean::partial_conviction_correspondence` lemma
   becomes a corollary of `full_conviction_correspondence` here.
   The `Soundness.lean` boundary comment (lines 18–22) drops
   Lemma 6.3 from the "pen-and-paper-only" list; the paper §6.6
   boundary statement narrows to {6.5, cross-section composition,
   oracle-Z3-port}. *Editorial only — no new proof obligations.*

2. **Cross-section variant.** The cross-section lemma needs a
   separate `GraphSMTModel`-style extension that includes
   per-conviction atoms `cv_{n'}`. Tracked in `todo.md` under the
   cross-section bullet. Estimate: 2–3 person-months per
   `todo.md` L52–54 — this lemma is *not* unblocked by closing
   6.3 (it requires its own structural-induction story over
   inter-statute references).
-/

end Yuho
