/-
Smoke tests: small executable examples that exercise the
operational evaluator and confirm element correspondence on
concrete fixtures.

These are not part of the formal proof — they confirm the
*definitions* in `Yuho/Eval.lean` compute the values we expect on
small cases. A regression in the operational rules surfaces here
as a `decide`-time mismatch.

Run: `cd mechanisation && lake build Tests`.
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs
import Yuho.Soundness
import Yuho.Graph

namespace Yuho.Tests

open Yuho

/-- Example fact pattern: `death = true`, `intent = true`. -/
def factsHomicide : Facts :=
  Facts.fromList [("death", true), ("intent", true)]

/-- Example: s299 culpable homicide structure (simplified). -/
def s299 : Statute :=
  { section_number := "299"
    title := "Culpable homicide"
    elements :=
      .allOf [
        .leaf { kind := .actusReus, name := "death", description := "" },
        .leaf { kind := .mensRea,   name := "intent", description := "" }
      ]
    exceptions := []
  }

example : s299.elementsSatisfied factsHomicide = true := by
  native_decide

example : s299.convicts factsHomicide = true := by
  native_decide

/-- Example: an exception that fires when `consent = true`. -/
def s299WithConsent : Statute :=
  { s299 with
    exceptions := [
      { label := "consent"
        guard := fun F => F "consent"
        defeats := []
      }
    ]
  }

def factsHomicideWithConsent : Facts :=
  Facts.fromList [("death", true), ("intent", true), ("consent", true)]

example : s299WithConsent.elementsSatisfied factsHomicideWithConsent = true := by
  native_decide

example : s299WithConsent.convicts factsHomicideWithConsent = false := by
  -- Elements satisfied but consent exception fires → no conviction.
  native_decide

/-- Element correspondence holds trivially on this concrete case. -/
example (m : SMTModel) :
    m.facts "death" = (Element.mk .actusReus "death" "").eval m.facts := by
  exact element_correspondence m { kind := .actusReus, name := "death", description := "" }

/-! ## §6.3 v2 smoke tests — exercising `Graph.lean`. -/

/-- A `GraphSMTModel` whose `groupTruth` is defined to *be* the
operational `ElementGroup.eval m.facts`; this is the canonical
saturating model and trivially satisfies the bicond bundle. -/
def canonicalGraphModel (F : Facts) (s : Statute) : GraphSMTModel where
  facts := F
  groupTruth := fun g => g.eval F
  excFires  := fun lbl => decide (lbl ∈ Exception.firedSet s.exceptions F)

/-- The canonical model satisfies the bicond bundle for any statute. -/
theorem canonicalGraphModel_satisfies (F : Facts) (s : Statute) :
    (canonicalGraphModel F s).satisfies s where
  leaf  e  := by
    simp [canonicalGraphModel, ElementGroup.eval, Element.eval]
  allOf gs := by
    simp only [canonicalGraphModel, ElementGroup.eval]
    exact (evalAll_corresp_param (canonicalGraphModel F s) gs (fun _ _ => rfl)).symm
  anyOf gs := by
    simp only [canonicalGraphModel, ElementGroup.eval]
    exact (evalAny_corresp_param (canonicalGraphModel F s) gs (fun _ _ => rfl)).symm
  exc   _  := rfl

/-- Lemma 6.3 specialised to s299 / homicide facts kernel-checks. -/
example :
    (canonicalGraphModel factsHomicide s299).groupTruth s299.elements
      = s299.elements.eval factsHomicide :=
  element_graph_correspondence
    (canonicalGraphModel factsHomicide s299) s299
    (canonicalGraphModel_satisfies factsHomicide s299) s299.elements

end Yuho.Tests
