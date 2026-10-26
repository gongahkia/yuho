import Yuho.CoreYuho.Quantitative
open Yuho.CoreYuho.Quantitative

def display : Value → String
  | none => "U"
  | some n => "K:" ++ toString n
def main : IO _root_.Unit := do
  -- Independently authored mathematical cases; no production Haskell helper.
  let cases := [
    sumValues [some 400000, some 600000],
    sumValues [some 400000, some 599999],
    sumValues [some 1, some (-4)],
    filteredSum [(.yes, some 4), (.yes, none)],
    filteredSum [(.yes, some 4), (.no, none)],
    filteredSum [(.yes, some 4), (.unknown, some 0)],
    scale 3 (sumValues [some 125, some 275]),
    scale 0 none,
    count [.yes, .no, .yes], count [.yes, .unknown],
    sumValues [], scale 3 (some 9007199254740993), count [],
    scale (-2) (some 7), inclusion .unknown (some 0)]
  for value in cases do IO.println (display value)
