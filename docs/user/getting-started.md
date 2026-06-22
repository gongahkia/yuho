# Getting Started

Yuho ships as a local CLI and Python package for parsing, checking,
transpiling, verifying, and inspecting statute encodings.

## 1. Install

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

For package use:

```bash
pip install yuho
```

## 2. Parse a statute

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

## 3. Transpile

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

## 4. Explore the checked-in corpus

```bash
yuho check library/penal_code/s415_cheating/statute.yh
yuho refs 415
yuho refs --scc --json
```

The repository ships all 524 Singapore Penal Code sections as `.yh`,
plus raw corpus material for the Indian Penal Code.

## 5. Verify retained gates

```bash
make verify-core
```

That target runs the retained corpus and toolchain checks: parse/lint
coverage, AKN XSD round-trip, runtime tests, Lean structural diff, and
mechanisation where the Lean toolchain is installed.

For direct `yuho verify` use, the dev install covers Z3. Alloy 6 is a
separate jar install; see the README
[Verification backends](../../README.md#verification-backends) section.

## Next Steps

- [CLI reference](cli-reference.md)
- [5-minute tour](5-minutes.md)
- [Syntax reference](../researcher/syntax.md)
- [Contributor architecture](../contributor/architecture.md)
