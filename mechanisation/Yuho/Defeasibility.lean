/-
Defeasibility.lean - rebut/undercut split for exception soundness.

The Z3 and operational layers both keep `_fires` as the active
inference atom. This file records the two conclusion-level facts:
rebuts negate conviction; undercuts do not negate conviction unless
a rebut also fires.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval

namespace Yuho

/-- An undercutting node is not a rebutting node. -/
theorem undercut_fire_is_not_rebut_fire
    (xs : List Exception) (F : Facts) (x : Exception)
    (hRelation : x.relation = .undercuts) :
    Exception.rebutFires xs F x = false := by
  simp [Exception.rebutFires, Exception.rebutsConclusion, hRelation]

/-- Rebut soundness: a fired rebutting exception negates conviction. -/
theorem rebut_soundness
    (s : Statute) (F : Facts)
    (hRebut : Exception.anyRebutFires s.exceptions F = true) :
    s.convicts F = false := by
  unfold Statute.convicts Statute.anyExceptionFires
  rw [hRebut]
  simp

/-- Undercut soundness: fired undercuts alone do not negate conviction. -/
theorem undercut_soundness
    (s : Statute) (F : Facts)
    (hNoRebut : Exception.anyRebutFires s.exceptions F = false)
    (_hUndercut : Exception.anyUndercutFires s.exceptions F = true) :
    s.convicts F = s.elementsSatisfied F := by
  unfold Statute.convicts Statute.anyExceptionFires
  rw [hNoRebut]
  simp

end Yuho
