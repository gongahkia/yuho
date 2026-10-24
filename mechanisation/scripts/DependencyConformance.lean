import Yuho.CoreYuho.DependencyPlan
open Yuho.CoreYuho
open Yuho.CoreYuho.DependencyPlan

def rows : List (String × Evidence) :=
  [("T", .expression .satisfied), ("F", .expression .notSatisfied),
   ("U", .expression .unresolved), ("P-established", .proposition .established),
   ("P-defeated", .proposition .defeated), ("P-not-established", .proposition .notEstablished),
   ("P-unresolved", .proposition .unresolved), ("P-conflict", .proposition .conflict),
   ("unavailable", .unavailable "sealed finite engine model")]

def valueText : Option Status → String
  | some .satisfied => "satisfied"
  | some .notSatisfied => "not_satisfied"
  | some .unresolved => "unresolved"
  | none => "not_evaluated"
def availabilityText : Availability → String
  | .eligible => "eligible"
  | .ineligible => "ineligible"
  | .unresolved _ => "unresolved"
  | .notEvaluated _ => "not_evaluated"

def rowJson (row : String × Evidence) : String :=
  let c := convert row.2
  "{\"id\":\"" ++ row.1 ++ "\",\"value\":\"" ++ valueText c.value ++
    "\",\"conflict\":" ++ (if c.conflictOrigin then "true" else "false") ++
    ",\"availability\":\"" ++ availabilityText (availability c) ++ "\"}"

def main : IO Unit := IO.println ("[" ++ String.intercalate "," (rows.map rowJson) ++ "]")
