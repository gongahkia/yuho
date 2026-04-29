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

-- §6.6 Python-side faithfulness — emits Generator.encodeStatute
-- as JSON for the smoke fixtures. Driven by
-- scripts/verify_structural_diff.py from the repo root.
-- The full-corpus fixture file (`scripts/Fixtures.lean`) is
-- auto-generated; it has to be declared as a lib so lake can
-- elaborate the import in ExportSpec.lean.
lean_lib «scripts» where
  globs := #[.submodules `scripts]

lean_exe «export_spec» where
  root := `scripts.ExportSpec
