/- Independently executable abstract model: fixed manually specified cases. -/
import Yuho.CoreYuho.ScopedDefinitions
open Yuho.CoreYuho
open Yuho.CoreYuho.TypedFinite
open Yuho.CoreYuho.ScopedDefinitions

def fixtureOccurrence : Occurrence :=
  ⟨⟨"synthetic", "1.0.0", "permission", "retained.yh"⟩, "explicit-use", "selected-component",
   ⟨"actor", "event", none, none, "selected", []⟩, [⟨"actor", "person"⟩], "scenario"⟩

def statusName : Status → String
  | .satisfied => "satisfied"
  | .notSatisfied => "not_satisfied"
  | .unresolved => "unresolved"

def main : IO Unit := do
  let states : List Status := [.satisfied, .notSatisfied, .unresolved]
  for a in states do
    for b in states do
      let env : AssessmentEnvironment := fun _ p _ => if p == "first" then a else b
      let body := Body.conjunction (.atom "first" [⟨"actor", "person"⟩])
        (.negation (.atom "second" [⟨"actor", "person"⟩]))
      IO.println (statusName (evaluate env fixtureOccurrence body))
