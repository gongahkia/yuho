import Yuho.CoreYuho.ReleaseV03

namespace Yuho.CoreYuho.ReleaseV03.Conformance

open Yuho.CoreYuho
open Yuho.CoreYuho.TypedFinite
open Yuho.CoreYuho.ReleaseV03

inductive Vector where
  | normApplicability (identifier : Identifier) (status : Status)
  | normConflictVector (identifier : Identifier) (left right : NormModality)
  | sanctionBounds (identifier : Identifier) (minimum maximum : SanctionBound)
  | sanctionShapeVector (identifier : Identifier) (sanction : CandidateSanction)
  | responsibilityRoute (identifier : Identifier) (status : Status)
  | missingRoute (identifier : Identifier)
  | priority (identifier : Identifier) (higher lower : RuleResult) (ordered : Bool)

def statusName : Status → String
  | .satisfied => "satisfied"
  | .notSatisfied => "not_satisfied"
  | .unresolved => "unresolved"

def propositionStateName : PropositionState → String
  | .established => "established"
  | .defeated => "defeated"
  | .conflict => "conflict"
  | .unresolved => "unresolved"
  | .notEstablished => "not_established"

def evaluateVector : Vector → Identifier × String
  | .normApplicability identifier status => (identifier,statusName status)
  | .normConflictVector identifier left right =>
      (identifier,if normConflict left right then "true" else "false")
  | .sanctionBounds identifier minimum maximum =>
      (identifier,if validBounds minimum maximum then "valid" else "invalid")
  | .sanctionShapeVector identifier sanction => (identifier,sanctionShape sanction)
  | .responsibilityRoute identifier status => (identifier,statusName status)
  | .missingRoute identifier => (identifier,statusName (routeLookup [] "p:target"))
  | .priority identifier higher lower ordered =>
      let edge : Priority := { higher := higher.identifier, lower := lower.identifier }
      let result := resolveCompetingRules higher lower (if ordered then some edge else none)
      (identifier,statusName result.1 ++ "/" ++ propositionStateName result.2)

def escapeJson (value : String) : String :=
  value.foldl (fun output character => output ++ match character with
    | '"' => "\\\"" | '\\' => "\\\\" | '\n' => "\\n"
    | '\r' => "\\r" | '\t' => "\\t" | other => String.singleton other) ""

def encodeRow (row : Identifier × String) : String :=
  "{\"id\":\"" ++ escapeJson row.1 ++ "\",\"result\":\"" ++
    escapeJson row.2 ++ "\"}"

def evaluateVectors (vectors : List Vector) : String :=
  let rows := vectors.map (encodeRow ∘ evaluateVector)
  "{\"results\":[" ++ String.intercalate "," rows ++
    "],\"schema\":\"yuho.core-conformance-results-v0.3\"}"

end Yuho.CoreYuho.ReleaseV03.Conformance
