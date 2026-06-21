# FAQ

## What does Yuho mean?

Yuho is derived from 夢法 (*yume ho*), roughly "ideal law" in Japanese.

## What Python version is required?

Python 3.10 or later. See `pyproject.toml` for the supported versions.

## How do I install Yuho?

```bash
pip install yuho
```

For repository work:

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

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
