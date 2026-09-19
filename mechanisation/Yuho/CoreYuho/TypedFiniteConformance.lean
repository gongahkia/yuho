import Yuho.CoreYuho.TypedFinite

namespace Yuho.CoreYuho.TypedFinite.Conformance

open Yuho.CoreYuho
open Yuho.CoreYuho.TypedFinite

inductive QuantifierOperation where | forall | exists deriving Repr

inductive Vector where
  | negation (identifier : Identifier) (status : Status)
  | quantifier (identifier : Identifier) (operation : QuantifierOperation)
      (values : List Status)
  | cardinality (identifier : Identifier) (kind : CardinalityKind)
      (threshold : Nat) (values : List Status)
  | comparison (identifier : Identifier) (operation : Comparison)
      (left right : ScalarValue)
  | priority (identifier : Identifier) (higher lower : RuleResult) (ordered : Bool)
  | substitution (identifier binder entity : Identifier) (term : TypedTerm)
  | isolation (identifier selected : Identifier)
      (assignments : List (Identifier × Status))
  deriving Repr

def truthName : Status → String
  | .satisfied => "satisfied"
  | .notSatisfied => "not_satisfied"
  | .unresolved => "unresolved"

def propositionStateName : PropositionState → String
  | .established => "established"
  | .defeated => "defeated"
  | .conflict => "conflict"
  | .unresolved => "unresolved"
  | .notEstablished => "not_established"

def lookupStatus : List (Identifier × Status) → Identifier → Option Status
  | [], _ => none
  | (identifier,status) :: rest, selected =>
      if identifier = selected then some status else lookupStatus rest selected

def evaluateVector : Vector → Except String (Identifier × String)
  | .negation identifier status => pure (identifier,truthName (negateStatus status))
  | .quantifier identifier operation values =>
      pure (identifier,truthName (match operation with
        | .forall => finiteForall values | .exists => finiteExists values))
  | .cardinality identifier kind threshold values =>
      pure (identifier,truthName (cardinalityStatus kind threshold values))
  | .comparison identifier operation left right =>
      pure (identifier,truthName (compareScalar operation left right))
  | .priority identifier higher lower ordered =>
      let edge : Priority := { higher := higher.identifier, lower := lower.identifier }
      let priority := if ordered then some edge else none
      let result := resolveCompetingRules higher lower priority
      pure (identifier,truthName result.1 ++ "/" ++ propositionStateName result.2)
  | .substitution identifier binder entity term =>
      let replacement : TypedTerm := { identifier := entity, typeName := term.typeName }
      pure (identifier,(substituteTerm
        { identifier := binder, typeName := term.typeName } replacement term).identifier)
  | .isolation identifier selected assignments => match lookupStatus assignments selected with
      | some status => pure (identifier,truthName status)
      | none => throw ("selected assignment missing: " ++ selected)

def escapeJson (value : String) : String :=
  value.foldl (fun output character => output ++ match character with
    | '"' => "\\\"" | '\\' => "\\\\" | '\n' => "\\n"
    | '\r' => "\\r" | '\t' => "\\t" | other => String.singleton other) ""

def encodeRow (row : Identifier × String) : String :=
  "{\"id\":\"" ++ escapeJson row.1 ++ "\",\"result\":\"" ++
    escapeJson row.2 ++ "\"}"

def evaluateVectors (vectors : List Vector) : Except String String := do
  let rows ← vectors.mapM evaluateVector
  pure ("{\"results\":[" ++ String.intercalate "," (rows.map encodeRow) ++
    "],\"schema\":\"yuho.core-conformance-results-v0.2\"}")

end Yuho.CoreYuho.TypedFinite.Conformance
