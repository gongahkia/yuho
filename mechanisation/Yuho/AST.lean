/-
Yuho AST — the syntactic domains used by the mechanisation.

This file mechanises Definitions 4.1–4.4 (element / element group /
exception / statute). The encoding intentionally drops fields that
are semantically inert at the conviction layer (descriptions,
definitions, illustrations, case-law anchors, metadata) so the
proof obligations of §6 stay focused on element + exception
structure.
-/

namespace Yuho

/-- Doctrinal element kind. The kind tag is preserved for downstream
tools (the controlled-English transpiler renders by kind) but is
inert at the structural layer of §4 — `Element.eval` doesn't
inspect it. -/
inductive ElementKind where
  | actusReus : ElementKind
  | mensRea : ElementKind
  | circumstance : ElementKind
deriving Repr, DecidableEq, BEq

/-- A leaf element: a kind tag, a unique identifier (matches the
fact-map key), and a free-text description (semantically opaque). -/
structure Element where
  kind : ElementKind
  name : String
  description : String
deriving Repr, BEq

/-- An element tree: leaves (single elements) or recursive groups
combined under `all_of` / `any_of`. The top-level element block of
a statute is implicitly `all_of` per §4.2. -/
inductive ElementGroup where
  | leaf  : Element → ElementGroup
  | allOf : List ElementGroup → ElementGroup
  | anyOf : List ElementGroup → ElementGroup
deriving Repr

/-- An exception's guard is a boolean predicate over a fact pattern.
We treat `Facts → Bool` opaquely here; the surface language allows
arbitrary boolean expressions, but for the purposes of §6 only
the eventual truth value matters. -/
abbrev Guard := (String → Bool) → Bool

/-- The effect of a fired exception relation. A rebutting exception
negates the statute conclusion; an undercutting exception only
negates the target exception's inference. -/
inductive DefeatKind where
  | rebuts : DefeatKind
  | undercuts : DefeatKind
deriving Repr, DecidableEq, BEq, Inhabited

/-- An exception node. `defeats` carries the labels of sibling
exceptions this one targets; `relation` says whether the target is
rebutted at conclusion level or undercut at inference level. The
linter (in the wider toolchain) enforces the relation DAGs are
acyclic. -/
structure Exception where
  label : String
  guard : Guard
  defeats : List String
  relation : DefeatKind := .rebuts
deriving Inhabited

/-- A statute. Penalty + subsection + metadata fields are elided
from the mechanisation per §4 preliminaries — they are inert at the
conviction layer. -/
structure Statute where
  section_number : String
  title : String
  elements : ElementGroup
  exceptions : List Exception

/-- A complete module is a list of statutes. -/
structure Module where
  statutes : List Statute

end Yuho
