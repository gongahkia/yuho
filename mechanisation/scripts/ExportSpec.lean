/-
ExportSpec.lean — emit the verified `Generator.encodeStatute`
biconditional list and Lean expected verdict rows as JSON for smoke
fixtures.

Driven by `scripts/verify_structural_diff.py` (Python). The Python
harness invokes `lake env lean --run scripts/ExportSpec.lean` from
`mechanisation/`, captures stdout, parses the JSON object, and
diffs the entries against what
`src/yuho/verify/z3_solver.py::Z3Generator
._generate_statute_constraints` actually emits on parallel
fixtures.

The four hand-stitched fixtures (s299/s300/s378/s415) remain
inlined for backwards compatibility with the original PoC harness.
The full-corpus extension (524 sections) lives in
`Fixtures.lean` (auto-generated via
`mechanisation/scripts/generate_fixtures.py`); it is loaded only
when `--full` is passed on the command line so the smoke harness
stays fast.
-/

import Yuho
import «scripts».Fixtures

open Yuho

namespace Yuho.ExportSpec

/-! ## JSON serialisation for SMTFormula. -/

private def escape (s : String) : String :=
  s.foldl (init := "")
    (fun acc c =>
      acc ++
        match c with
        | '"'   => "\\\""
        | '\\'  => "\\\\"
        | '\n'  => "\\n"
        | _     => String.singleton c)

partial def formulaToJSON : SMTFormula → String
  | .var n     => "{\"kind\":\"var\",\"name\":\"" ++ escape n ++ "\"}"
  | .const b   => "{\"kind\":\"const\",\"value\":" ++ (if b then "true" else "false") ++ "}"
  | .not φ     => "{\"kind\":\"not\",\"arg\":" ++ formulaToJSON φ ++ "}"
  | .and φ ψ   =>
      "{\"kind\":\"and\",\"lhs\":" ++ formulaToJSON φ ++
      ",\"rhs\":" ++ formulaToJSON ψ ++ "}"
  | .or  φ ψ   =>
      "{\"kind\":\"or\",\"lhs\":" ++ formulaToJSON φ ++
      ",\"rhs\":" ++ formulaToJSON ψ ++ "}"
  | .iff φ ψ   =>
      "{\"kind\":\"iff\",\"lhs\":" ++ formulaToJSON φ ++
      ",\"rhs\":" ++ formulaToJSON ψ ++ "}"

def listToJSON (φs : List SMTFormula) : String :=
  let inner := String.intercalate "," (φs.map formulaToJSON)
  "[" ++ inner ++ "]"

/-! ## Smoke fixtures (mirror `Tests/Smoke.lean`). -/

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

