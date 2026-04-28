/-
Yuho mechanisation — top-level module.

Re-exports the formal-statement layer (AST + operational semantics
+ abstract SMT model + soundness lemmas) for the §6.6 paper claim.

Build: `cd mechanisation && lake build`. Requires the Lean
toolchain pinned in `lean-toolchain` (Lean 4.10.0+).
-/

import Yuho.AST
import Yuho.Facts
import Yuho.Eval
import Yuho.SMTAbs
import Yuho.Soundness
import Yuho.Graph
import Yuho.Cross
import Yuho.Penalty
import Yuho.Generator
