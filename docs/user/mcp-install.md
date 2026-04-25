# Wiring Yuho's MCP Server into AI Clients

Yuho ships an MCP (Model Context Protocol) server that exposes the Singapore
Penal Code library, the grammar, the Phase-D encoding prompts, and a tool
surface for encoding / reviewing / navigating sections. AI clients (Claude
Desktop, Claude Code, Codex CLI, Cursor, etc.) can consume this surface
directly — no REST API, no SDK.

## Install

```bash
cd /path/to/yuho
./setup.sh                              # or pip install -e ./src
pip install -e 'src[mcp]'               # fastmcp + httpx dependencies
```

Verify:

```bash
python -c "from yuho.mcp.server import YuhoMCPServer; YuhoMCPServer(); print('ok')"
```

## Transports

Two transports are supported. Pick based on the client.

### stdio (Claude Desktop, Claude Code, Codex CLI)

Launch:

```bash
yuho serve                              # defaults to stdio
```

Register with **Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "yuho": {
      "command": "yuho",
      "args": ["serve"]
    }
  }
}
```

Register with **Claude Code** (`~/.claude/mcp.json` or per-project `.mcp.json`):

```json
{
  "mcpServers": {
    "yuho": {
      "command": "yuho",
      "args": ["serve"]
    }
  }
}
```

Register with **Codex CLI** — append to `~/.codex/config.toml`:

```toml
[[mcp_servers]]
name = "yuho"
command = "yuho"
args = ["serve"]
```

### HTTP/SSE (browser / hosted clients)

```bash
yuho serve --http --port 8080
```

Optional auth: set `mcp.auth_token` in `~/.config/yuho/config.toml`, then
clients send `Authorization: Bearer <token>` on every request.

## What the server exposes

### Tools (26)

Core language ops: `yuho_check`, `yuho_transpile`, `yuho_parse`,
`yuho_format`. LSP-like: `yuho_complete`, `yuho_hover`, `yuho_definition`,
`yuho_references`, `yuho_symbols`, `yuho_diagnostics`. Library:
`yuho_library_search`, `yuho_library_get`, `yuho_library_list`,
`yuho_validate_contribution`. Phase-D workflow:
`yuho_find_by_anchor`, `yuho_find_citations_to`, `yuho_section_pair`
(optional `include_ast=true` for structural AST summary),
`yuho_coverage_status`, `yuho_propose_encoding_skeleton`,
`yuho_grammar_example`, `yuho_run_l3_review` (mechanical checklist
audit, structured result), `yuho_apply_flag_fix` (trigger a
minimum-edit flag-fix via Codex).

**Research / G10 / corpus tools** (added in v5.1):
- `yuho_section_references(section, direction='both', kind=None, transitive=False)` — walk the cross-section reference graph (subsumes / amends / implicit edges).
- `yuho_simulate_fact_pattern(facts)` — run the fact-pattern simulator on a structured fact dict; returns satisfied / contradicted / unresolved element trace.
- `yuho_verify_grounded(answer)` — check that every claim in a model answer cites a real span in the encoded corpus; reports orphan claims and spurious citations.
- `yuho_benchmark_task(task_type, n=1, offset=0)` — fetch tasks from the Yuho benchmark pack (`citation_grounding`, `penalty_extraction`, `element_classification`, `cross_reference`, `illustration_recognition`).

Admin: `yuho_rate_limit_stats`.

### Resources

- `yuho://library/index` — full library listing with L1/L2/L3 badges. Primary discovery entry point.
- `yuho://library/{section}` — encoded `.yh` source for one section.
- `yuho://raw/{section}` — canonical SSO text for one section.
- `yuho://coverage` — live `coverage.json`.
- `yuho://flags` — currently flagged sections awaiting review.
- `yuho://gaps` — grammar gap log (G1–G14).
- `yuho://grammar` — full tree-sitter grammar source (~850 lines).
- `yuho://grammar/summary` — condensed plain-English summary of statute-body primitives (recommended for LLMs).
- `yuho://types` — built-in type reference.
- `yuho://examples/{primitive}` — worked example per grammar primitive (subsection, effective, fine_unlimited, caning_unspecified, penalty_or_both, penalty_when, nested_penalty, exception_priority, doc_comment_on_group, section_suffix, illustration, element_group).
- `yuho://prompts/phase-d-reencoding` — strict re-encoding prompt.
- `yuho://prompts/phase-d-l3-review` — 11-point L3 audit checklist.
- `yuho://prompts/phase-d-flag-fix` — minimum-edit flag-fix prompt.
- `yuho://docs/{topic}` — reference docs.

### Prompts

- `explain_statute(file_content)` — plain-English statute explanation.
- `convert_to_yuho(natural_text)` — statute text → Yuho skeleton.
- `analyze_coverage(file_content)` — test-coverage plan.
- `find_fidelity_issues(section)` — audit encoded vs canonical via the checklist.
- `recommend_l3(section)` — quick STAMP/FLAG decision.
- `encode_new_section(section)` — end-to-end encoding guide for an unencoded section.

## Typical client workflows

### Browse the library

1. Read `yuho://library/index` or call `yuho_library_list`.
2. For any section of interest, call `yuho_section_pair(section)` to see canonical + encoded side-by-side.

### Encode a new section

1. Call prompt `encode_new_section(section)` for a full guide.
2. Call `yuho_propose_encoding_skeleton(section)` for the boilerplate.
3. Read `yuho://prompts/phase-d-reencoding` for the strict rules.
4. Pull relevant `yuho://examples/{primitive}` for syntax.
5. Write the file. Call `yuho_check` to validate.

### Review an existing encoding

1. Call prompt `find_fidelity_issues(section)` or `recommend_l3(section)`.
2. The prompt tells the agent to call `yuho_section_pair(section)` and walk the checklist.
3. Stamp or flag based on findings. Human signs off on the stamp.

### Audit cross-references

1. Call `yuho_find_citations_to("415")` — who extends Cheating?
2. Call `yuho_find_by_anchor("pr415-")` to go from SSO URL to encoded section.

## Rate limits

The server has per-tool rate limits. See `yuho_rate_limit_stats` for live
stats. Override defaults in `~/.config/yuho/config.toml`:

```toml
[mcp]
host = "127.0.0.1"
port = 8080
auth_token = "..."
```

## Troubleshooting

- **`ImportError: MCP dependencies not installed`** → run `pip install -e 'src[mcp]'`.
- **Server starts but no tools appear in client** → confirm the client actually launched stdio (check its logs). Each client has a different reload trigger after editing `mcpServers` config.
- **`section X not in canonical corpus`** → either the section number is wrong or `library/penal_code/_raw/act.json` is stale. Regenerate with `scripts/scrape_sso.py`.
- **`coverage.json missing`** → run `scripts/coverage_report.py --act-dir library/penal_code --yuho ./path/to/yuho`.
