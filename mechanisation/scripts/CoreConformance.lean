import Yuho.CoreYuho.GeneratedVectors

open Yuho.CoreYuho.Conformance

def main : IO Unit := do
  match evaluateVectors vectors with
  | .ok encoded => IO.print encoded
  | .error issue => throw (IO.userError issue)
