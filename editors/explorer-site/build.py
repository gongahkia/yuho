#!/usr/bin/env python3
"""Build the static Penal Code explorer site from the canonical JSON corpus.

Output goes to ``editors/explorer-site/build/``. Layout:

    build/
    ├── index.html            -- searchable index of all 524 sections
    ├── coverage.html         -- L1 / L2 / L3 dashboard
    ├── flags.html            -- list of L3-flagged sections needing review
    ├── about.html            -- methodology, citation, disclaimer
    ├── s/<N>.html            -- per-section page
    └── static/
        ├── style.css
        └── search.js

The site is plain static HTML + a tiny JS index for client-side search.
No build chain (Webpack / Rollup / Astro / etc.) — single-file generator
that writes the tree directly. Deploy to any static host (gh-pages,
Netlify, Cloudflare Pages, plain S3) by serving ``build/``.

Run:
    python3 scripts/build_corpus.py                            # produce corpus
    python3 editors/explorer-site/build.py                     # produce site
    python3 -m http.server -d editors/explorer-site/build 8000 # preview
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html as _html
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"
SITE_ROOT = Path(__file__).resolve().parent
BUILD = SITE_ROOT / "build"
STATIC = BUILD / "static"


# ---------------------------------------------------------------------------
# Style + scripts
# ---------------------------------------------------------------------------


_STYLE = r"""
:root {
  --c-bg: #fafafc;
  --c-fg: #1a1a22;
  --c-muted: #6a6a75;
  --c-card: #ffffff;
  --c-border: #e8e8ee;
  --c-accent: #3a86ff;
  --c-accent-2: #6f5cff;
  --c-l3-stamped: #1a8b3a;
  --c-l3-flagged: #c43d3d;
  --c-l3-unstamped: #b07020;
}
@media (prefers-color-scheme: dark) {
  :root {
    --c-bg: #15151c;
    --c-fg: #e2e2e8;
    --c-muted: #9090a0;
    --c-card: #1a1a22;
    --c-border: #2a2a35;
    --c-l3-stamped: #4adb6a;
    --c-l3-flagged: #ff6a6a;
    --c-l3-unstamped: #e0a050;
  }
}

* { box-sizing: border-box; }
html { font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
body { margin: 0; background: var(--c-bg); color: var(--c-fg); }

a { color: var(--c-accent); text-decoration: none; }
a:hover { text-decoration: underline; }

header.site {
  background: linear-gradient(135deg, var(--c-accent) 0%, var(--c-accent-2) 100%);
  color: #fff;
  padding: 1.4rem 1.4rem 1.6rem;
  display: flex;
  align-items: baseline;
  gap: 1.2rem;
  flex-wrap: wrap;
}
header.site h1 { margin: 0; font-size: 1.4rem; font-weight: 700; letter-spacing: 0.02em; }
header.site nav { margin-left: auto; display: flex; gap: 1.2rem; font-size: 0.95em; }
header.site nav a { color: #fff; opacity: 0.92; }
header.site nav a:hover { opacity: 1; text-decoration: underline; }
header.site .tagline { font-size: 0.92em; opacity: 0.92; }

main {
  max-width: 70rem;
  margin: 0 auto;
  padding: 1.6rem 1.4rem 4rem;
}

h2 { margin-top: 2.2em; font-size: 1.1rem; font-weight: 600; }
h2:first-child { margin-top: 0; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr));
  gap: 0.55rem;
  margin: 1rem 0 2rem;
}

