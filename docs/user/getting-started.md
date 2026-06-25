# Getting Started

Yuho ships as a local CLI and Python package for parsing, checking,
transpiling, verifying, and inspecting statute encodings.

## 1. Install

For the packaged CLI:

```bash
uv tool install 'yuho[dev]'
yuho doctor
yuho init yuho-starter
```

For a local checkout with the corpus and verification Make targets:

```bash
git clone https://github.com/gongahkia/yuho
cd yuho
./install.sh --dev
```

Manual local install:

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
yuho doctor
```

If this checkout's venv predates 2026-06-22, rerun
`uv pip install -e '.[dev]'` to pick up `z3-solver`.

For package use:

```bash
pip install yuho
```

If a shell resolves `yuho` outside the project venv, prefer
`uv run yuho ...` or reactivate `.venv`.

## 2. Create a starter workspace

```bash
yuho init yuho-starter
cd yuho-starter
yuho check statute.yh
yuho explain statute.yh --facts facts.json
```

`yuho init` writes a small statute, a matching facts file, a README, and
an English transpilation under `out/`.

## 3. Parse a statute

```bash
cat > theft.yh <<'YH'
statute 1 "Theft" {
  elements {
    actus_reus taking := "Takes movable property";
    mens_rea dishonestly := "With dishonest intent";
  }
  penalty {
    imprisonment := 1 year .. 3 years;
  }
}
YH

yuho check theft.yh
```

## 4. Transpile

```bash
yuho transpile -t english    theft.yh
yuho transpile -t json       theft.yh
yuho transpile -t latex      theft.yh
yuho transpile -t mermaid    theft.yh
yuho transpile -t mindmap    theft.yh
yuho transpile -t alloy      theft.yh
yuho transpile -t docx       theft.yh -o theft.docx
yuho transpile -t akomantoso theft.yh
```

`yuho transpile --all theft.yh --dir out/` writes the standard target
set into a directory. PDF/SVG/PNG outputs are derived from LaTeX or
Mermaid when the external renderers are installed.

## 5. Explore the checked-in corpus

```bash
yuho check library/penal_code/s415_cheating/statute.yh
yuho lint library/penal_code/s415_cheating/statute.yh
yuho ast library/penal_code/s415_cheating/statute.yh --stats --depth 3
yuho refs 415
yuho refs --scc --json
```

The repository ships all 524 Singapore Penal Code sections as `.yh`,
plus BNS, IPC, Malaysia, and Pakistan corpus material.

## 6. Verify retained gates

```bash
make verify-core
```

That target runs the retained corpus and toolchain checks: parse/lint
coverage, AKN XSD round-trip, runtime tests, Lean structural diff, and
mechanisation where the Lean toolchain is installed.

For direct `yuho verify` use, the dev install covers Z3. Z3 rejects
unsupported case-law and typed-burden constructs explicitly. Alloy 6 is a
separate jar install and is a secondary bounded-shape smoke backend; see the
README [Verification backends](../../README.md#verification-backends) section.

## 7. Shell completion

```bash
yuho completion zsh --install
yuho completion bash --install
yuho completion fish --install
```

## 8. Optional renderers

```bash
brew install --cask mactex-no-gui      # PDF target
npm install -g @mermaid-js/mermaid-cli # SVG/PNG targets
```

## Next Steps

- [CLI reference](cli-reference.md)
- [5-minute tour](5-minutes.md)
- [Syntax reference](../researcher/syntax.md)
- [Contributor architecture](../contributor/architecture.md)
