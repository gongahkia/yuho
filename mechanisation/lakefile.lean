import Lake
open Lake DSL

-- Yuho mechanisation: Lemma 6.2 (element correspondence) +
-- Lemma 6.4 (exception correspondence) of the soundness theorem.

package «yuho-mech» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

@[default_target]
lean_lib «Yuho» where
  -- Public finite Core surface re-exported by Yuho.lean.
  roots := #[`Yuho]

-- Independent conformance runners.
lean_lib «scripts» where
  globs := #[.submodules `scripts]

lean_exe «core_conformance» where
  root := `scripts.CoreConformance

lean_exe «typed_finite_conformance» where
  root := `scripts.TypedFiniteConformance

lean_exe «release_v03_conformance» where
  root := `scripts.ReleaseV03Conformance
