/-
Yuho mechanisation — top-level module.

Re-exports the formal-statement layer (AST + operational semantics
+ abstract SMT model + soundness lemmas).

Build: `cd mechanisation && lake build`. Requires the Lean
toolchain pinned in `lean-toolchain` (Lean 4.10.0+).
-/

import Yuho.AST
import Yuho.ScopedName
import Yuho.Facts
import Yuho.Eval
import Yuho.CaseLaw
import Yuho.SMTAbs
import Yuho.Soundness
import Yuho.Graph
import Yuho.Cross
import Yuho.CrossDeep
import Yuho.Defeasibility
import Yuho.Penalty
import Yuho.Range
import Yuho.Generator
