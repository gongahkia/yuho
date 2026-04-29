/-
ExportSpec.lean — emit the verified `Generator.encodeStatute`
biconditional list as JSON for each smoke fixture.

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

def fixtureJSON (name : String) (s : Statute) : String :=
  "\"" ++ name ++ "\":" ++ listToJSON (Generator.encodeStatute s)

def allJSON (fixtures : List (String × Statute)) : String :=
  let entries := fixtures.map (fun (n, s) => fixtureJSON n s)
  "{" ++ String.intercalate "," entries ++ "}"

end Yuho.ExportSpec

def main (args : List String) : IO Unit := do
  let useFull := args.contains "--full"
  let fixtures :=
    if useFull then Yuho.Fixtures.fixtures
    else Yuho.ExportSpec.smokeFixtures
  IO.println (Yuho.ExportSpec.allJSON fixtures)
