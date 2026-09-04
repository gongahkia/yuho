# FAQ

## What does Yuho mean?

Yuho is derived from 夢法 (*yume ho*), roughly "ideal law" in Japanese.

## What Python version is required?

Python 3.10 or later. See `pyproject.toml` for the supported versions.

## How do I install Yuho?

```bash
uv tool install 'yuho==5.1.0'
```

For repository work:

```bash
git clone https://github.com/gongahkia/yuho
cd yuho
./install.sh --dev
```

The checkout installer requires uv 0.11.14 and synchronizes the committed
`uv.lock`; choose an exact published version when installing the package.

## What file extension does Yuho use?

`.yh`.

## Can Yuho model statutes outside Singapore?

The syntax is jurisdiction-agnostic. The checked-in encoded corpus is
Singapore Penal Code focused; other statute families need separate
encoding work.

## What transpilation targets are supported?

JSON, controlled English, LaTeX, Mermaid flowchart, Mermaid mindmap,
Alloy, DOCX, and Akoma Ntoso. The CLI can derive PDF/SVG/PNG when the
external renderers are installed.

## What editor should I use?

Any text editor. Save files with a `.yh` extension and run `yuho check`
or `yuho fmt` from the CLI.

## Does Yuho provide legal advice?

No. It encodes and checks statute structure. Legal application,
interpretation, and advice remain outside the tool.
