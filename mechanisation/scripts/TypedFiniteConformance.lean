import Yuho.CoreYuho.GeneratedTypedFiniteVectors

open Yuho.CoreYuho.TypedFinite.Conformance

def main : IO Unit := do
  match evaluateVectors vectors with
  | .ok encoded => IO.print encoded
  | .error issue => throw (IO.userError issue)
