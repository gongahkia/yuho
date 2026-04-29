# Yuho documentation

Docs are grouped by audience. Pick the section that matches what you want
to do; cross-links between sections are explicit.

---

## I want to *use* Yuho — `user/`

Audience: people running the `yuho` CLI, the LSP, or the MCP server,
encoding statutes or consuming the encoded library.

- [Getting started](user/getting-started.md) — install + first encoding in 60 seconds.
- [5-minute tour](user/5-minutes.md) — the core grammar by example.
- [FAQ](user/faq.md) — common questions about scope, coverage, and how Yuho compares to Catala / Akoma Ntoso.
- [Law student guide](user/law-student-guide.md) — Yuho through the lens of a Singapore criminal-law learner.
- [CLI reference](user/cli-reference.md) — every `yuho` subcommand with examples.
- [CLI exit codes](user/cli-exit-codes.md) — what each non-zero exit means.
- [Error codes](user/error-codes.md) — diagnostic IDs and their meanings.
- [MCP install](user/mcp-install.md) — wire Yuho's MCP server into Claude Desktop / Claude Code / Codex CLI / Cursor.
- [Deployment](user/deployment.md) — running Yuho in CI or as a service.

---

## I want to *change* Yuho — `contributor/`

Audience: people changing the codebase, adding transpilers, or porting
Yuho to a new statute family.

- [Architecture](contributor/architecture.md) — module layout and data flow from grammar to AST to transpilers.
- [Configuration](contributor/config.md) — config schema and defaults.
- [SDK](contributor/sdk.md) — embedding Yuho in another Python program.
- [SDK quickstart](contributor/sdk-quickstart.md) — minimal embed example.
- [Transpiler plugins](contributor/transpiler-plugins.md) — author a new transpile target.
- [Porting guide](contributor/porting-guide.md) — encode a different statute family.
- [CI templates](contributor/ci-templates/) — drop-in CI configs.

---

## I want to *understand* Yuho — `researcher/`

Audience: paper readers, reviewers, anyone tracing the design rationale.

- [Formal semantics](researcher/formal-semantics.md) — the grammar's denotational semantics.
- [Syntax reference](researcher/syntax.md) — every grammar production with examples.
- [Phase C gaps](researcher/phase-c-gaps.md) — the fourteen grammar gaps surfaced during mass-encoding (G1–G14).
- [Grammar quirks](grammar-quirks.md) — known parser limitations + authoring guidance to avoid them.
- [OpenAPI spec](researcher/openapi.yaml) — Yuho's REST surface (where it has one).

---

## Cross-cutting

- [Cookbook](cookbook/) — recipe-style how-tos that don't fit one audience.
- [Assets](assets/) — diagrams, screenshots, comic / meme variants.
- [Architecture diagram (SVG)](architecture.svg) — rendered from `paper/figures/architecture.mmd`.
- [Retrospective](retrospective.md) — Phase A–D lessons learned + numbers.

The Phase D agent prompts now live under `researcher/`:
- [phase-d-l3-review-prompt.md](researcher/phase-d-l3-review-prompt.md)
- [phase-d-reencoding-prompt.md](researcher/phase-d-reencoding-prompt.md)
- [phase-d-flag-fix-prompt.md](researcher/phase-d-flag-fix-prompt.md)

---

## See also

- [Top-level README](../README.md) — project pitch + quickstart.
- [Research paper draft](../paper/) — full prose treatment of the design.
- [Encoded library](../library/penal_code/) — the artefact itself.
- [TODO.md](../TODO.md) — outstanding work.
