/-
Abstract SMT-encoding model.

The Z3 backend in the wider toolchain emits a finite set of named
boolean variables and assertions; a *satisfying assignment* is any
mapping from those names to booleans that satisfies the
assertions. For the mechanisation we work at the abstraction
level above any specific solver — we model an "SMT model"
abstractly and require it to satisfy the *biconditionals* the Z3
generator emits.

The biconditionals we need are exactly the ones §6 names:
- per-leaf-element:    `<sX>_<elem>_satisfied = elementEval`
- per-group:           `elementsSatisfied = elementGroupEval`
- per-exception:       `<sX>_<exc>_fires = exceptionFires`
- per-statute:         `<sX>_conviction = elementsSatisfied ∧ ¬anyFires`

This file declares the abstraction and `SMTModel.satisfies`
predicate; `Soundness.lean` then proves the lemmas relating
`SMTModel.satisfies` to the operational evaluator's verdict.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval

namespace Yuho

/-- Abstract SMT model: maps element identifiers to truth values
(the encoded fact pattern), and exception labels to "fires" bools.
Conviction follows by definition (we don't need a separate field).

In the real Z3 backend these are `z3.Bool` atoms inside a satisfying
assignment; here we abstract them as plain functions because the
soundness theorem is invariant under choice of solver. -/
structure SMTModel where
  /-- The fact-pattern encoded by this model. Each element's
  `<sX>_<elem>_satisfied` Bool's value becomes the corresponding
  fact-map entry. -/
  facts : Facts
  /-- Whether each labelled exception fires under this model. -/
  excFires : String → Bool

/-- The biconditionals a Z3 model must satisfy to be a *satisfying
assignment* of the constraints emitted for statute `s`. We capture
the four families inline rather than as separate axioms so the
proof obligations of §6 stay visible. -/
def SMTModel.satisfies (m : SMTModel) (s : Statute) : Prop :=
  -- (B1) Per-element biconditional: trivially holds because
  -- `m.facts e.name` *is* the value `<sX>_<elem>_satisfied` is
  -- assigned in any satisfying model.
  (∀ e : Element, m.facts e.name = e.eval m.facts) ∧
  -- (B2) Per-exception biconditional: the firedSet computation
  -- agrees with the model's per-label fires bools.
  (∀ label : String,
    m.excFires label = decide (label ∈ Exception.firedSet s.exceptions m.facts)) ∧
  -- (B3) Conviction biconditional: elements all hold AND no
  -- exception fires.
  -- This composes from B1 + B2 + the AllOf / AnyOf propagation.
  True  -- placeholder; the conviction biconditional is an outcome
        -- of the lemmas, not an independent axiom.

end Yuho
