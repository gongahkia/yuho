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
  unfold Statute.elementsSatisfied
  unfold ElementGroup.eval Element.eval
  decide

example : s299.convicts factsHomicide = true := by
  unfold Statute.convicts
  decide

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
  decide

example : s299WithConsent.convicts factsHomicideWithConsent = false := by
  -- Elements satisfied but consent exception fires → no conviction.
  decide

/-- Element correspondence holds trivially on this concrete case. -/
example (m : SMTModel) :
    m.facts "death" = (Element.mk .actusReus "death" "").eval m.facts := by
  exact element_correspondence m { kind := .actusReus, name := "death", description := "" }

end Yuho.Tests