def s300 : Statute :=
  { section_number := "300"
    title := "Murder"
    elements :=
      .allOf [
        .leaf { kind := .actusReus, name := "death", description := "" },
        .anyOf [
          .leaf { kind := .mensRea, name := "intent_to_kill",      description := "" },
          .leaf { kind := .mensRea, name := "intent_likely_fatal", description := "" },
          .leaf { kind := .mensRea, name := "intent_sufficient",   description := "" },
          .leaf { kind := .mensRea, name := "knowledge_imminent",  description := "" }
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

def smokeFixtures : List (String × Statute) :=
  [("s299", s299), ("s300", s300), ("s378", s378), ("s415", s415)]

/-! ## Expected verdict fixtures. -/

structure VerdictFixture where
  name : String
  statuteName : String
  statute : Statute
  factsName : String
  factsPairs : List (String × Bool)

def VerdictFixture.facts (vf : VerdictFixture) : Facts :=
  Facts.fromList vf.factsPairs

def boolJSON (b : Bool) : String :=
  if b then "true" else "false"

def factPairJSON (p : String × Bool) : String :=
  "\"" ++ escape p.fst ++ "\":" ++ boolJSON p.snd

def factsJSON (pairs : List (String × Bool)) : String :=
  "{" ++ String.intercalate "," (pairs.map factPairJSON) ++ "}"

def verdictFixtureJSON (vf : VerdictFixture) : String :=
  "{"
    ++ "\"name\":\"" ++ escape vf.name ++ "\","
    ++ "\"statute\":\"" ++ escape vf.statuteName ++ "\","
    ++ "\"facts\":\"" ++ escape vf.factsName ++ "\","
    ++ "\"factValues\":" ++ factsJSON vf.factsPairs ++ ","
    ++ "\"expected\":" ++ boolJSON (vf.statute.convicts vf.facts)
    ++ "}"

def verdictsJSON (fixtures : List VerdictFixture) : String :=
  "[" ++ String.intercalate "," (fixtures.map verdictFixtureJSON) ++ "]"

def verdictFixtures : List VerdictFixture :=
  [
    {
      name := "s299_true"
      statuteName := "s299"
      statute := s299
      factsName := "factsHomicide"
      factsPairs := [("death", true), ("intent", true)]
    },
    {
      name := "s299_missing_intent"
      statuteName := "s299"
      statute := s299
      factsName := "factsHomicideMissingIntent"
      factsPairs := [("death", true)]
    },
    {
      name := "s300_true"
      statuteName := "s300"
      statute := s300
      factsName := "factsMurderIntent"
      factsPairs := [("death", true), ("intent_to_kill", true)]
    },
    {
      name := "s300_consent_exception"
      statuteName := "s300"
      statute := s300
      factsName := "factsMurderConsent"
      factsPairs := [("death", true), ("intent_to_kill", true), ("exc_consent", true)]
    },
    {
      name := "s378_true"
      statuteName := "s378"
      statute := s378
      factsName := "factsTheft"
      factsPairs := [
        ("intention", true), ("taking", true), ("possession", true),
        ("consent", true), ("movement", true)
      ]
    },
    {
      name := "s378_claim_of_right_exception"
      statuteName := "s378"
      statute := s378
      factsName := "factsTheftClaimOfRight"
      factsPairs := [
        ("intention", true), ("taking", true), ("possession", true),
        ("consent", true), ("movement", true), ("exc_claimOfRight", true)
      ]
    },
    {
      name := "s415_true"
      statuteName := "s415"
      statute := s415
      factsName := "factsCheatingFraudulent"
      factsPairs := [
        ("deception", true), ("fraudulent", true),
        ("inducement", true), ("harm", true)
      ]
    },
    {
      name := "s415_missing_mens_rea"
      statuteName := "s415"
      statute := s415
      factsName := "factsCheatingNoMensRea"
      factsPairs := [("deception", true), ("inducement", true), ("harm", true)]
    },
    {
      name := "s204_flat_true"
      statuteName := "s204"
      statute := Yuho.Fixtures.s204
      factsName := "factsS204Flat"
      factsPairs := [("prohibited_handling", true)]
    },
    {
      name := "s204_flat_missing"
      statuteName := "s204"
      statute := Yuho.Fixtures.s204
      factsName := "factsS204Missing"
      factsPairs := []
    },
    {
      name := "s101_nested_attempt_branch"
      statuteName := "s101"
      statute := Yuho.Fixtures.s101
      factsName := "factsS101AttemptBranch"
      factsPairs := [
        ("reasonable_belief_of_danger_to_body", true),
        ("attempt_to_commit_offence", true),
        ("belief_continues_at_time_of_act", true)
      ]
    },
    {
      name := "s101_nested_missing_any_branch"
      statuteName := "s101"
      statute := Yuho.Fixtures.s101
      factsName := "factsS101MissingAnyBranch"
      factsPairs := [
        ("reasonable_belief_of_danger_to_body", true),
        ("belief_continues_at_time_of_act", true)
      ]
    },
    {
      name := "s107_any_instigation"
      statuteName := "s107"
      statute := Yuho.Fixtures.s107
      factsName := "factsS107Instigation"
      factsPairs := [("instigation", true)]
    },
    {
      name := "s107_any_conspiracy_branch"
      statuteName := "s107"
      statute := Yuho.Fixtures.s107
      factsName := "factsS107ConspiracyBranch"
      factsPairs := [
        ("conspiracy", true),
        ("act_or_illegal_omission_in_pursuance", true),
        ("in_order_to_do_thing", true)
      ]
    },
    {
      name := "s107_exception_defeats"
      statuteName := "s107"
      statute := Yuho.Fixtures.s107
      factsName := "factsS107GeneralDefence"
      factsPairs := [("instigation", true), ("exc_general_defence_s79", true)]
    }
  ]

mutual
def leafNames : ElementGroup → List String
  | .leaf e => [e.name]
  | .allOf gs => leafNamesList gs
  | .anyOf gs => leafNamesList gs

def leafNamesList : List ElementGroup → List String
  | [] => []
  | g :: rest => leafNames g ++ leafNamesList rest
end

def containsString (needle : String) : List String → Bool
  | [] => false
  | x :: rest => if x == needle then true else containsString needle rest

def uniqueStringsLoop : List String → List String → List String
  | [], acc => acc
  | x :: rest, acc =>
      uniqueStringsLoop rest (if containsString x acc then acc else acc ++ [x])

def uniqueStrings (xs : List String) : List String :=
  uniqueStringsLoop xs []

def allTrueFacts (s : Statute) : List (String × Bool) :=
  (uniqueStrings (leafNames s.elements)).map (fun name => (name, true))

def namePairsWith (first : String) : List String → List (String × String)
  | [] => []
  | second :: rest => (first, second) :: namePairsWith first rest

def namePairs : List String → List (String × String)
  | [] => []
  | _ :: [] => []
  | first :: rest => namePairsWith first rest ++ namePairs rest

structure NameTriple where
  first : String
  second : String
  third : String

def nameTriplesWithPair (first second : String) : List String → List NameTriple
  | [] => []
  | third :: rest =>
      { first := first, second := second, third := third } ::
        nameTriplesWithPair first second rest

def nameTriplesWithFirst (first : String) : List String → List NameTriple
  | [] => []
  | _ :: [] => []
  | second :: rest =>
      nameTriplesWithPair first second rest ++ nameTriplesWithFirst first rest

def nameTriples : List String → List NameTriple
  | [] => []
  | _ :: [] => []
  | _ :: _ :: [] => []
  | first :: rest => nameTriplesWithFirst first rest ++ nameTriples rest

def takeExactly : Nat → List String → Option (List String)
  | 0, _ => some []
  | _ + 1, [] => none
  | n + 1, first :: rest =>
      match takeExactly n rest with
      | some taken => some (first :: taken)
      | none => none

def joinedNamePieces : List String → String
  | [] => ""
  | first :: [] => first
  | first :: rest => first ++ "_" ++ joinedNamePieces rest

def concatNamePieces : List String → String
  | [] => ""
  | first :: rest => first ++ concatNamePieces rest

def alternatingFactsFrom (value : Bool) : List String → List (String × Bool)
  | [] => []
  | first :: rest => (first, value) :: alternatingFactsFrom (!value) rest

def pairFacts (pair : String × String) : List (String × Bool) :=
  [(pair.fst, true), (pair.snd, true)]

def tripleFacts (triple : NameTriple) : List (String × Bool) :=
  [(triple.first, true), (triple.second, true), (triple.third, true)]

def pairVerdictFixture (n : String) (s : Statute) (pair : String × String) :
    VerdictFixture :=
  {
    name := n ++ "_corpus_pair_" ++ pair.fst ++ "_" ++ pair.snd
    statuteName := n
    statute := s
    factsName := n ++ "Pair" ++ pair.fst ++ pair.snd
    factsPairs := pairFacts pair
  }

def tripleVerdictFixture (n : String) (s : Statute) (triple : NameTriple) :
    VerdictFixture :=
  {
    name := n ++ "_corpus_triple_" ++ triple.first ++ "_" ++ triple.second ++
      "_" ++ triple.third
    statuteName := n
    statute := s
    factsName := n ++ "Triple" ++ triple.first ++ triple.second ++ triple.third
    factsPairs := tripleFacts triple
  }

def mixedVerdictFixture (n : String) (s : Statute) (label : String)
    (names : List String) : VerdictFixture :=
  {
    name := n ++ "_corpus_mixed_" ++ label ++ "_" ++ joinedNamePieces names
    statuteName := n
    statute := s
    factsName := n ++ "Mixed" ++ label ++ concatNamePieces names
    factsPairs := alternatingFactsFrom true names
  }

def boundedMixedVerdictFixtures (n : String) (s : Statute)
    (names : List String) : List VerdictFixture :=
  let quad :=
    match takeExactly 4 names with
    | some selected => [mixedVerdictFixture n s "quad" selected]
    | none => []
  let quint :=
    match takeExactly 5 names with
    | some selected => [mixedVerdictFixture n s "quint" selected]
    | none => []
  quad ++ quint

def exceptionFactName (x : Exception) : String :=
  "exc_" ++ x.label

def exceptionVerdictFixture (n : String) (s : Statute) (x : Exception) :
    VerdictFixture :=
  {
    name := n ++ "_corpus_exception_" ++ x.label
    statuteName := n
    statute := s
    factsName := n ++ "Exception" ++ x.label
    factsPairs := allTrueFacts s ++ [(exceptionFactName x, true)]
  }

def corpusVerdictFixturesFor (fixture : String × Statute) : List VerdictFixture :=
  let n := fixture.fst
  let s := fixture.snd
  let names := uniqueStrings (leafNames s.elements)
  let firstOnly :=
    match names with
    | first :: _second :: _ =>
        [
          {
            name := n ++ "_corpus_first_only"
            statuteName := n
            statute := s
            factsName := n ++ "FirstOnly"
            factsPairs := [(first, true)]
          }
        ]
    | _ => []
  [
    {
      name := n ++ "_corpus_all_true"
      statuteName := n
      statute := s
      factsName := n ++ "AllTrue"
      factsPairs := allTrueFacts s
    },
    {
      name := n ++ "_corpus_empty"
      statuteName := n
      statute := s
      factsName := n ++ "Empty"
      factsPairs := []
    }
  ] ++ firstOnly
    ++ (namePairs names).map (pairVerdictFixture n s)
    ++ (nameTriples names).map (tripleVerdictFixture n s)
    ++ boundedMixedVerdictFixtures n s names
    ++ s.exceptions.map (exceptionVerdictFixture n s)

def isSmokeFixtureName (name : String) : Bool :=
  name == "s299" || name == "s300" || name == "s378" || name == "s415"

def corpusVerdictFixtures : List VerdictFixture :=
  (Yuho.Fixtures.fixtures.filter (fun fixture => !isSmokeFixtureName fixture.fst)).bind
    corpusVerdictFixturesFor

def allVerdictFixtures : List VerdictFixture :=
  verdictFixtures ++ corpusVerdictFixtures

/-! ## Penalty footprint fixtures. -/

structure PenaltyFootprintFixture where
  name : String
  penalty : Penalty
  footprint : Footprint

def natFieldJSON (name : String) (n : Nat) : String :=
  "\"" ++ name ++ "\":" ++ toString n

def boolFieldJSON (name : String) (b : Bool) : String :=
  "\"" ++ name ++ "\":" ++ boolJSON b

def footprintJSON (fp : Footprint) : String :=
  "{"
    ++ String.intercalate "," [
      natFieldJSON "imp_lo" fp.imp_lo,
      natFieldJSON "imp_hi" fp.imp_hi,
      natFieldJSON "fine_lo" fp.fine_lo,
      natFieldJSON "fine_hi" fp.fine_hi,
      boolFieldJSON "fine_unlimited" fp.fine_unlimited,
      natFieldJSON "caning_lo" fp.caning_lo,
      natFieldJSON "caning_hi" fp.caning_hi,
      boolFieldJSON "caning_unspecified" fp.caning_unspecified,
      boolFieldJSON "death" fp.death
    ]
    ++ "}"

def penaltyFootprintFixtureJSON (pf : PenaltyFootprintFixture) : String :=
  "{"
    ++ "\"name\":\"" ++ escape pf.name ++ "\","
    ++ "\"footprint\":" ++ footprintJSON pf.footprint ++ ","
    ++ "\"expected\":" ++ boolJSON (pf.penalty.admits pf.footprint)
    ++ "}"

def penaltyFootprintsJSON (fixtures : List PenaltyFootprintFixture) : String :=
  "[" ++ String.intercalate "," (fixtures.map penaltyFootprintFixtureJSON) ++ "]"

def penaltyFootprintFixtures : List PenaltyFootprintFixture :=
  [
    {
      name := "imprisonment_admits"
      penalty := Penalty.imprisonment 1 5
      footprint := { imp_lo := 1, imp_hi := 5 : Footprint }
    },
    {
      name := "imprisonment_rejects_hi"
      penalty := Penalty.imprisonment 1 5
      footprint := { imp_lo := 1, imp_hi := 6 : Footprint }
    },
    {
      name := "fine_admits"
      penalty := Penalty.fine 1000 2000
      footprint := { fine_lo := 1000, fine_hi := 2000 : Footprint }
    },
    {
      name := "fine_unlimited_admits"
      penalty := Penalty.fineUnlimited 0
      footprint := { fine_lo := 0, fine_hi := 0, fine_unlimited := true : Footprint }
    },
    {
      name := "fine_unlimited_finite_admits"
      penalty := Penalty.fineUnlimited 0
      footprint := { fine_lo := 0, fine_hi := 5000 : Footprint }
    },
    {
      name := "caning_admits"
      penalty := Penalty.caning 3 6
      footprint := { caning_lo := 3, caning_hi := 6 : Footprint }
    },
    {
      name := "caning_unspecified_admits"
      penalty := Penalty.caningUnspecified 0
      footprint := ({
        caning_lo := 0, caning_hi := 0,
        caning_unspecified := true
      } : Footprint)
    },
    {
      name := "caning_unspecified_finite_admits"
      penalty := Penalty.caningUnspecified 0
      footprint := { caning_lo := 0, caning_hi := 6 : Footprint }
    },
    {
      name := "death_admits"
      penalty := Penalty.death
      footprint := { death := true : Footprint }
    },
    {
      name := "death_rejects"
      penalty := Penalty.death
      footprint := { death := false : Footprint }
    },
    {
      name := "cumulative_admits"
      penalty := Penalty.cumulative [
        Penalty.imprisonment 1 5, Penalty.fine 1000 2000,
        Penalty.caning 3 6, Penalty.death
      ]
      footprint := {
        imp_lo := 1, imp_hi := 5,
        fine_lo := 1000, fine_hi := 2000,
        caning_lo := 3, caning_hi := 6,
        death := true : Footprint
      }
    }
  ]

def fixtureJSON (name : String) (s : Statute) : String :=
  "\"" ++ name ++ "\":" ++ listToJSON (Generator.encodeStatute s)

def allJSON (fixtures : List (String × Statute)) : String :=
  let entries := fixtures.map (fun (n, s) => fixtureJSON n s)
  "{" ++ String.intercalate "," entries ++ "}"

end Yuho.ExportSpec

def main (args : List String) : IO Unit := do
  if args.contains "--verdicts" then
    IO.println (Yuho.ExportSpec.verdictsJSON Yuho.ExportSpec.allVerdictFixtures)
    return
  if args.contains "--penalty-footprints" then
    IO.println (Yuho.ExportSpec.penaltyFootprintsJSON Yuho.ExportSpec.penaltyFootprintFixtures)
    return
  let useFull := args.contains "--full"
  let fixtures :=
    if useFull then Yuho.Fixtures.fixtures
    else Yuho.ExportSpec.smokeFixtures
  IO.println (Yuho.ExportSpec.allJSON fixtures)
