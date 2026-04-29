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
import Yuho.Penalty
import Yuho.Range
import Yuho.Generator
import Yuho.Cross

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

/-! ## §6.5-v4 smoke tests — exercising `Penalty.lean`'s G8/G14
sentinel handling.

The two examples below check the unlimited-fine and unspecified-
caning leaves on plausible footprints. They confirm that:

  - A penalty `fine := 0 .. unlimited` admits any model that
    respects the lower bound, regardless of what the model's
    `fine_hi` claims (or whether it claims unlimited itself).
  - A penalty `caning := 0 .. unspecified` admits the same
    family of models on the caning axis.
-/

/-- s299 / s300 carry unlimited fines on the murder-adjacent
penalty schema; this smoke test confirms `fineUnlimited 0` admits
a model that supplies a bounded numeric range. -/
example :
    (Penalty.fineUnlimited 0).admits
      { fine_lo := 0, fine_hi := 50000, fine_unlimited := false : Footprint }
      = true := by
  native_decide

/-- Same penalty admits a model that itself claims unlimited. -/
example :
    (Penalty.fineUnlimited 0).admits
      { fine_lo := 100, fine_hi := 0, fine_unlimited := true : Footprint }
      = true := by
  native_decide

/-- A bounded-fine penalty rejects an unbounded model claim
above the cap. -/
example :
    (Penalty.fine 0 1000).admits
      { fine_lo := 0, fine_hi := 5000 : Footprint }
      = false := by
  native_decide

/-- s323 / s325 carry unspecified caning on some schemas; smoke
test the `caningUnspecified` admit on a bounded-strokes model. -/
example :
    (Penalty.caningUnspecified 0).admits
      { caning_lo := 0, caning_hi := 12,
        caning_unspecified := false : Footprint }
      = true := by
  native_decide

/-- Same penalty admits a model that itself claims unspecified. -/
example :
    (Penalty.caningUnspecified 0).admits
      { caning_lo := 6, caning_hi := 0,
        caning_unspecified := true : Footprint }
      = true := by
  native_decide

/-! ## §6.6-v5 smoke tests — exercising `Generator.lean`'s
canonical-model discharge of the oracle assumption. -/

/-- The verified generator's canonical SMTModel for s299 satisfies
the bicond bundle on every fact pattern. The conditional Lemmas
6.2 and 6.4 specialise to unconditional statements via this
witness. -/
example : (Generator.canonicalSMTModel s299 factsHomicide).satisfies s299 :=
  canonical_smt_satisfies s299 factsHomicide

/-- The verified generator's canonical GraphSMTModel for s299
satisfies the bicond bundle on every fact pattern. Discharges
Lemma 6.3's oracle premise on this fixture. -/
example : (Generator.canonicalGraphModel s299 factsHomicide).satisfies s299 :=
  canonical_graph_satisfies s299 factsHomicide

/-- Unconditional Lemma 6.2 specialised to s299: no oracle. -/
example :
    (Generator.canonicalSMTModel s299 factsHomicide).facts "death"
      = (Element.mk .actusReus "death" "").eval
        (Generator.canonicalSMTModel s299 factsHomicide).facts :=
  element_correspondence_unconditional s299
    { kind := .actusReus, name := "death", description := "" }
    factsHomicide

/-- Unconditional Lemma 6.3 specialised to s299: no oracle. -/
example :
    (Generator.canonicalGraphModel s299 factsHomicide).groupTruth s299.elements
      = s299.elements.eval (Generator.canonicalGraphModel s299 factsHomicide).facts :=
  element_graph_correspondence_unconditional s299 s299.elements factsHomicide

/-- Unconditional Lemma 6.4 specialised to the consent exception
on s299WithConsent: no oracle. -/
example :
    (Generator.canonicalSMTModel s299WithConsent factsHomicideWithConsent).excFires "consent"
      = decide ("consent" ∈ Exception.firedSet
          s299WithConsent.exceptions
          (Generator.canonicalSMTModel s299WithConsent factsHomicideWithConsent).facts) :=
  exception_correspondence_unconditional
    s299WithConsent "consent" factsHomicideWithConsent

/-- The verified spec emits exactly two leaf biconditionals for
s299's two-element conjunction (`death`, `intent`). -/
example :
    (Generator.encodeLeafBiconds s299 s299.elements).length = 2 := by
  native_decide

/-! ## §6.6-v5 smoke tests — canonical-model coverage across more
element-tree + exception-list shapes (s300, s378, s415).

