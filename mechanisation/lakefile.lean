import Lake
open Lake DSL

-- Yuho mechanisation: Lemma 6.2 (element correspondence) +
-- Lemma 6.4 (exception correspondence) of the soundness theorem
-- in `paper/sections/soundness.tex`.

package «yuho-mech» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

@[default_target]
lean_lib «Yuho» where
  -- Public surface — re-exported by the top-level Yuho.lean.
  roots := #[`Yuho]

lean_lib «Tests» where
  globs := #[.submodules `Tests]
