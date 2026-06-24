/-
ScopedName.lean — binder infrastructure for qualified mechanisation names.

The SMT-facing generator needs statute-local atoms such as
`<section>_<local>`. This module centralises that binding shape so
future scoped names (for definitions, case-law effects, and typed
facts) do not duplicate string concatenation across proof files.
-/

import Yuho.AST

namespace Yuho

/-- A lexical namespace path. For current generator atoms the path is
just the statute section number, but the representation supports deeper
scopes. -/
structure NameScope where
  parts : List String
deriving Repr, BEq

namespace NameScope

def root : NameScope :=
  { parts := [] }

def child (scope : NameScope) (part : String) : NameScope :=
  { parts := scope.parts ++ [part] }

def statute (s : Statute) : NameScope :=
  child root s.section_number

def render : NameScope → String
  | { parts := [] } => ""
  | { parts := head :: rest } =>
      rest.foldl (fun acc part => acc ++ "_" ++ part) head

end NameScope

/-- A local name bound inside a scope. -/
structure ScopedName where
  scope : NameScope
  localName : String
deriving Repr, BEq

namespace ScopedName

def inScope (scope : NameScope) (localName : String) : ScopedName :=
  { scope, localName }

def statute (s : Statute) (localName : String) : ScopedName :=
  inScope (NameScope.statute s) localName

def render (name : ScopedName) : String :=
  name.scope.render ++ "_" ++ name.localName

theorem render_statute (s : Statute) (localName : String) :
    (statute s localName).render = s.section_number ++ "_" ++ localName := by
  simp [statute, inScope, render, NameScope.statute, NameScope.child,
    NameScope.root, NameScope.render]

end ScopedName

end Yuho
