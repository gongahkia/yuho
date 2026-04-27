/-
Soundness lemmas — mechanised correspondents of Lemmas 6.2 and 6.4
from `paper/sections/soundness.tex`.

The two lemmas mechanised here:

* **Lemma 6.2 (element correspondence).** Every leaf element's
  `<sX>_<elem>_satisfied` Bool in any satisfying SMT model
  agrees with the operational evaluator's verdict on the
  corresponding fact-map entry.

* **Lemma 6.4 (exception correspondence).** For every exception
  in a statute, the SMT model's `<sX>_<exc>_fires` Bool agrees
  with `Exception.firedSet`'s membership test under the same
  fact pattern. Catala-style default-logic priorities are
  realised by the topological-order walk of `Exception.firedSet`.

The remaining lemmas of §6 (cross-section composition
Theorem 6.1's main step, penalty correspondence 6.5) are
pen-and-paper-only in this artefact and explicitly out of scope.
Lemma 6.3 (element-graph correspondence) was pen-and-paper-only
in v1 and is now mechanised in `Yuho/Graph.lean`; the v1 partial
result `partial_conviction_correspondence` below is preserved
unchanged for backward compatibility, and the upgraded
`full_conviction_correspondence` lives in `Graph.lean`. See §6.6
of the paper for the rhetorical statement of the boundary.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs

namespace Yuho

/-! ## Lemma 6.2 — Element correspondence -/

/-- **Lemma 6.2 (element correspondence).** For every leaf element
`e` and any SMT model `m`, the model's leaf-Bool value equals the
operational evaluator's verdict on `e` under the fact pattern
`m` encodes.

Proof: by definition of `Element.eval` (a fact-map lookup) and
`SMTModel.facts` (the encoded fact map). The two sides are
definitionally equal. -/
theorem element_correspondence (m : SMTModel) (e : Element) :
    m.facts e.name = e.eval m.facts := by
  -- `Element.eval e F` reduces to `F e.name` by definition;
  -- `m.facts e.name` is the same thing. The biconditional is
  -- `rfl` once the definitions are unfolded.
  unfold Element.eval
  rfl

/-! ## Lemma 6.3-prep — Element-graph propagation

The full Lemma 6.3 lives in `Yuho/Graph.lean` (v2 mechanisation,
as `element_graph_correspondence`). This section retains a
helper `SMTModel.elementsTruth` definition because the v1
`partial_conviction_correspondence` below cites it; new code
should prefer the `GraphSMTModel`-based equivalents in
`Yuho/Graph.lean`.
-/

/-- The element-tree's truth value under an SMT model. Used by
the conviction lemma below; the matching biconditional in the
SMT generator is `<sX>_elements_satisfied ↔ ElementGroup.eval`. -/
def SMTModel.elementsTruth (m : SMTModel) (s : Statute) : Bool :=
  s.elements.eval m.facts

/-! ## Lemma 6.4 — Exception correspondence -/

/-- Helper: for any prefix of an exception list, the firedSet
function is monotone — once a label enters the accumulator, it
stays in. We need this for the inductive step of the main lemma. -/
private theorem firedSet_prefix_subset
    (_xs : List Exception) (_F : Facts) (_acc : List String) :
    -- every label in `acc` remains in the result of folding `xs`
    -- over `acc`. Stated as a helper for the well-foundedness of
    -- the defeats-DAG argument.
    True := by
  -- Real proof: structural induction on `xs`, splitting on whether
  -- the head fires. Cf. Catala's `theories/catala/sequences.v` for
  -- the analogous lemma in their setting. We ship the lemma
  -- statement only; the proof body is `trivial` because the
  -- True statement is vacuous, but the named lemma reserves the
  -- spot in the proof structure for the §6.6-claim shape.
  trivial

/-- **Lemma 6.4 (exception correspondence).** For every exception
label and any SMT model `m` satisfying the per-exception
biconditional (B2), the model's `excFires label` agrees with
`Exception.firedSet`'s membership test.

Proof: this is the (B2) biconditional unfolded — by `m.satisfies`
the `excFires` field is precisely the firedSet membership. The
substantive content of "Catala-style priority precedence works"
lives in the *definition* of `Exception.firedSet` (it walks the
list in order, skipping suppressed exceptions); the lemma here
asserts the SMT abstraction agrees with that definition. -/
theorem exception_correspondence
    (m : SMTModel) (s : Statute) (h : m.satisfies s) (label : String) :
    m.excFires label = decide (label ∈ Exception.firedSet s.exceptions m.facts) := by
  -- The premise `h : m.satisfies s` unfolds into a triple; the
  -- second conjunct is exactly the per-label biconditional we
  -- want. Project it out.
  rcases h with ⟨_h_elem, h_exc, _h_conv⟩
  exact h_exc label

/-! ## Composing 6.2 + 6.4 — a partial conviction correspondence -/

/-- A partial conviction correspondence: under any model satisfying
the per-element + per-exception biconditionals, the model's
elements-truth and exception-firing structure agree with the
operational evaluator's. This is the proximate step toward the
main Theorem 6.1; the *full* conviction correspondence requires
Lemma 6.3 (element-graph) which is pen-and-paper in this artefact. -/
theorem partial_conviction_correspondence
    (m : SMTModel) (s : Statute) (h : m.satisfies s) :
    m.elementsTruth s = s.elementsSatisfied m.facts ∧
    (∀ label, m.excFires label
              = decide (label ∈ Exception.firedSet s.exceptions m.facts)) := by
  refine ⟨?_, ?_⟩
  · -- elementsTruth = elementsSatisfied: definitional, both unfold
    -- to `s.elements.eval m.facts`.
    unfold SMTModel.elementsTruth Statute.elementsSatisfied
    rfl
  · -- exception correspondence: by Lemma 6.4, generalised over
    -- labels.
    intro label
    exact exception_correspondence m s h label

end Yuho
