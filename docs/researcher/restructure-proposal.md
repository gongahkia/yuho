# Repository restructure proposal

Status: **proposal**, not yet executed. Approve / amend before any moves.

This document compares the current top-level layout against a proposed one,
explains every move / rename / delete, lists the blast radius of each, and
specifies the order in which the moves should happen so the working tree
stays buildable at every step.

---

## Goals

1. **Tighter top level.** Currently 11 directories at the root, several with
   overlapping or unclear purpose. Aim: ≤ 9 dirs, each with a one-sentence
   purpose statement that does not overlap any other.
2. **Audience-grouped docs.** `doc/` is currently 25+ flat files. Group by
   audience (user / contributor / researcher) so a newcomer can read the
   right doc first.
3. **OSS-conventional naming.** Singular `asset/` and `doc/` are unusual;
   plural `assets/` and `docs/` are the OSS norm.
4. **Standard Python layout.** `pyproject.toml` lives under `src/`, which
   confuses `pip install -e .` and most tooling. Promote to repo root.
5. **No empty / stale dirs.** `packages/` is empty; `statutes/` overlaps
   `examples/`.

Non-goals:

- Restructuring `src/yuho/` internals. The 19 subpackages are fine for
  what they do; touching them would break imports across the codebase.
- Renaming `library/penal_code/` or any encoded-statute paths. They are
  the primary artefact and have stable paths referenced from the LSP /
  MCP / CLI.
- Renaming committed git history. The git log is durable; no rewrites.

---

## Current layout

```
yuho/
├── README.md            (10 KB top-level pitch)
├── TODO.md              (case-insensitive duplicate of todo.md)
├── CLAUDE.md            (symlink to ~/.claude/CLAUDE.md)
├── .gitignore .gitattributes .pre-commit-hooks.yaml
├── .phase_d_progress.jsonl, .phase_d_l3_progress.jsonl,
│   .phase_d_flag_fix_progress.jsonl   (Phase-D dispatcher state)
├── asset/               (logo, comic, memes, screenshot — 4 dirs)
├── doc/                 (25 flat .md files + asset/, ci-templates/, cookbook/)
├── editors/
│   └── vscode-yuho/     (extension; word-yuho/ planned)
├── examples/            (6 toy .yh demo files)
├── library/
│   ├── _index/          (sso_acts.json — 500 SG Acts catalogue)
│   └── penal_code/      (524 encoded sections + _coverage/, _raw/)
├── packages/            (empty — leftover scaffolding)
├── paper/               (research paper — landed this session)
├── scripts/             (build_grammar, coverage_report, scrape_sso, phase_d_*)
├── src/
│   ├── pyproject.toml   (Python build config — odd location)
│   ├── hatch_build.py
│   ├── tree-sitter-yuho/  (grammar.js + bindings)
│   ├── tree_sitter_yuho/  (compiled .dylib)
│   └── yuho/            (19 subpackages: ast, cli, lsp, mcp, transpile, etc.)
├── statutes/            (3 stale demo .yh files — overlaps with examples/)
└── tests/               (pytest, ~20 test_*.py + e2e/)
```

---

## Proposed layout

```
yuho/
├── README.md            (rewritten — hero, badges, quickstart, feature matrix)
├── CONTRIBUTING.md      (NEW — extracted from inline READMEs)
├── CITATION.cff         (NEW — for paper / artefact citation)
├── LICENSE              (NEW — explicit license file at root, currently MIT in pyproject)
├── pyproject.toml       (MOVED from src/pyproject.toml)
├── todo.md
├── CLAUDE.md            (symlink, unchanged)
├── .gitignore .gitattributes .pre-commit-hooks.yaml
├── .phase_d_progress.jsonl  (etc — unchanged, gitignored already)
├── assets/              (RENAMED from asset/. Same contents.)
├── docs/                (RENAMED from doc/. Reorganised — see § Doc reorg.)
├── editors/
│   ├── vscode-yuho/
│   └── word-yuho/       (NEW — Office Add-in scaffold, next task)
├── examples/            (6 existing files + 3 absorbed from statutes/)
├── library/             (UNCHANGED — _index/, penal_code/)
├── paper/               (UNCHANGED)
├── scripts/             (UNCHANGED)
├── src/
│   ├── tree-sitter-yuho/
│   ├── tree_sitter_yuho/
│   ├── yuho/            (UNCHANGED internal layout — 19 subpackages stay)
│   └── hatch_build.py
└── tests/               (UNCHANGED)
```

**Removed:**
- `packages/` (empty)
- `statutes/` (stale; absorbed into `examples/`)
- `TODO.md` (case-insensitive dup of `todo.md`; same inode on macOS APFS already)

**Renamed:**
- `asset/` → `assets/`
- `doc/` → `docs/`

**Moved:**
- `src/pyproject.toml` → `pyproject.toml` (root)
- `src/hatch_build.py` (stays — `hatchling` build hook references it relative)