s299 above exercises the simplest shape (allOf of two leaves, no
exceptions / one exception). The fixtures below extend coverage to:

  * **s300 — Murder.** allOf [actusReus, anyOf[mensRea×4]] + a
    five-element exception list (the §300 Exceptions 1–5 priority
    chain in the surface library).
  * **s378 — Theft.** Flat allOf of five leaves spanning all three
    kinds (mensRea, actusReus×2, circumstance×2) + one structural
    exception (claim-of-right).
  * **s415 — Cheating.** allOf with a nested anyOf
    [actusReus, anyOf[mensRea×2], actusReus, circumstance] —
    different nesting depth than s300.

For each shape we check:
  * `elementsSatisfied` and `convicts` on a witness fact pattern
    (operational evaluator green on a real fixture);
  * `canonicalSMTModel` / `canonicalGraphModel` satisfy the bicond
    bundle (the v5 unconditional discharge holds across shapes);
  * `encodeLeafBiconds` emits the expected number of leaves for
    each shape (mirrors the Python generator's atom-emit count).
-/

/-! ### s300 — Murder. -/

/-- s300: allOf [actusReus death, anyOf [intent1..intent4]]. -/
def s300 : Statute :=
  { section_number := "300"
    title := "Murder"
    elements :=
      .allOf [
        .leaf { kind := .actusReus, name := "death", description := "" },
        .anyOf [
          .leaf { kind := .mensRea, name := "intent_to_kill",       description := "" },
          .leaf { kind := .mensRea, name := "intent_likely_fatal",  description := "" },
          .leaf { kind := .mensRea, name := "intent_sufficient",    description := "" },
          .leaf { kind := .mensRea, name := "knowledge_imminent",   description := "" }
        ]
      ]
    exceptions := [
      { label := "provocation",    guard := fun F => F "exc_provocation",    defeats := [] },
      { label := "privateDefence", guard := fun F => F "exc_privateDefence", defeats := [] },
      { label := "publicServant",  guard := fun F => F "exc_publicServant",  defeats := [] },
      { label := "suddenFight",    guard := fun F => F "exc_suddenFight",    defeats := [] },
      { label := "consent",        guard := fun F => F "exc_consent",        defeats := [] }
    ]
  }

/-- Witness facts: limb (a) intent + actus death, no exception
fires. -/
def factsMurder : Facts :=
  Facts.fromList [("death", true), ("intent_to_kill", true)]

example : s300.elementsSatisfied factsMurder = true := by
  native_decide

example : s300.convicts factsMurder = true := by
  native_decide

/-- Same fact pattern with provocation exception → no conviction. -/
def factsMurderWithProvocation : Facts :=
  Facts.fromList
    [("death", true), ("intent_to_kill", true), ("exc_provocation", true)]

example : s300.convicts factsMurderWithProvocation = false := by
  native_decide

/-- Canonical SMTModel discharge on s300. -/
example :
    (Generator.canonicalSMTModel s300 factsMurder).satisfies s300 :=
  canonical_smt_satisfies s300 factsMurder

/-- Canonical GraphSMTModel discharge on s300. -/
example :
    (Generator.canonicalGraphModel s300 factsMurder).satisfies s300 :=
  canonical_graph_satisfies s300 factsMurder

/-- s300 carries one actus + four mens leaves under the nested
shape; encoder emits five leaf biconditionals. -/
example :
    (Generator.encodeLeafBiconds s300 s300.elements).length = 5 := by
  native_decide

/-! ### s378 — Theft. Flat five-leaf allOf, mixed kinds. -/

/-- s378: allOf [mensRea intention, actusReus taking,
circumstance possession, circumstance consent, actusReus movement]. -/
def s378 : Statute :=
  { section_number := "378"
    title := "Theft"
    elements :=
      .allOf [
        .leaf { kind := .mensRea,      name := "intention",  description := "" },
        .leaf { kind := .actusReus,    name := "taking",     description := "" },
        .leaf { kind := .circumstance, name := "possession", description := "" },
        .leaf { kind := .circumstance, name := "consent",    description := "" },
        .leaf { kind := .actusReus,    name := "movement",   description := "" }
      ]
    exceptions := [
      { label := "claimOfRight", guard := fun F => F "exc_claimOfRight", defeats := [] }
    ]
  }

/-- Witness: all five fact keys true, no exception. -/
def factsTheft : Facts :=
  Facts.fromList
    [("intention", true), ("taking", true), ("possession", true),
     ("consent", true), ("movement", true)]

example : s378.elementsSatisfied factsTheft = true := by
  native_decide

example : s378.convicts factsTheft = true := by
  native_decide

/-- Missing `movement` (the Explanation-3 movement element) →
elements not satisfied. -/
def factsTheftNoMovement : Facts :=
  Facts.fromList
    [("intention", true), ("taking", true), ("possession", true),
     ("consent", true)]

example : s378.elementsSatisfied factsTheftNoMovement = false := by
  native_decide

example : s378.convicts factsTheftNoMovement = false := by
  native_decide

/-- Claim-of-right exception fires on full elements → no
conviction. -/
def factsTheftClaimOfRight : Facts :=
  Facts.fromList
    [("intention", true), ("taking", true), ("possession", true),
     ("consent", true), ("movement", true), ("exc_claimOfRight", true)]

example : s378.convicts factsTheftClaimOfRight = false := by
  native_decide

/-- Canonical SMTModel discharge on s378. -/
example :
    (Generator.canonicalSMTModel s378 factsTheft).satisfies s378 :=
  canonical_smt_satisfies s378 factsTheft

/-- Canonical GraphSMTModel discharge on s378. -/
example :
    (Generator.canonicalGraphModel s378 factsTheft).satisfies s378 :=
  canonical_graph_satisfies s378 factsTheft

/-- Five flat leaves → five biconditionals. -/
example :
    (Generator.encodeLeafBiconds s378 s378.elements).length = 5 := by
  native_decide

/-! ### s415 — Cheating. allOf with a nested anyOf at non-final
position (different shape than s300). -/

/-- s415: allOf [actus deception, anyOf [mens fraud, mens dish],
actus inducement, circ harm]. -/
def s415 : Statute :=
  { section_number := "415"
    title := "Cheating"
    elements :=
      .allOf [
        .leaf { kind := .actusReus, name := "deception", description := "" },
        .anyOf [
          .leaf { kind := .mensRea, name := "fraudulent", description := "" },
          .leaf { kind := .mensRea, name := "dishonest",  description := "" }
        ],
        .leaf { kind := .actusReus,    name := "inducement", description := "" },
        .leaf { kind := .circumstance, name := "harm",       description := "" }
      ]
    exceptions := []
  }

/-- Witness: dishonest-limb cheating. -/
def factsCheating : Facts :=
  Facts.fromList
    [("deception", true), ("dishonest", true),
     ("inducement", true), ("harm", true)]

example : s415.elementsSatisfied factsCheating = true := by
  native_decide

example : s415.convicts factsCheating = true := by
  native_decide

/-- Neither limb of the anyOf satisfied → elements fail. -/
def factsCheatingNeitherLimb : Facts :=
  Facts.fromList
    [("deception", true), ("inducement", true), ("harm", true)]

example : s415.elementsSatisfied factsCheatingNeitherLimb = false := by
  native_decide

/-- Canonical SMTModel discharge on s415. -/
example :
    (Generator.canonicalSMTModel s415 factsCheating).satisfies s415 :=
  canonical_smt_satisfies s415 factsCheating

/-- Canonical GraphSMTModel discharge on s415. -/
example :
    (Generator.canonicalGraphModel s415 factsCheating).satisfies s415 :=
  canonical_graph_satisfies s415 factsCheating

/-- s415: 1 actus + 2 mens (in anyOf) + 1 actus + 1 circ = 5
leaves. -/
example :
    (Generator.encodeLeafBiconds s415 s415.elements).length = 5 := by
  native_decide

/-! ## §6.5-v5 smoke tests — `Range.cumulativeJoin` /
`Range.orBothMeet` algebraic surface. -/

/-- A two-component cumulative range (fine ≤ 1000 AND caning ≤ 12)
admits a model that respects both axis caps. -/
example :
    (Range.cumulativeJoin [Penalty.fine 0 1000, Penalty.caning 0 12]).admits
      { fine_lo := 0, fine_hi := 500, caning_lo := 0, caning_hi := 6
        : Footprint }
      = true := by
  native_decide

/-- The same cumulative rejects a model that breaches one axis. -/
example :
    (Range.cumulativeJoin [Penalty.fine 0 1000, Penalty.caning 0 12]).admits
      { fine_lo := 0, fine_hi := 500, caning_lo := 0, caning_hi := 24
        : Footprint }
      = false := by
  native_decide

/-- An or-both range over (fine ≤ 1000) ⊔ (caning ≤ 12) admits any
model that satisfies either axis. -/
example :
    (Range.orBothMeet [Penalty.fine 0 1000, Penalty.caning 0 12]).admits
      { fine_lo := 0, fine_hi := 500, caning_lo := 0, caning_hi := 24
        : Footprint }
      = true := by
  native_decide

/-- Empty cumulative is vacuously admitted. -/
example :
    (Range.cumulativeJoin []).admits ({} : Footprint) = true := by
  native_decide

/-- Empty or-both admits nothing. -/
example :
    (Range.orBothMeet []).admits ({} : Footprint) = false := by
  native_decide

/-! ## §6.5-v6 smoke tests — `Penalty.wellFormed` predicate.

The well-formedness predicate decides each fixture's
sentinel-propagation + non-empty-orBoth invariant by
`native_decide` on the recursive Bool definition. Pairs each
shape from §6.5-v4 (bounded leaves, unbounded sentinels,
combinators) with an ill-formed counterpart to confirm the
predicate is non-vacuous. -/

/-- Bounded imprisonment leaf with coherent range is well-formed. -/
example : (Penalty.imprisonment 0 (3 * 365)).wellFormed = true := by
  native_decide

/-- Bounded imprisonment leaf with `lo > hi` is ill-formed. -/
example : (Penalty.imprisonment 100 50).wellFormed = false := by
  native_decide

/-- Unbounded fine sentinel (G8) is vacuously well-formed. -/
example : (Penalty.fineUnlimited 0).wellFormed = true := by
  native_decide

/-- Unspecified caning sentinel (G14) is vacuously well-formed. -/
example : (Penalty.caningUnspecified 0).wellFormed = true := by
  native_decide

/-- Death penalty leaf is well-formed. -/
example : Penalty.death.wellFormed = true := by
  native_decide

/-- Empty cumulative is vacuously well-formed (matches
`Range.cumulativeJoin_nil`'s vacuous-admittance behaviour). -/
example : (Penalty.cumulative []).wellFormed = true := by
  native_decide

/-- Empty or-both is ill-formed (matches `Range.orBothMeet_nil`'s
admits-nothing behaviour). -/
example : (Penalty.orBoth []).wellFormed = false := by
  native_decide

/-- Cumulative of two coherent leaves (mirrors a typical SG PC
imprisonment + fine penalty schema). -/
example :
    (Penalty.cumulative [Penalty.imprisonment 0 (3 * 365),
                         Penalty.fineUnlimited 0]).wellFormed = true := by
  native_decide

/-- Cumulative containing one ill-formed child is ill-formed. -/
example :
    (Penalty.cumulative [Penalty.imprisonment 100 50,
                         Penalty.fine 0 1000]).wellFormed = false := by
  native_decide

/-- Or-both of two coherent leaves is well-formed. -/
example :
    (Penalty.orBoth [Penalty.fine 0 1000,
                     Penalty.caning 0 12]).wellFormed = true := by
  native_decide

/-! ## §6.6-v6 smoke tests — `Generator.canonicalPenaltyModel`
constructive discharge of the §6.5 oracle.

The v6 layer extends the v5 discharge (Lemmas 6.2 / 6.3 / 6.4)
to Lemma 6.5 (penalty layer). Each smoke test exercises one
shape (leaf, leaf with sentinel, leaf with user-supplied
footprint). The arbitrary-`Penalty` discharge is via the
`canonicalPenaltyModel` constructor with a user-supplied
witness; the leaf-shape constructors below need no witness. -/

/-- Canonical witness for `Penalty.imprisonment 0 1095`
(s378-style three-year imprisonment cap). -/
example :
    (Penalty.imprisonment 0 1095).admits
      (Generator.canonicalFootprintImprisonment 0 1095) = true := by
  exact canonicalFootprintImprisonment_admits 0 1095 (by decide)

/-- Canonical witness for `Penalty.fineUnlimited 0` (the s378
unlimited-fine schema). -/
example :
    (Penalty.fineUnlimited 0).admits
      (Generator.canonicalFootprintFineUnlimited 0) = true :=
  canonicalFootprintFineUnlimited_admits 0

/-- Canonical witness for `Penalty.death` (the s302 murder
sentence). -/
example :
    Penalty.death.admits Generator.canonicalFootprintDeath = true :=
  canonicalFootprintDeath_admits

/-- The canonical penalty model satisfies the v5 satisfies
bundle for s299 + a witness imprisonment penalty. -/
example :
    (Generator.canonicalPenaltyModel s299 factsHomicide
        (Generator.canonicalFootprintImprisonment 0 3650)).satisfies
      s299 (Penalty.imprisonment 0 3650) :=
  canonical_penalty_satisfies s299 factsHomicide
    (Penalty.imprisonment 0 3650)
    (Generator.canonicalFootprintImprisonment 0 3650)
    (canonicalFootprintImprisonment_admits 0 3650 (by decide))

/-- The canonical penalty model satisfies the v6 strengthened
bundle (`satisfiesWF`) for s299 + a wellFormed witness
imprisonment penalty. -/
example :
    (Generator.canonicalPenaltyModel s299 factsHomicide
        (Generator.canonicalFootprintImprisonment 0 3650)).satisfiesWF
      s299 (Penalty.imprisonment 0 3650) :=
  canonical_penalty_satisfies_wf s299 factsHomicide
    (Penalty.imprisonment 0 3650)
    (Generator.canonicalFootprintImprisonment 0 3650)
    (canonicalFootprintImprisonment_admits 0 3650 (by decide))
    (by native_decide)

/-- Unconditional Lemma 6.5 specialised to s378 + an unlimited
fine: no oracle assumption, no user-supplied witness beyond
the leaf-shape canonical constructor. -/
example :
    (Penalty.fineUnlimited 0).admits
      (Generator.canonicalPenaltyModel s378 factsTheft
        (Generator.canonicalFootprintFineUnlimited 0)).footprint = true :=
  penalty_correspondence_unconditional s378 factsTheft
    (Penalty.fineUnlimited 0)
    (Generator.canonicalFootprintFineUnlimited 0)
    (canonicalFootprintFineUnlimited_admits 0)
    (by native_decide)

/-- Unconditional Lemma 6.5 on s300 + death penalty (the
s302-attached sentence): no oracle, no user witness. -/
example :
    Penalty.death.admits
      (Generator.canonicalPenaltyModel s300 factsMurder
        Generator.canonicalFootprintDeath).footprint = true :=
  penalty_correspondence_unconditional s300 factsMurder
    Penalty.death
    Generator.canonicalFootprintDeath
    canonicalFootprintDeath_admits
    (by native_decide)

/-- Unconditional Lemma 6.5 on s415 + a cumulative
imprisonment + fine penalty (user-supplied witness for the
combinator shape). -/
example :
    (Penalty.cumulative [Penalty.imprisonment 0 (10 * 365),
                         Penalty.fineUnlimited 0]).admits
      (Generator.canonicalPenaltyModel s415 factsCheating
        { imp_lo := 0, imp_hi := 10 * 365,
          fine_lo := 0, fine_hi := 0,
          fine_unlimited := true : Footprint }).footprint = true :=
  penalty_correspondence_unconditional s415 factsCheating
    (Penalty.cumulative [Penalty.imprisonment 0 (10 * 365),
                         Penalty.fineUnlimited 0])
    { imp_lo := 0, imp_hi := 10 * 365,
      fine_lo := 0, fine_hi := 0,
      fine_unlimited := true : Footprint }
    (by native_decide)
    (by native_decide)

/-! ## §6-cross-v4 smoke tests — `Generator.canonicalCrossModel`
constructive discharge of the cross-section bundle.

The v4 refactor replaces v3's raw-label `excFires` bicond
with a qualified-atom version
(`<sX>_exc_<label>_fires`) and exhibits a constructive
canonical model. The singleton-module discharge below
exercises the bundle on the `s299WithConsent` fixture. -/

/-- The canonical cross model for the singleton module
`⟨[s299WithConsent]⟩` satisfies the v4 bundle. The fixture
has exactly one exception (`consent`); the singleton
discharge applies. -/
example :
    (Generator.canonicalCrossModel ⟨[s299WithConsent]⟩
        factsHomicideWithConsent).satisfies ⟨[s299WithConsent]⟩ :=
  canonical_cross_satisfies_singleton_singleton_exc
    s299WithConsent
    { label := "consent"
      guard := fun F => F "consent"
      defeats := [] }
    factsHomicideWithConsent
    rfl

/-- The canonical cross model's `convicts` field returns the
operational `Statute.convicts` for the in-module section. -/
example :
    (Generator.canonicalCrossModel ⟨[s299WithConsent]⟩
        factsHomicideWithConsent).convicts "299"
      = s299WithConsent.convicts factsHomicideWithConsent := by
  native_decide

/-- The qualified-atom `excFires` returns the operational
`firedSet` membership for the in-module exception. The v4
fix: this would have been raw label "consent" under v3,
which collides with any other statute carrying a "consent"
exception in the same module. -/
example :
    (Generator.canonicalCrossModel ⟨[s299WithConsent]⟩
        factsHomicideWithConsent).excFires
      (Generator.exceptionAtomName s299WithConsent
        { label := "consent"
          guard := fun F => F "consent"
          defeats := [] : Exception })
      = decide ("consent" ∈ Exception.firedSet
          s299WithConsent.exceptions
          factsHomicideWithConsent) := by
  native_decide

end Yuho.Tests