.card {
  background: var(--c-card);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 0.5rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  transition: transform 0.06s ease-out, border-color 0.06s ease-out;
}
.card:hover {
  border-color: var(--c-accent);
  transform: translateY(-1px);
}
.card a {
  color: var(--c-fg);
  font-weight: 600;
  font-size: 0.95em;
}
.card .num { color: var(--c-muted); font-family: ui-monospace, monospace; font-size: 0.85em; }
.card .title { font-size: 0.92em; line-height: 1.3; min-height: 2.4em; }
.card .badges { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-top: 0.18rem; }
.card .snippet {
  margin-top: 0.3em;
  font-size: 0.83em;
  color: var(--c-muted);
  line-height: 1.35;
  border-top: 1px dashed var(--c-border);
  padding-top: 0.3em;
}
.card .snippet mark {
  background: #ffe066;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}
@media (prefers-color-scheme: dark) {
  .card .snippet mark { background: #5a4a10; color: #ffe9a0; }
}

.badge {
  display: inline-block;
  font: 600 0.7em/1.2 ui-monospace, monospace;
  padding: 0.05em 0.4em;
  border-radius: 3px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.badge.l1 { background: #e3f2fd; color: #1976d2; }
.badge.l2 { background: #e8f5e9; color: #2e7d32; }
.badge.l3-stamped { background: #e8f5e9; color: var(--c-l3-stamped); }
.badge.l3-flagged { background: #ffeaea; color: var(--c-l3-flagged); }
.badge.l3-unstamped { background: #fff5e0; color: var(--c-l3-unstamped); }

@media (prefers-color-scheme: dark) {
  .badge.l1 { background: #1a3252; }
  .badge.l2 { background: #1f3622; }
  .badge.l3-stamped { background: #1f3622; }
  .badge.l3-flagged { background: #401818; }
  .badge.l3-unstamped { background: #3a2810; }
}

.searchbar {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0 1.5rem;
}
.searchbar input {
  flex: 1;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  font: 14.5px/1.4 inherit;
  background: var(--c-card);
  color: var(--c-fg);
}
.searchbar input:focus {
  outline: 2px solid var(--c-accent);
  outline-offset: -1px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr));
  gap: 0.7rem;
  margin: 1rem 0;
}
.stat {
  background: var(--c-card);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 0.7rem 0.9rem;
}
.stat .v { font: 700 1.7rem/1.2 ui-monospace, monospace; color: var(--c-accent); }
.stat .l { color: var(--c-muted); font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.2em; }

table.refs { border-collapse: collapse; width: 100%; margin: 0.6em 0; }
table.refs th, table.refs td { padding: 0.35em 0.55em; border-bottom: 1px solid var(--c-border); text-align: left; font-size: 0.92em; }
table.refs th { color: var(--c-muted); font-weight: 500; font-size: 0.82em; text-transform: uppercase; letter-spacing: 0.04em; }

pre.src {
  background: #15151c;
  color: #d6d6e0;
  border-radius: 6px;
  padding: 0.85rem 1rem;
  font: 12.5px/1.55 ui-monospace, "SF Mono", monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
pre.lite {
  background: var(--c-card);
  color: var(--c-fg);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 0.7rem 0.9rem;
  font: 12.5px/1.55 ui-monospace, monospace;
  overflow-x: auto;
  white-space: pre-wrap;
}

section.section-page header {
  border-bottom: 1px solid var(--c-border);
  padding-bottom: 0.9rem;
  margin-bottom: 1.2rem;
}
section.section-page h1 { margin: 0; font-size: 1.5rem; }
section.section-page h1 .num { color: var(--c-muted); font-weight: 500; margin-right: 0.5em; font-family: ui-monospace, monospace; }
section.section-page .meta { color: var(--c-muted); font-size: 0.92em; display: flex; gap: 0.9rem; flex-wrap: wrap; margin-top: 0.5rem; }

.diagram {
  width: 100%;
  overflow: auto;
  background: var(--c-card);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 0.8rem;
  text-align: center;
  margin: 0.6rem 0;
}
.diagram svg.yuho-mermaid-svg, .diagram svg {
  max-width: 100%;
  height: auto;
}
@media (prefers-color-scheme: dark) {
  .diagram svg text { fill: #d6d6e0; }
}

.flag-callout {
  background: #fff8e6;
  border: 1px solid #ffd166;
  border-left: 3px solid #ffd166;
  border-radius: 5px;
  padding: 0.7rem 0.9rem;
  margin: 1rem 0;
  color: #6a4a00;
}
@media (prefers-color-scheme: dark) {
  .flag-callout { background: #2a2418; border-color: #6a4a00; color: #ffe0a0; }
}

footer.site {
  border-top: 1px solid var(--c-border);
  padding: 1.2rem 1.4rem;
  margin-top: 3rem;
  color: var(--c-muted);
  font-size: 0.88em;
  text-align: center;
}
"""


_SEARCH_JS = r"""
// Client-side search over title + body. Loads search-index.json (one big
// blob with title/summary/english/raw concatenated per section) and does
// case-insensitive substring + token-AND matching.
(function () {
  const input = document.getElementById('search-input');
  const grid = document.getElementById('section-grid');
  if (!input || !grid) return;

  let DATA = null;
  let SEARCH = null;
  Promise.all([
    fetch('static/index.json').then(r => r.json()),
    fetch('static/search-index.json').then(r => r.json()),
  ]).then(([idx, sidx]) => {
    DATA = idx;
    SEARCH = sidx;
    render(idx.sections);
  }).catch(() => {
    // search-index missing? fall back to title/number only.
    fetch('static/index.json').then(r => r.json()).then(idx => {
      DATA = idx;
      render(idx.sections);
    });
  });

  function render(rows) {
    grid.innerHTML = '';
    if (rows.length === 0) {
      grid.innerHTML = '<p class="muted">No sections match.</p>';
      return;
    }
    const frag = document.createDocumentFragment();
    for (const row of rows) {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <span class="num">s${row.number}</span>
        <a href="s/${row.number}.html">${escape(row.title || '(untitled)')}</a>
        <div class="badges">
          ${row.L1 ? '<span class="badge l1">L1</span>' : ''}
          ${row.L2 ? '<span class="badge l2">L2</span>' : ''}
          ${badgeForL3(row.L3)}
        </div>
        ${row._snippet ? `<div class="snippet">${row._snippet}</div>` : ''}
      `;
      frag.appendChild(card);
    }
    grid.appendChild(frag);
  }
  function badgeForL3(s) {
    if (!s) return '';
    return `<span class="badge l3-${s}">L3 · ${s}</span>`;
  }
  function escape(s) {
    return (s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function snippet(body, q) {
    const i = body.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return '';
    const start = Math.max(0, i - 30);
    const end = Math.min(body.length, i + q.length + 60);
    let s = (start > 0 ? '…' : '') + body.slice(start, end) + (end < body.length ? '…' : '');
    s = escape(s);
    const reEsc = q.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
    return s.replace(new RegExp(reEsc, 'gi'), m => `<mark>${m}</mark>`);
  }

  input.addEventListener('input', () => {
    if (!DATA) return;
    const q = input.value.trim();
    if (!q) { render(DATA.sections); return; }
    const ql = q.toLowerCase();
    const tokens = ql.split(/\s+/).filter(Boolean);
    const filtered = [];
    for (const row of DATA.sections) {
      const num = row.number.toLowerCase();
      const title = (row.title || '').toLowerCase();
      const body = SEARCH ? (SEARCH[row.number] || '') : '';
      // token-AND across title|number|body
      const hay = `${num}\n${title}\n${body.toLowerCase()}`;
      const allHit = tokens.every(t => hay.includes(t));
      if (!allHit) continue;
      const annotated = Object.assign({}, row);
      // Only show snippet for body matches, not pure title/number hits.
      if (body && !title.includes(ql) && !num.includes(ql)) {
        annotated._snippet = snippet(body, q);
      }
      filtered.push(annotated);
    }
    render(filtered);
  });
})();
"""


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


def _esc(s: Any) -> str:
    return _html.escape("" if s is None else str(s))


def _page(title: str, body: str, *, active_nav: str = "") -> str:
    nav_link = lambda key, label, href: (
        f'<a href="{href}"' + (' aria-current="page"' if active_nav == key else "") + f">{label}</a>"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<header class="site">
  <h1><a href="/" style="color:inherit">Yuho</a></h1>
  <span class="tagline">Singapore Penal Code 1871 — explorer</span>
  <nav>
    {nav_link("index", "Index", "/index.html")}
    {nav_link("coverage", "Coverage", "/coverage.html")}
    {nav_link("flags", "Flags", "/flags.html")}
    {nav_link("about", "About", "/about.html")}
    <a href="https://github.com/gongahkia/yuho">GitHub ↗</a>
  </nav>
</header>
<main>
{body}
</main>
<footer class="site">
  Yuho · proof-of-concept research artefact ·
  <a href="https://gabrielongzm.com">Gabriel Ong Zhe Mian</a> ·
  <a href="https://github.com/gongahkia/yuho">github.com/gongahkia/yuho</a>
</footer>
<script src="/static/search.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------


def render_index(index: Dict[str, Any]) -> str:
    body = f"""
<h2>Browse the Singapore Penal Code 1871</h2>
<p>{_esc(index['n_sections'])} encoded sections.
   <strong>{_esc(index['totals']['L1'])}</strong> pass parse,
   <strong>{_esc(index['totals']['L2'])}</strong> pass lint,
   <strong>{_esc(index['totals']['L3_stamped'])}</strong> human-stamped at the strictest tier.
   <strong style="color:var(--c-l3-flagged)">{_esc(index['totals']['L3_flagged'])}</strong> currently flagged for review.</p>
<div class="searchbar">
  <input id="search-input" type="search" placeholder="Search by section number or title (e.g. 415, cheating, theft)">
</div>
<div id="section-grid" class="grid"><p>Loading…</p></div>
"""
    return _page("Yuho — Singapore Penal Code explorer", body, active_nav="index")


def render_coverage(index: Dict[str, Any]) -> str:
    t = index["totals"]
    body = f"""
<h2>Coverage dashboard</h2>
<p>Latest snapshot regenerated from <code>library/penal_code/_coverage/coverage.json</code> at corpus build time.</p>
<div class="stats">
  <div class="stat"><div class="v">{t['L1']}</div><div class="l">L1 — parses</div></div>
  <div class="stat"><div class="v">{t['L2']}</div><div class="l">L2 — passes lint</div></div>
  <div class="stat"><div class="v">{t['L3_stamped']}</div><div class="l">L3 — human-stamped</div></div>
  <div class="stat"><div class="v">{t['L3_flagged']}</div><div class="l">L3 — flagged</div></div>
  <div class="stat"><div class="v">{t['L3_unstamped']}</div><div class="l">L3 — unstamped</div></div>
  <div class="stat"><div class="v">{index['n_sections']}</div><div class="l">total sections</div></div>
</div>

<h2>Tiers, briefly</h2>
<ul>
  <li><strong>L1 (parse)</strong> — the encoded <code>.yh</code> file passes the tree-sitter grammar.</li>
  <li><strong>L2 (lint)</strong> — the AST builds, semantic checks pass, and the four fidelity diagnostics emit no warnings.</li>
  <li><strong>L3 (human stamp)</strong> — an 11-point checklist over the encoded <code>.yh</code> against the canonical SSO text. Stamping happens via <code>scripts/phase_d_l3_review.py</code>; flags surface here and in <a href="/flags.html">Flags</a>.</li>
</ul>
"""
    return _page("Yuho — Coverage dashboard", body, active_nav="coverage")


def render_flags(index: Dict[str, Any]) -> str:
    flagged = [r for r in index["sections"] if r.get("L3") == "flagged"]
    rows = "".join(
        f'<tr><td><a href="/s/{_esc(r["number"])}.html">s{_esc(r["number"])}</a></td>'
        f'<td>{_esc(r.get("title",""))}</td>'
        f'<td><span class="badge l3-flagged">flagged</span></td></tr>'
        for r in flagged
    )
    body = f"""
<h2>L3 flags ({len(flagged)})</h2>
<p>Sections whose encoding the L3 reviewer (<code>scripts/phase_d_l3_review.py</code>)
flagged for human attention. Each flag includes a numeric checklist failure
code, a reason, and a suggested fix; per-section pages render the full flag
text.</p>
<table class="refs">
  <thead><tr><th>Section</th><th>Title</th><th>Status</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""
    return _page("Yuho — Flags", body, active_nav="flags")


def render_404() -> str:
    body = """
<h2>404 — section not found</h2>
<p>The page you asked for doesn't exist on this site.</p>
<ul>
  <li><a href="/index.html">Index of all 524 sections</a></li>
  <li><a href="/coverage.html">Coverage dashboard</a></li>
  <li><a href="/flags.html">Flagged sections</a></li>
  <li><a href="/about.html">About</a></li>
</ul>
<p>If you arrived from a citation that mentions a specific section number,
try <code>/s/&lt;number&gt;.html</code> directly — e.g.
<a href="/s/415.html">/s/415.html</a> for cheating.</p>
"""
    return _page("Yuho — 404", body)


def render_sitemap(index: Dict[str, Any], base_url: str) -> str:
    """XML sitemap. base_url should not end with a slash."""
    base = base_url.rstrip("/")
    today = _dt.date.today().isoformat()
    urls = [f"{base}/index.html", f"{base}/coverage.html",
            f"{base}/flags.html", f"{base}/about.html"]
    urls.extend(f"{base}/s/{r['number']}.html" for r in index["sections"])
    entries = "".join(
        f"  <url><loc>{_esc(u)}</loc><lastmod>{today}</lastmod></url>\n"
        for u in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'{entries}'
            '</urlset>\n')


def render_robots(base_url: str) -> str:
    base = base_url.rstrip("/")
    return ("User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {base}/sitemap.xml\n")


def render_about() -> str:
    body = """
<h2>About this site</h2>
<p>Yuho is a domain-specific language for encoding statutes as executable,
machine-checkable artefacts. The proof-of-concept corpus encodes the entire
Singapore Penal Code 1871 (524 sections); this site is a public, citable
explorer over that corpus.</p>

<h2>What is each page?</h2>
<ul>
  <li><a href="/index.html">Index</a> — search and browse all 524 sections by number or title.</li>
  <li><a href="/coverage.html">Coverage</a> — three-tier (L1 / L2 / L3) coverage dashboard.</li>
  <li><a href="/flags.html">Flags</a> — sections currently flagged by the L3 reviewer for human attention.</li>
  <li><a href="/s/415.html">Per-section pages</a> — raw SSO text, encoded <code>.yh</code>, controlled English, structural counts, references in/out, and SSO deep-link. Each page is a static citable URL.</li>
</ul>

<h2>Browser extension</h2>
<p>If you spend time reading the Penal Code on
<a href="https://sso.agc.gov.sg/Act/PC1871">Singapore Statutes Online</a>,
the <a href="https://github.com/gongahkia/yuho/tree/main/editors/browser-yuho">Yuho browser extension</a>
overlays the same enrichment directly on SSO pages. Same data; different UX.</p>

<h2>Citation</h2>
<pre class="lite">@software{yuho_2026,
  author  = {Gabriel Ong Zhe Mian},
  title   = {Yuho: A Domain-Specific Language for Encoding the
             Singapore Penal Code as Executable Statute},
  year    = {2026},
  url     = {https://github.com/gongahkia/yuho},
  version = {5.1.0}
}</pre>

<h2>Disclaimer</h2>
<p>This site is a research / educational artefact. It does not provide legal
advice. The encoded statute is a structural representation of the Penal Code
drafted from publicly available SSO text; cross-reference with the
<a href="https://sso.agc.gov.sg/Act/PC1871">canonical SSO source</a> for any
decision that matters.</p>
"""
    return _page("Yuho — About", body, active_nav="about")


def render_section(rec: Dict[str, Any]) -> str:
    cov = rec.get("coverage", {})
    ast = rec.get("encoded", {}).get("ast_summary", {}) or {}
    flag = cov.get("L3_flag")
    title = rec.get("section_title", "")

    flag_html = ""
    if flag:
        flag_html = f"""
<div class="flag-callout">
  <strong>Flagged for L3 review.</strong>
  <p>{_esc(flag.get("reason") or flag.get("raw") or "")}</p>
  {f'<p><em>Suggested fix:</em> {_esc(flag.get("suggested_fix"))}</p>' if flag.get("suggested_fix") else ""}
</div>"""

    badges = []
    if cov.get("L1"): badges.append('<span class="badge l1">L1</span>')
    if cov.get("L2"): badges.append('<span class="badge l2">L2</span>')
    if cov.get("L3"): badges.append(f'<span class="badge l3-{_esc(cov["L3"])}">L3 · {_esc(cov["L3"])}</span>')

    raw_text = rec.get("raw", {}).get("text", "")
    en = rec.get("transpiled", {}).get("english", "")
    yh = rec.get("encoded", {}).get("yh_source", "")
    mermaid_svg = rec.get("transpiled", {}).get("mermaid_svg") or ""

    refs = rec.get("references", {})

    def render_edge_rows(edges, side):
        if not edges:
            return f'<tr><td colspan="3" class="muted">No {side} references.</td></tr>'
        out = []
        for e in edges:
            other = e["dst"] if side == "outgoing" else e["src"]
            snip = _esc(e.get("snippet") or "")
            out.append(
                f'<tr><td><a href="/s/{_esc(other)}.html">s{_esc(other)}</a></td>'
                f'<td><span class="badge l1">{_esc(e["kind"])}</span></td>'
                f'<td>{snip}</td></tr>'
            )
        return "".join(out)

    structural_rows = []
    for label, key in (("Elements", "elements"), ("Illustrations", "illustrations"),
                       ("Subsections", "subsections"), ("Exceptions", "exceptions"),
                       ("Case law", "case_law")):
        v = ast.get(key, 0)
        structural_rows.append(f"<tr><th>{label}</th><td>{_esc(v)}</td></tr>")
    if ast.get("effective_dates"):
        structural_rows.append(f"<tr><th>Effective</th><td>{_esc(', '.join(ast['effective_dates']))}</td></tr>")
    if ast.get("repealed_date"):
        structural_rows.append(f"<tr><th>Repealed</th><td>{_esc(ast['repealed_date'])}</td></tr>")
    if ast.get("subsumes"):
        structural_rows.append(f"<tr><th>Subsumes</th><td><a href=\"/s/{_esc(ast['subsumes'])}.html\">s{_esc(ast['subsumes'])}</a></td></tr>")
    if ast.get("amends"):
        structural_rows.append(f"<tr><th>Amends</th><td><a href=\"/s/{_esc(ast['amends'])}.html\">s{_esc(ast['amends'])}</a></td></tr>")

    summary = rec.get("metadata", {}).get("summary") or rec.get("raw", {}).get("marginal_note") or ""

    body = f"""
<section class="section-page">
  <header>
    <h1><span class="num">s{_esc(rec['section_number'])}</span>{_esc(title)}</h1>
    <div class="meta">
      <span>{' '.join(badges)}</span>
      <span>·</span>
      <a href="{_esc(rec.get('sso_url',''))}" target="_blank" rel="noopener">canonical text on SSO ↗</a>
    </div>
  </header>

  {flag_html}

  {f'<h2>Summary</h2><p>{_esc(summary)}</p>' if summary else ""}

  <h2>Canonical SSO text</h2>
  <pre class="lite">{_esc(raw_text) or "(no raw text)"}</pre>

  {f'<h2>Controlled English</h2><pre class="lite">{_esc(en)}</pre>' if en else ""}

  <h2>Structural counts</h2>
  <table class="refs">
    <tbody>{''.join(structural_rows)}</tbody>
  </table>

  <h2>Outgoing references</h2>
  <table class="refs">
    <thead><tr><th>To</th><th>Kind</th><th>Context</th></tr></thead>
    <tbody>{render_edge_rows(refs.get("outgoing", []), "outgoing")}</tbody>
  </table>

  <h2>Incoming references</h2>
  <table class="refs">
    <thead><tr><th>From</th><th>Kind</th><th>Context</th></tr></thead>
    <tbody>{render_edge_rows(refs.get("incoming", []), "incoming")}</tbody>
  </table>

  {f'<h2>Diagram</h2><div class="diagram">{mermaid_svg}</div>' if mermaid_svg else ""}

  <h2>Encoded <code>.yh</code> source</h2>
  <pre class="src">{_esc(yh) or "(no encoded source)"}</pre>

  <p class="muted" style="font-size:0.85em;margin-top:1.5rem;color:var(--c-muted)">
    raw SHA-256: <code>{_esc(rec.get('raw',{}).get('hash_sha256',''))[:16]}…</code>
    · yuho {_esc(rec.get('provenance',{}).get('yuho_version',''))}
    · generated {_esc(rec.get('provenance',{}).get('generated_at',''))}
  </p>
</section>
"""
    return _page(f"Yuho — s{rec['section_number']} · {title}", body)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--base-url", default="https://yuho.dev",
                    help="absolute base URL used in sitemap.xml + robots.txt (default: https://yuho.dev)")
    args = ap.parse_args()

    if not (CORPUS / "index.json").exists():
        print("error: corpus not built; run scripts/build_corpus.py first.")
        return 1

    BUILD.mkdir(parents=True, exist_ok=True)
    STATIC.mkdir(parents=True, exist_ok=True)
    (BUILD / "s").mkdir(parents=True, exist_ok=True)

    # Load index
    with (CORPUS / "index.json").open("r", encoding="utf-8") as f:
        index = json.load(f)

    # Static assets
    (STATIC / "style.css").write_text(_STYLE)
    (STATIC / "search.js").write_text(_SEARCH_JS)

    # Index.json copy for client-side search
    shutil.copy2(CORPUS / "index.json", STATIC / "index.json")

    # Top-level pages
    (BUILD / "index.html").write_text(render_index(index))
    (BUILD / "coverage.html").write_text(render_coverage(index))
    (BUILD / "flags.html").write_text(render_flags(index))
    (BUILD / "about.html").write_text(render_about())
    (BUILD / "404.html").write_text(render_404())
    (BUILD / "sitemap.xml").write_text(render_sitemap(index, args.base_url))
    (BUILD / "robots.txt").write_text(render_robots(args.base_url))

    # Per-section pages + full-text search index (G2).
    sect_dir = CORPUS / "sections"
    n_pages = 0
    search_index: Dict[str, str] = {}
    for path in sorted(sect_dir.glob("s*.json")):
        with path.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        out = BUILD / "s" / f"{rec['section_number']}.html"
        out.write_text(render_section(rec))
        n_pages += 1
        # Concatenate searchable bodies. Stored lowercased + length-capped
        # so the bundle stays under a few hundred KB.
        parts = [
            rec.get("section_title", ""),
            rec.get("metadata", {}).get("summary") or "",
            rec.get("raw", {}).get("text", "") or "",
            rec.get("transpiled", {}).get("english", "") or "",
        ]
        joined = "\n".join(p for p in parts if p)
        if len(joined) > 4000:
            joined = joined[:4000]
        search_index[rec["section_number"]] = joined

    (STATIC / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, separators=(",", ":"))
    )

    print(f"site built: {BUILD}")
    print(f"  {n_pages} per-section pages")
    print(f"  index.html, coverage.html, flags.html, about.html")
    print(f"  static/{{style.css, search.js, index.json}}")
    print(f"\npreview: python3 -m http.server -d {BUILD.relative_to(REPO)} 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