**Added:**
- `CONTRIBUTING.md`, `CITATION.cff`, `LICENSE` at root
- `editors/word-yuho/` directory scaffold (next task)

---

## Doc reorg

`doc/` currently has 25 flat files. Proposed grouping in `docs/`:

```
docs/
├── INDEX.md                 (NEW — top-level audience-grouped TOC)
├── architecture.svg         (NEW — rendered from paper/figures/architecture.mmd)
├── retrospective.md         (NEW — pulls from PHASE_C_REVIEW + PHASE_D_*)
│
├── user/                    (audience: people running yuho)
│   ├── getting-started.md   (← GETTING_STARTED.md)
│   ├── 5-minutes.md         (← 5_MINUTES.md)
│   ├── faq.md               (← FAQ.md)
│   ├── law-student-guide.md (← LAW_STUDENT_GUIDE.md)
│   ├── cli-reference.md     (← CLI_REFERENCE.md)
│   ├── cli-exit-codes.md    (← CLI_EXIT_CODES.md)
│   ├── error-codes.md       (← ERROR_CODES.md)
│   ├── mcp-install.md       (← MCP_INSTALL.md)
│   └── deployment.md        (← DEPLOYMENT.md)
│
├── contributor/             (audience: people changing yuho)
│   ├── architecture.md      (← ARCHITECTURE.md)
│   ├── config.md            (← CONFIG.md)
│   ├── sdk.md               (← SDK.md)
│   ├── sdk-quickstart.md    (← SDK_QUICKSTART.md)
│   ├── transpiler-plugins.md (← TRANSPILER_PLUGINS.md)
│   ├── porting-guide.md     (← PORTING_GUIDE.md)
│   └── ci-templates/        (← ci-templates/)
│
├── researcher/              (audience: paper / theory)
│   ├── formal-semantics.md  (← FORMAL_SEMANTICS.md)
│   ├── syntax.md            (← SYNTAX.md)
│   ├── phase-c-gaps.md      (← PHASE_C_GAPS.md)
│   ├── phase-c-review.md    (← PHASE_C_REVIEW.md)
│   ├── phase-d-l3-review-prompt.md   (← PHASE_D_L3_REVIEW_PROMPT.md)
│   ├── phase-d-reencoding-prompt.md  (← PHASE_D_REENCODING_PROMPT.md)
│   ├── phase-d-flag-fix-prompt.md    (← PHASE_D_FLAG_FIX_PROMPT.md)
│   └── openapi.yaml          (← openapi.yaml)
│
├── cookbook/                (kept as-is — recipe-style how-tos)
└── assets/                  (← doc/asset/, renamed for consistency)
```

**Naming convention**: lowercase-kebab-case. macOS HFS+/APFS is case-insensitive
by default but other contributors use case-sensitive filesystems; consistent
casing avoids the `TODO.md` / `todo.md` collision class.

**Why this shape**: Hugging Face model cards, Notion docs, and Obsidian
vaults all converge on audience-first grouping. Logseq is outliner-shaped
which doesn't translate to filesystem layout, so we don't borrow from it
structurally — just from its cross-link emphasis (see § Cross-linking).

---

## Top-level README rewrite

Current `README.md` is ~10 KB of mixed pitch/install/feature copy. Replacement
will follow the Hugging Face / Catala style:

1. **Hero block** (above the fold):
   - Project name + one-line tagline.
   - Author link (`gabrielongzm.com`).
   - Status badges: build, tests, coverage (524/524 L1+L2 · 122 L3),
     license, Python version.
   - Animated GIF or screenshot of the LSP hover in action (kept under
     `assets/screenshot/`).
2. **What is Yuho?** — 3-paragraph pitch (max). Cite the paper if it lands.
3. **Quickstart** — tabbed "I want to ..." block:
   - I want to *read* an encoded statute → link to one rendered example.
   - I want to *encode* a new statute → 60-second `pip install` + LSP setup.
   - I want to *understand* the design → link to the paper PDF in `paper/`.
4. **Feature matrix** — small table covering the 6 transpilers, the 3 editor
   surfaces, the 2 verification engines. Single column of checks.
5. **Architecture diagram** — embedded SVG of `docs/architecture.svg`.
6. **Project status** — coverage numbers (auto-injected from
   `library/penal_code/_coverage/coverage.json` via a tiny Makefile target).
7. **Citation block** — BibTeX entry pointing at the paper.
8. **Contributing** — one paragraph, link to `CONTRIBUTING.md`.

References for visual reference:
- HuggingFace transformers README (badge density, audience triage)
- Catala README (narrative intro, example-first)
- Obsidian forum-style callouts for "Note:" / "Warning:" / "Tip:"
- Notion's toggle-block pattern for "Click to expand: full feature list"
  (achieved in markdown via `<details><summary>...</summary>`)

---

## Cross-linking

Every `.md` should be reachable from `docs/INDEX.md` via at most two clicks.
Within a file, references to other docs should be relative-path links —
Obsidian-style wikilinks would be cleaner but standard markdown link syntax
is universal and works in Github's renderer.

