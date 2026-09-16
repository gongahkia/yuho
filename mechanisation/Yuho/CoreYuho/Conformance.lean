import Yuho.CoreYuho.Theorems

namespace Yuho.CoreYuho.Conformance

open Yuho.CoreYuho

inductive AggregateOperation where
  | all
  | any
  | branch
  | guard
  deriving Repr

structure ScopeAssignment where
  key : ScopedKey
  input : Identifier
  status : Status
  deriving Repr

structure AllegationVector where
  identifier : Identifier
  requirement : Requirement
  assignments : List (Identifier × Status)
  deriving Repr

inductive Vector where
  | aggregate (identifier : Identifier) (operation : AggregateOperation)
      (values : List Status)
  | requirement (identifier kind : Identifier) (expression : Requirement)
      (assignments : List (Identifier × Status))
  | exception (identifier : Identifier) (ordinary : Status)
      (guards : List Status)
  | presumption (identifier : Identifier) (trigger rebuttal : Status)
  | scope (identifier : Identifier) (selected : ScopedKey) (input : Identifier)
      (assignments : List ScopeAssignment)
  | caseAnalysis (identifier : Identifier) (allegations : List AllegationVector)
  | temporal (identifier : Identifier) (date : Nat)
      (intervals : List TemporalInterval)
  deriving Repr

def lookupStatus : List (Identifier × Status) → Identifier → Option Status
  | [], _ => none
  | (identifier, status) :: rest, query =>
      if identifier = query then some status else lookupStatus rest query

def truthName : Status → String
  | .satisfied => "satisfied"
  | .notSatisfied => "not_satisfied"
  | .unresolved => "unresolved"

def stateName : PresumptionState → String
  | .active => "active"
  | .inactive => "inactive"
  | .rebutted => "rebutted"
  | .unresolved => "unresolved"

def guardedListStatus (guards : List Status) : Status :=
  match anyStatus guards with
  | .satisfied => .notSatisfied
  | .notSatisfied => .satisfied
  | .unresolved => .unresolved

def evaluateGuardedBranch (ordinary : Status) (guards : List Status) : Status :=
  match ordinary with
  | .satisfied => guardedListStatus guards
  | .notSatisfied => .notSatisfied
  | .unresolved => .unresolved

def evaluateScope
    (selected : ScopedKey) (input : Identifier)
    (assignments : List ScopeAssignment) : Option Status :=
  match assignments with
  | [] => none
  | assignment :: rest =>
      if assignment.key = selected ∧ assignment.input = input
        then some assignment.status
        else evaluateScope selected input rest

def joinResults : List (Identifier × Status) → String
  | [] => ""
  | [(identifier, status)] => identifier ++ "=" ++ truthName status
  | (identifier, status) :: rest =>
      identifier ++ "=" ++ truthName status ++ ";" ++ joinResults rest

def requireSome {alpha : Type} (issue : String) : Option alpha → Except String alpha
  | some value => pure value
  | none => throw issue

def evaluateAllegations : List AllegationVector → Except String String
  | [] => pure ""
  | allegations => do
      let results ← allegations.mapM fun allegation => do
        let status ← requireSome
          ("missing primitive in allegation " ++ allegation.identifier)
          (allegation.requirement.evaluate (lookupStatus allegation.assignments))
        pure (allegation.identifier, status)
      pure (joinResults results)

def evaluateVector : Vector → Except String (Identifier × String)
  | .aggregate identifier operation values =>
      let status := match operation with
        | .all => allStatus values
        | .any => anyStatus values
        | .branch => anyStatus values
        | .guard => guardedListStatus values
      pure (identifier, truthName status)
  | .requirement identifier _ expression assignments => do
      let status ← requireSome ("missing primitive in " ++ identifier)
        (expression.evaluate (lookupStatus assignments))
      pure (identifier, truthName status)
  | .exception identifier ordinary guards =>
      pure (identifier, truthName (evaluateGuardedBranch ordinary guards))
  | .presumption identifier trigger rebuttal =>
      pure (identifier, stateName (derivePresumption trigger rebuttal))
  | .scope identifier selected input assignments => do
      let status ← requireSome ("missing selected scoped input in " ++ identifier)
        (evaluateScope selected input assignments)
      pure (identifier, truthName status)
  | .caseAnalysis identifier allegations => do
      let result ← evaluateAllegations allegations
      pure (identifier, result)
  | .temporal identifier date intervals =>
      let selectedIntervals := intervals.filter (·.contains date)
      let result := match selectedIntervals with
        | [selected] => "selected:" ++ selected.expression
        | [] => "gap"
        | _ => "overlap"
      pure (identifier, result)

def escapeJson (value : String) : String :=
  value.foldl (fun output character => output ++ match character with
    | '"' => "\\\""
    | '\\' => "\\\\"
    | '\n' => "\\n"
    | '\r' => "\\r"
    | '\t' => "\\t"
    | other => String.singleton other) ""

def encodeRow (row : Identifier × String) : String :=
  "{\"id\":\"" ++ escapeJson row.1 ++ "\",\"result\":\"" ++
    escapeJson row.2 ++ "\"}"

def encodeResults (rows : List (Identifier × String)) : String :=
  "{\"results\":[" ++ String.intercalate "," (rows.map encodeRow) ++
    "],\"schema\":\"yuho.core-conformance-results-v0.1\"}"

def evaluateVectors (vectors : List Vector) : Except String String := do
  let results ← vectors.mapM evaluateVector
  pure (encodeResults results)

end Yuho.CoreYuho.Conformance