A weekly link-checker script (`scripts/check_links.py`) will:
1. Parse every `.md` file under `docs/`, `editors/*/README.md`, top-level
   `README.md`, and `paper/README.md`.
2. Verify every relative link resolves to an existing file.
3. Verify every `http(s)://` link returns a 2xx (with timeout + skip-on-fail).

Not a hard CI gate; a nightly cron-style check.

---

## Move sequence (so build stays green at every step)

The proposal becomes a series of git commits:

1. **Commit A — additions only.** Create `CONTRIBUTING.md`, `CITATION.cff`,
   `LICENSE` at root. Create `docs/INDEX.md` placeholder. No moves yet.
2. **Commit B — `pyproject.toml` move.** Move `src/pyproject.toml` →
   `pyproject.toml`. Update `[tool.hatch.build.targets.wheel]` packages
   path. Update `[tool.hatch.build.targets.sdist]` include patterns.
   Run `pip install -e .` locally; run `pytest tests/` to confirm.
3. **Commit C — `doc/` → `docs/` rename.** Single `git mv doc docs`. Update
   any in-file references via `git grep -l 'doc/' | xargs sed -i ...`.
   Run `pytest tests/test_docs_contract.py` to catch breakage.
4. **Commit D — doc reorg.** `git mv` each file into its audience subfolder.
   Update `docs/INDEX.md` to point at the new locations. Update top-level
   `README.md` to point into the new structure.
5. **Commit E — `asset/` → `assets/` rename.**
6. **Commit F — remove `packages/`.** Single empty-dir delete.
7. **Commit G — absorb `statutes/` into `examples/`.** `git mv statutes/*.yh
   examples/`, then `rmdir statutes/`. Spot-check that the 3 absorbed files
   parse via `yuho check`.
8. **Commit H — top-level `README.md` rewrite.** Hero, badges, quickstart
   matrix, architecture SVG, citation. The diff for this is large because
   the file is rewritten end-to-end.
9. **Commit I — `editors/word-yuho/` scaffold.** New directory, manifest,
   minimal Office.js add-in (this also kicks off the next task).
10. **Commit J — link-checker script.** Add `scripts/check_links.py`.

Each commit is reversible. After each, the test suite passes and `yuho
check` over `library/penal_code/` still reports 524/524 L1+L2.

---

## Risks and known issues

- **Symlink: `CLAUDE.md`.** The top-level `CLAUDE.md` is a symlink to
  `~/.claude/CLAUDE.md` (per-machine config). The restructure does not
  touch it. Other contributors will see a broken symlink; we should
  either convert to a regular file with a comment "edit your local
  ~/.claude/CLAUDE.md instead", or `.gitignore` the symlink. Decision
  deferred — doesn't block the restructure.
- **Phase-D progress files at root.** `.phase_d_*.jsonl` files are dispatcher
  state. Should be moved under `library/penal_code/_coverage/` for tidiness.
  Already gitignored; no commit-time impact. Defer to a separate cleanup.
- **`pyproject.toml` move blast radius.** Build helpers, CI templates,
  install instructions in every README, the paper `\verb` blocks all
  reference `src/pyproject.toml` paths. The Commit B step needs a
  `git grep -l 'src/pyproject.toml'` sweep before merging.
- **`tree-sitter-yuho/` paths.** The grammar's hatch hook compiles to
  `src/tree_sitter_yuho/libtree-sitter-yuho.dylib`. Moving `pyproject.toml`
  changes the relative path the hook resolves; `hatch_build.py` will need
  one-line tweak.
- **Doc rename CI.** If any internal CI references `doc/cookbook/` or
  similar, those will need updating. Grep before merge.

---

## What this proposal does *not* do

- Doesn't change `src/yuho/` internal module layout. Tempting to consolidate
  19 subpackages, but it's working, importing, and tested. Touching it is a
  separate task with its own risk budget.
- Doesn't introduce a monorepo / workspace tool (Nx, Turborepo, pnpm
  workspaces). The Python + TypeScript split is small enough that two
  separate `pyproject.toml` and `package.json` files are clearer than a
  monorepo manifest.
- Doesn't pick a docs-site generator (Docusaurus, MkDocs, Sphinx). Static
  site is in `todo.md` as a `(def)` deferred item; the markdown reorg
  proposed here is generator-friendly so we can pick later.
- Doesn't rename `library/penal_code/` paths. The L3 dispatcher, MCP
  resources, and LSP hover handlers all hard-code these paths.

---

## Sign-off

When you're ready, approve and I'll execute commits A–J in order, running
the relevant smoke check between each. Estimated ~30 minutes of mechanical
moves + a top-level README rewrite that takes the bulk of the time.

If any item above is wrong — particularly anything in § Risks — flag it
before we start. The cost of catching a mis-ordered move at proposal time
is one paragraph; the cost at commit time is a revert chain.
