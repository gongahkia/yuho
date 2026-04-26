#!/usr/bin/env python3
"""Build the static Penal Code explorer site from the canonical JSON corpus.

Output goes to ``editors/explorer-site/build/``. Layout:

    build/
    ├── index.html            -- searchable index of all 524 sections
    ├── coverage.html         -- L1 / L2 / L3 dashboard
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
import hashlib
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

# Set by main() from --base-path; "" means served from /, "/yuho" means
# every absolute href is prefixed accordingly.
_BASE_PATH: str = ""


def _rewrite_absolute_paths(html_text: str) -> str:
    """Prefix every internal absolute href/src with BASE_PATH.

    Matches ``href="/..."`` and ``src="/..."`` but skips ``//`` (protocol-
    relative) and ``/static/.../external.com`` is not a concern because we
    only ever emit our own paths.
    """
    if not _BASE_PATH:
        return html_text
    import re as _re
    pat = _re.compile(r'(href|src)="(/(?!/)[^"]*)"')
    return pat.sub(lambda m: f'{m.group(1)}="{_BASE_PATH}{m.group(2)}"', html_text)


# ---------------------------------------------------------------------------
# Style + scripts
# ---------------------------------------------------------------------------


_STYLE = r"""
/* SSO-inspired palette: dark crimson header, white body, light grey
   row separators, SSO blue links, dark teal section headings. */
:root {
  --c-bg: #ffffff;
  --c-fg: #1a1a22;
  --c-muted: #6a6a75;
  --c-card: #ffffff;
  --c-border: #d0d0d0;
  --c-accent: #0066CC;            /* SSO link blue */
  --c-header-bg: #8C1313;         /* SSO dark crimson */
  --c-header-fg: #ffffff;
  --c-heading: #1B5045;           /* SSO dark teal */
  --c-row-alt: #fafafa;
  --c-row-hover: #fff8f0;
  --c-status: #8C1313;
  --c-l3-stamped: #1a8b3a;
  --c-l3-flagged: #c43d3d;
  --c-l3-unstamped: #b07020;
}

* { box-sizing: border-box; }
html { font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
body { margin: 0; background: var(--c-bg); color: var(--c-fg); }

a { color: var(--c-accent); text-decoration: none; }
a:hover { text-decoration: underline; }

header.site {
  background: var(--c-header-bg);
  color: var(--c-header-fg);
  padding: 1.4rem 1.4rem 1.6rem;
  display: flex;
  align-items: baseline;
  gap: 1.2rem;
  flex-wrap: wrap;
  border-bottom: 3px solid #5C0A0A;
}
header.site h1 { margin: 0; font-size: 1.4rem; font-weight: 700; letter-spacing: 0.02em; }
header.site h1 a.brand { color: inherit; text-decoration: none; }
header.site h1 a.brand:hover { text-decoration: underline; }

.skip-link {
  position: absolute;
  left: -9999px;
  top: auto;
  padding: 0.5rem 0.9rem;
  background: var(--c-fg);
  color: var(--c-bg);
  z-index: 100;
  border-radius: 0 0 6px 0;
}
.skip-link:focus { left: 0; top: 0; outline: 2px solid var(--c-accent); }

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
header.site nav { margin-left: auto; display: flex; gap: 1.2rem; font-size: 0.95em; }
header.site nav a { color: #fff; opacity: 0.92; }
header.site nav a:hover { opacity: 1; text-decoration: underline; }
header.site .tagline { font-size: 0.92em; opacity: 0.92; }

main {
  max-width: 70rem;
  margin: 0 auto;
  padding: 1.6rem 1.4rem 4rem;
}

h2 { margin-top: 2.2em; font-size: 1.1rem; font-weight: 600; color: var(--c-heading); }
h2:first-child { margin-top: 0; }

/* Row-based section listing (SSO-style table layout). */
.section-list {
  margin: 1rem 0 2rem;
  border-top: 1px solid var(--c-border);
}
.section-row {
  display: grid;
  grid-template-columns: 5rem 1fr auto;
  gap: 1rem;
  align-items: center;
  padding: 0.7rem 0.9rem;
  border-bottom: 1px solid var(--c-border);
  background: var(--c-card);
  transition: background-color 0.06s ease-out;
}
.section-row:nth-child(even) { background: var(--c-row-alt); }
.section-row:hover { background: var(--c-row-hover); }
.section-row .num {
  color: var(--c-muted);
  font-family: ui-monospace, monospace;
  font-size: 0.95em;
  font-weight: 600;
}
.section-row .title-cell {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.section-row .title-cell a {
  color: var(--c-fg);
  font-weight: 600;
  font-size: 0.97em;
}
.section-row .title-cell a:hover { color: var(--c-accent); }
.section-row .badges { display: flex; gap: 0.3rem; flex-wrap: wrap; align-items: center; }
.section-row .snippet {
  font-size: 0.83em;
  color: var(--c-muted);
  line-height: 1.35;
  margin-top: 0.15em;
}
.section-row .snippet mark {
  background: #ffe066;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}
@media (max-width: 50rem) {
  .section-row { grid-template-columns: 4rem 1fr; }
  .section-row .badges { grid-column: 1 / -1; padding-left: 4rem; }
}

.about-hero {
  display: flex;
  gap: 1.4rem;
  align-items: center;
  margin: 1rem 0 2rem;
  padding: 1.2rem;
  background: var(--c-row-alt);
  border: 1px solid var(--c-border);
  border-radius: 6px;
}
.about-hero .mascot {
  width: 140px;
  height: auto;
  flex-shrink: 0;
}
.about-hero h2 { margin-top: 0; }
@media (max-width: 38rem) {
  .about-hero { flex-direction: column; text-align: center; }
}

/* Cross-reference graph page. */
.graph-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin: 0.6rem 0;
  flex-wrap: wrap;
}
.graph-controls input[type="search"] {
  flex-grow: 1;
  min-width: 14rem;
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--c-border);
  border-radius: 4px;
  font: inherit;
}
#graph-canvas {
  width: 100%;
  height: 70vh;
  min-height: 30rem;
  border: 1px solid var(--c-border);
  border-radius: 4px;
  background: var(--c-row-alt);
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

table.cov-table th[data-sort] { cursor: pointer; user-select: none; }
table.cov-table th[data-sort]:hover { color: var(--c-accent); }
table.cov-table th[data-sort].asc::after  { content: " ▲"; font-size: 0.7em; color: var(--c-accent); }
table.cov-table th[data-sort].desc::after { content: " ▼"; font-size: 0.7em; color: var(--c-accent); }
table.cov-table td.cov-cell { text-align: center; font-family: ui-monospace, monospace; }
table.cov-table td.cov-num,
table.cov-table th.cov-num  { text-align: right; font-variant-numeric: tabular-nums; }
input.cov-filter {
  width: 100%;
  margin: 0.4em 0 0.6em;
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  background: var(--c-card);
  color: var(--c-fg);
}

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
section.section-page .downloads { font-family: ui-monospace, monospace; font-size: 0.88em; }
section.section-page .downloads a { color: var(--c-accent); margin: 0 0.05em; }

.breadcrumb {
  font-size: 0.85em;
  color: var(--c-muted);
  margin-bottom: 0.6rem;
}
.breadcrumb a { color: var(--c-muted); }
.breadcrumb a:hover { color: var(--c-accent); }
.breadcrumb [aria-current] { color: var(--c-fg); font-weight: 600; }

.toc {
  background: var(--c-card);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  padding: 0.6rem 0.9rem;
  margin: 1rem 0 1.4rem;
  font-size: 0.88em;
}
.toc ul { margin: 0; padding-left: 1.1rem; columns: 2; column-gap: 1.2rem; }
.toc li { margin: 0.15em 0; }

.prevnext {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
  margin: 1.6rem 0 0.6rem;
}
.navchip {
  display: flex;
  flex-direction: column;
  gap: 0.15em;
  padding: 0.55rem 0.7rem;
  background: var(--c-card);
  border: 1px solid var(--c-border);
  border-radius: 6px;
  color: var(--c-fg);
  text-decoration: none;
}
.navchip:hover { border-color: var(--c-accent); text-decoration: none; }
.navchip .dir { font-size: 0.75em; color: var(--c-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.navchip:nth-child(2) { text-align: right; }
.navchip .num { font: 600 0.95em ui-monospace, monospace; color: var(--c-accent); }
.navchip .ttl { font-size: 0.92em; line-height: 1.3; }
.navchip.empty {
  background: transparent;
  border-style: dashed;
  color: var(--c-muted);
  font-size: 0.85em;
  align-items: center;
  justify-content: center;
  display: flex;
}

/* Counter-example explorer pages (Tier 3 #8) */
.explore-list { margin: 0.4em 0 1em 1.2em; padding: 0; }
.explore-list li { margin: 0.2em 0; line-height: 1.4; }
.elem-t {
  display: inline-block; padding: 0 0.4em; margin: 0 0.18em 0.18em 0;
  background: #e8f5e9; color: #1f6f2c; border-radius: 3px;
  font: 600 0.78em ui-monospace, monospace;
}
.elem-f {
  display: inline-block; padding: 0 0.4em; margin: 0 0.18em 0.18em 0;
  background: #ffeaea; color: #a8302a; border-radius: 3px;
  font: 600 0.78em ui-monospace, monospace;
}
@media (prefers-color-scheme: dark) {
  .elem-t { background: #1f3622; color: #6fdb88; }
  .elem-f { background: #401818; color: #ff8888; }
}

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

@media print {
  /* G7: print-friendly. Force light theme, drop the gradient header,
     ink-saving pres, hide non-essential UI. */
  :root {
    --c-bg: #ffffff;
    --c-fg: #000000;
    --c-muted: #555555;
    --c-card: #ffffff;
    --c-border: #cccccc;
  }
  html, body { background: #fff; color: #000; }
  header.site {
    background: #fff !important;
    color: #000 !important;
    border-bottom: 1px solid #999;
    padding: 0.6rem 0;
  }
  header.site h1 a { color: #000 !important; }
  header.site nav,
  header.site nav a,
  .searchbar,
  #section-grid,
  .prevnext,
  .toc,
  footer.site { display: none !important; }
  pre.src {
    background: #fff !important;
    color: #000 !important;
    border: 1px solid #999;
    page-break-inside: avoid;
  }
  pre.lite { border: 1px solid #999; page-break-inside: avoid; }
  .diagram { border: 1px solid #999; page-break-inside: avoid; }
  .badge { border: 1px solid #999; background: #fff !important; color: #000 !important; }
  a { color: #000; text-decoration: underline; }
  /* Expose link targets in print */
  section.section-page a[href^="http"]::after {
    content: " (" attr(href) ")";
    font-size: 0.85em;
    color: #555;
    word-break: break-all;
  }
  h2 { page-break-after: avoid; }
}
"""


_SEMANTIC_GRAPH_JS = r"""
// Semantic graph: typed nodes (section / definition / element /
// exception) and typed edges (contains / mentions / defeats /
// shares_term). Interaction: filter pins one section's neighbourhood,
// toggles hide noisy edge kinds. Click a section node to navigate to
// its per-section page; click any other node to focus its neighbours.
(function () {
  const canvas = document.getElementById('graph-canvas');
  if (!canvas || typeof cytoscape !== 'function') return;

  const filterInput = document.getElementById('semgraph-filter');
  const hideMentions = document.getElementById('hide-mentions');
  const hideShares = document.getElementById('hide-shares');

  fetch('static/semantic-graph.json')
    .then(r => r.json())
    .then(boot)
    .catch(err => {
      canvas.innerHTML = '<p class="muted" style="padding:2rem">' +
        'Failed to load semantic graph: ' + (err && err.message || err) + '</p>';
    });

  function boot(data) {
    const elements = [];
    for (const n of (data.nodes || [])) {
      elements.push({
        data: { id: n.id, label: n.label, kind: n.kind, section: n.section,
                element_type: n.element_type || '' },
      });
    }
    for (const e of (data.edges || [])) {
      elements.push({
        data: { id: `${e.kind}:${e.src}>${e.dst}`,
                source: e.src, target: e.dst, kind: e.kind, snippet: e.snippet || '' },
      });
    }

    const cy = cytoscape({
      container: canvas,
      elements: elements,
      wheelSensitivity: 0.2,
      style: [
        { selector: 'node[kind = "section"]',
          style: { 'background-color': '#8C1313', 'shape': 'round-rectangle',
                   'label': 'data(label)', 'color': '#ffffff', 'font-size': '8px',
                   'text-valign': 'center', 'text-halign': 'center',
                   'width': 50, 'height': 18, 'overlay-padding': 4 } },
        { selector: 'node[kind = "definition"]',
          style: { 'background-color': '#1B5045', 'shape': 'diamond',
                   'label': 'data(label)', 'font-size': '7px',
                   'text-valign': 'center', 'text-halign': 'center',
                   'color': '#ffffff', 'width': 14, 'height': 14 } },
        { selector: 'node[kind = "element"]',
          style: { 'background-color': '#0066CC', 'shape': 'ellipse',
                   'label': 'data(label)', 'font-size': '7px',
                   'text-valign': 'center', 'text-halign': 'center',
                   'color': '#ffffff', 'width': 14, 'height': 14 } },
        { selector: 'node[kind = "exception"]',
          style: { 'background-color': '#b07020', 'shape': 'triangle',
                   'label': 'data(label)', 'font-size': '7px',
                   'text-valign': 'center', 'text-halign': 'center',
                   'color': '#ffffff', 'width': 14, 'height': 14 } },
        { selector: 'node:selected',
          style: { 'border-width': 3, 'border-color': '#0066CC' } },
        { selector: 'node.dim', style: { 'opacity': 0.1 } },
        { selector: 'edge',
          style: { 'curve-style': 'bezier', 'target-arrow-shape': 'triangle',
                   'arrow-scale': 0.5, 'width': 1, 'opacity': 0.45 } },
        { selector: 'edge[kind = "contains"]',
          style: { 'line-color': '#cccccc', 'target-arrow-color': '#cccccc',
                   'opacity': 0.4 } },
        { selector: 'edge[kind = "mentions"]',
          style: { 'line-color': '#0066CC', 'target-arrow-color': '#0066CC',
                   'line-style': 'dashed' } },
        { selector: 'edge[kind = "defeats"]',
          style: { 'line-color': '#b07020', 'target-arrow-color': '#b07020',
                   'width': 2 } },
        { selector: 'edge[kind = "shares_term"]',
          style: { 'line-color': '#1B5045', 'target-arrow-color': '#1B5045',
                   'line-style': 'dotted', 'opacity': 0.7,
                   'target-arrow-shape': 'none' } },
        { selector: 'edge.hidden', style: { 'display': 'none' } },
      ],
      layout: {
        name: 'cose', animate: false, nodeRepulsion: 3000,
        idealEdgeLength: 50, edgeElasticity: 80,
      },
    });

    cy.on('tap', 'node[kind = "section"]', evt => {
      const section = evt.target.data('section');
      if (section) window.location.href = 's/' + section + '.html';
    });

    cy.on('tap', 'node[kind != "section"]', evt => {
      // Focus: dim everything except the tapped node + its 1-hop neighbours.
      cy.nodes().addClass('dim');
      const n = evt.target;
      n.removeClass('dim');
      n.neighborhood().removeClass('dim');
    });

    if (hideMentions) {
      hideMentions.addEventListener('change', () => {
        cy.edges('[kind = "mentions"]').toggleClass('hidden', hideMentions.checked);
      });
    }
    if (hideShares) {
      hideShares.addEventListener('change', () => {
        cy.edges('[kind = "shares_term"]').toggleClass('hidden', hideShares.checked);
      });
    }

    if (filterInput) {
      filterInput.addEventListener('input', () => {
        const q = filterInput.value.trim().toLowerCase();
        if (!q) {
          cy.nodes().removeClass('dim');
          return;
        }
        cy.nodes().forEach(n => {
          const matches = n.data('section').toLowerCase().includes(q);
          n.toggleClass('dim', !matches);
        });
      });
    }
  }
})();
"""


_GRAPH_JS = r"""
// Reference-graph page: load static/graph.json and render via cytoscape.
(function () {
  const canvas = document.getElementById('graph-canvas');
  if (!canvas || typeof cytoscape !== 'function') return;

  const filterInput = document.getElementById('graph-filter');
  const hideImplicit = document.getElementById('hide-implicit');

  fetch('static/graph.json')
    .then(r => r.json())
    .then(data => boot(data))
    .catch(err => {
      canvas.innerHTML = '<p class="muted" style="padding:2rem">' +
        'Failed to load graph data: ' + (err && err.message || err) + '</p>';
    });

  function boot(data) {
    const elements = [];
    for (const id of (data.nodes || [])) {
      elements.push({
        data: { id: 's' + id, label: 's' + id, sectionId: id },
      });
    }
    for (const e of (data.edges || [])) {
      elements.push({
        data: {
          id: 'e_' + e.src + '_' + e.dst + '_' + e.kind,
          source: 's' + e.src,
          target: 's' + e.dst,
          kind: e.kind,
        },
      });
    }
    const cy = cytoscape({
      container: canvas,
      elements: elements,
      wheelSensitivity: 0.2,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#8C1313',
            'color': '#ffffff',
            'label': 'data(label)',
            'font-size': '8px',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': 18,
            'height': 18,
            'overlay-padding': 4,
          },
        },
        {
          selector: 'node:selected',
          style: { 'background-color': '#0066CC', 'border-width': 2, 'border-color': '#003366' },
        },
        {
          selector: 'node.dim',
          style: { 'opacity': 0.15 },
        },
        {
          selector: 'edge',
          style: {
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.6,
            'width': 1,
            'opacity': 0.55,
          },
        },
        {
          selector: 'edge[kind = "subsumes"]',
          style: { 'line-color': '#0066CC', 'target-arrow-color': '#0066CC' },
        },
        {
          selector: 'edge[kind = "amends"]',
          style: { 'line-color': '#1B5045', 'target-arrow-color': '#1B5045' },
        },
        {
          selector: 'edge[kind = "implicit"]',
          style: { 'line-color': '#8C8C8C', 'target-arrow-color': '#8C8C8C', 'line-style': 'dashed' },
        },
        {
          selector: 'edge.hidden',
          style: { 'display': 'none' },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: 5000,
        idealEdgeLength: 60,
        edgeElasticity: 100,
      },
    });

    cy.on('tap', 'node', evt => {
      const id = evt.target.data('sectionId');
      if (id) window.location.href = 's/' + id + '.html';
    });

    if (hideImplicit) {
      hideImplicit.addEventListener('change', () => {
        const on = hideImplicit.checked;
        cy.edges('[kind = "implicit"]').toggleClass('hidden', on);
      });
    }

    if (filterInput) {
      filterInput.addEventListener('input', () => {
        const q = filterInput.value.trim().toLowerCase();
        if (!q) {
          cy.nodes().removeClass('dim');
          return;
        }
        cy.nodes().forEach(n => {
          const matches = n.data('sectionId').toLowerCase().includes(q);
          n.toggleClass('dim', !matches);
        });
      });
    }
  }
})();
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
      const r = document.createElement('div');
      r.className = 'section-row';
      r.innerHTML = `
        <span class="num">s${row.number}</span>
        <div class="title-cell">
          <a href="s/${row.number}.html">${escape(row.title || '(untitled)')}</a>
          ${row._snippet ? `<div class="snippet">${row._snippet}</div>` : ''}
        </div>
        <div class="badges">
          ${row.L1 ? '<span class="badge l1">L1</span>' : ''}
          ${row.L2 ? '<span class="badge l2">L2</span>' : ''}
          ${badgeForL3(row.L3)}
        </div>
      `;
      frag.appendChild(r);
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

// Coverage table filter + sort. No-op when the table isn't present.
(function () {
  const table = document.getElementById('coverage-table');
  const filter = document.getElementById('coverage-filter');
  if (!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);

  if (filter) {
    filter.addEventListener('input', () => {
      const q = filter.value.trim().toLowerCase();
      for (const tr of rows) {
        tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none';
      }
    });
  }

  let sortState = { col: -1, dir: 1 };
  const heads = table.tHead.rows[0].cells;
  for (let i = 0; i < heads.length; i++) {
    const th = heads[i];
    if (!th.dataset.sort) continue;
    th.addEventListener('click', () => {
      const dir = (sortState.col === i) ? -sortState.dir : 1;
      sortState = { col: i, dir };
      for (const h of heads) h.classList.remove('asc', 'desc');
      th.classList.add(dir > 0 ? 'asc' : 'desc');
      const kind = th.dataset.sort;
      const visibleRows = rows.slice();
      visibleRows.sort((a, b) => {
        const av = a.cells[i].textContent.trim();
        const bv = b.cells[i].textContent.trim();
        let cmp;
        if (kind === 'num') {
          // Pull leading integer; non-numeric sorts as -1.
          const an = parseFloat(av) || 0;
          const bn = parseFloat(bv) || 0;
          cmp = an - bn;
        } else if (kind === 'bool') {
          cmp = (av === '✓' ? 1 : 0) - (bv === '✓' ? 1 : 0);
        } else {
          cmp = av.localeCompare(bv);
        }
        return cmp * dir;
      });
      tbody.replaceChildren(...visibleRows);
    });
  }
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
    html_text = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<link rel="icon" type="image/x-icon" href="/static/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png">
<link rel="apple-touch-icon" href="/static/yuho_mascot.png">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site">
  <h1><a href="/" class="brand">Yuho</a></h1>
  <span class="tagline">Singapore Penal Code 1871 — explorer</span>
  <nav aria-label="Primary">
    {nav_link("index", "Index", "/index.html")}
    {nav_link("coverage", "Coverage", "/coverage.html")}
    {nav_link("graph", "Graph", "/graph.html")}
    {nav_link("semantic-graph", "Semantic", "/semantic-graph.html")}
    {nav_link("about", "About", "/about.html")}
    <a href="https://github.com/gongahkia/yuho">GitHub ↗</a>
  </nav>
</header>
<main id="main-content">
{body}
</main>
<footer class="site">
  <a href="https://github.com/gongahkia/yuho">Yuho</a> ·
  <a href="https://gabrielongzm.com">Gabriel Ong Zhe Mian</a>
</footer>
<script src="/static/search.js" defer></script>
</body>
</html>
"""
    return _rewrite_absolute_paths(html_text)


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
  <label for="search-input" class="visually-hidden">Search sections</label>
  <input id="search-input" type="search" autocomplete="off"
         aria-controls="section-grid"
         placeholder="Search by section number, title, element wording (e.g. 415, cheating, induces delivery)">
</div>
<div id="section-grid" class="section-list" role="region" aria-label="Section results" aria-live="polite"><p>Loading…</p></div>
"""
    return _page("Yuho — Singapore Penal Code explorer", body, active_nav="index")


def render_coverage(index: Dict[str, Any]) -> str:
    t = index["totals"]

    def _badge_for_l3(s: str) -> str:
        return f'<span class="badge l3-{_esc(s)}">{_esc(s)}</span>'

    rows = []
    for r in index["sections"]:
        cell_l1 = "✓" if r.get("L1") else "—"
        cell_l2 = "✓" if r.get("L2") else "—"
        l3 = r.get("L3", "")
        rows.append(
            f'<tr>'
            f'<td><a href="/s/{_esc(r["number"])}.html">s{_esc(r["number"])}</a></td>'
            f'<td>{_esc(r.get("title",""))}</td>'
            f'<td class="cov-cell">{cell_l1}</td>'
            f'<td class="cov-cell">{cell_l2}</td>'
            f'<td>{_badge_for_l3(l3) if l3 else "—"}</td>'
            f'<td class="cov-num">{_esc(r.get("elements",0))}</td>'
            f'<td class="cov-num">{_esc(r.get("outgoing_refs",0))}/{_esc(r.get("incoming_refs",0))}</td>'
            f'</tr>'
        )

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
  <li><strong>L3 (human stamp)</strong> — an 11-point checklist over the encoded <code>.yh</code> against the canonical SSO text. Stamping happens via <code>scripts/l3_audit.py</code>; any flagged sections are noted on the per-section page.</li>
</ul>

<h2 id="per-section">Per-section coverage</h2>
<p class="muted" style="font-size:0.9em">Type below to filter; columns are sortable by clicking the header.</p>
<input id="coverage-filter" type="search" autocomplete="off"
       placeholder="Filter by section number, title, or L3 status…"
       aria-controls="coverage-table" class="cov-filter">
<table id="coverage-table" class="refs cov-table">
  <thead><tr>
    <th data-sort="num">#</th>
    <th data-sort="text">Title</th>
    <th data-sort="bool">L1</th>
    <th data-sort="bool">L2</th>
    <th data-sort="text">L3</th>
    <th data-sort="num" class="cov-num">Elements</th>
    <th data-sort="text" class="cov-num">Refs out/in</th>
  </tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table>
"""
    return _page("Yuho — Coverage dashboard", body, active_nav="coverage")


def render_semantic_graph(graph_data: Dict[str, Any]) -> str:
    """Library-wide semantic graph (definitions / elements / exceptions
    across all 524 sections). Different shape from the section-granular
    /graph.html: nodes here are typed (section / definition / element /
    exception), edges typed (contains / mentions / defeats / shares_term).

    Reuses the same cytoscape.js layout the reference graph uses; the
    JS in /static/semantic-graph.js styles by node + edge kind.
    """
    stats = graph_data.get("stats", {})
    body = f"""
<h2>Semantic graph</h2>
<p class="muted">
  {stats.get('n_section', 0)} sections ·
  {stats.get('n_definition', 0)} definitions ·
  {stats.get('n_element', 0)} elements ·
  {stats.get('n_exception', 0)} exceptions ·
  {stats.get('n_mentions', 0)} term-mention edges ·
  {stats.get('n_defeats', 0)} defeats edges ·
  {stats.get('n_shares_term', 0)} cross-section shared-term edges.
  Drag to pan, scroll to zoom; the graph is large — pin a section by
  number to focus its neighbourhood.
</p>

<div id="graph-controls" class="graph-controls">
  <input type="search" id="semgraph-filter" placeholder="Pin a section by number (e.g. 415)..." aria-controls="graph-canvas">
  <label class="muted">
    <input type="checkbox" id="hide-mentions"> hide term-mention edges
  </label>
  <label class="muted">
    <input type="checkbox" id="hide-shares"> hide shared-term edges
  </label>
  <a class="muted" href="/static/semantic-graph.json">semantic-graph.json</a>
</div>
<div id="graph-canvas" role="img" aria-label="Semantic graph"></div>

<script src="https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js"></script>
<script src="/static/semantic-graph.js" defer></script>
"""
    return _page("Yuho — Semantic graph", body, active_nav="semantic-graph")


def render_graph(graph_data: Dict[str, Any]) -> str:
    """Static reference-graph page with cytoscape.js client-side render.

    Reads ``static/graph.json`` (emitted at build time from the same
    :class:`yuho.library.reference_graph.ReferenceGraph` the CLI's
    ``yuho refs --scc`` consumes) and lays out a directed graph of all
    cross-section references. Nodes link back to per-section pages so
    the page acts as a navigable knowledge-graph view.
    """
    n_nodes = len(graph_data.get("nodes", []))
    n_edges = len(graph_data.get("edges", []))
    body = f"""
<h2>Cross-section reference graph</h2>
<p class="muted">
  {n_nodes} sections · {n_edges} edges
  ({graph_data.get('stats', {}).get('n_subsumes', 0)} subsumes,
   {graph_data.get('stats', {}).get('n_amends', 0)} amends,
   {graph_data.get('stats', {}).get('n_implicit', 0)} implicit).
  Drag to pan, scroll to zoom, click a section to open its page.
  Coloured edges: <span style="color:#0066CC">blue=subsumes</span>,
  <span style="color:#1B5045">teal=amends</span>,
  <span style="color:#8C8C8C">grey=implicit</span>.
</p>

<div id="graph-controls" class="graph-controls">
  <input type="search" id="graph-filter" placeholder="Highlight sections by number..." aria-controls="graph-canvas">
  <label class="muted">
    <input type="checkbox" id="hide-implicit"> hide implicit edges
  </label>
  <a class="muted" href="/static/graph.json">graph.json</a>
</div>
<div id="graph-canvas" role="img" aria-label="Cross-section reference graph"></div>

<script src="https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js"></script>
<script src="/static/graph.js" defer></script>
"""
    return _page("Yuho — Cross-reference graph", body, active_nav="graph")


def render_404() -> str:
    body = """
<h2>404 — section not found</h2>
<p>The page you asked for doesn't exist on this site.</p>
<ul>
  <li><a href="/index.html">Index of all 524 sections</a></li>
  <li><a href="/coverage.html">Coverage dashboard</a></li>
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
            f"{base}/graph.html", f"{base}/semantic-graph.html",
            f"{base}/about.html"]
    urls.extend(f"{base}/s/{r['number']}.html" for r in index["sections"])
    urls.extend(f"{base}/explore/{r['number']}.html" for r in index["sections"])
    entries = "".join(
        f"  <url><loc>{_esc(u)}</loc><lastmod>{today}</lastmod></url>\n"
        for u in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'{entries}'
            '</urlset>\n')


def render_explore_page(rec: Dict[str, Any], explore_payload: Dict[str, Any]) -> str:
    """Render a static counter-example explorer page for one section.

    Layered on top of the same _page() chrome as the section pages.
    Reads the pre-rendered explorer report (from build_explore.py),
    falls back to a "not yet rendered" placeholder when absent.
    """
    n = rec["section_number"]
    title = rec.get("section_title", "")
    if not explore_payload or not explore_payload.get("available"):
        body = f"""
<section class="section-page">
  <nav class="breadcrumb"><a href="/index.html">Index</a> ›
    <a href="/s/{_esc(n)}.html">s{_esc(n)}</a> ›
    <span aria-current="page">explore</span></nav>
  <header><h1><span class="num">s{_esc(n)}</span>{_esc(title)} — counter-examples</h1></header>
  <p class="muted">No pre-rendered explorer report available for this section.
  Run <code>python3 editors/browser-yuho/build_explore.py --section {_esc(n)}</code>
  to generate one. Reasons typically include: Z3 not installed, the section's
  encoding has no top-level elements, or the parser failed.</p>
</section>
"""
        return _page(f"Yuho — s{n} counter-examples", body)

    s = explore_payload.get("summary") or {}
    sat_html = ""
    if explore_payload.get("satisfying"):
        items = []
        for i, scen in enumerate(explore_payload["satisfying"], 1):
            tags = "".join(
                f'<span class="elem-{("t" if v else "f")}">{_esc(k)}</span>'
                for k, v in (scen.get("elements") or {}).items()
            )
            items.append(f'<li><strong>#{i}</strong> {tags}</li>')
        sat_html = f"<h2>Satisfying scenarios</h2><ul class='explore-list'>{''.join(items)}</ul>"
    else:
        sat_html = "<h2>Satisfying scenarios</h2><p class='muted'>None found — conviction may be unreachable.</p>"

    bord_html = ""
    if explore_payload.get("borderline"):
        items = []
        for scen in explore_payload["borderline"]:
            f_keys = [k for k, v in (scen.get("elements") or {}).items() if not v]
            if f_keys:
                items.append(f'<li>fails when missing: {_esc(", ".join(f_keys))}</li>')
        if items:
            bord_html = f"<h2>Load-bearing elements</h2><ul class='explore-list'>{''.join(items)}</ul>"

    exc_html = ""
    if explore_payload.get("exception_coverage"):
        items = []
        for e in explore_payload["exception_coverage"]:
            label = "REACHABLE" if e.get("reachable") is True else (
                "DEAD" if e.get("reachable") is False else "UNKNOWN"
            )
            items.append(f"<li>{_esc(e['exception'])} — {label}</li>")
        exc_html = f"<h2>Exception coverage</h2><ul class='explore-list'>{''.join(items)}</ul>"

    body = f"""
<section class="section-page">
  <nav class="breadcrumb">
    <a href="/index.html">Index</a> ›
    <a href="/s/{_esc(n)}.html">s{_esc(n)}</a> ›
    <span aria-current="page">explore</span>
  </nav>
  <header>
    <h1><span class="num">s{_esc(n)}</span>{_esc(title)} — counter-examples</h1>
    <div class="meta">
      <span>Pre-rendered structural witnesses from the Z3 verifier.</span>
      <span>·</span>
      <a href="/s/{_esc(n)}.html">back to section page</a>
    </div>
  </header>
  <h2>Summary</h2>
  <table class="refs">
    <tr><th>Elements</th><td>{s.get('n_leaf_elements', 0)}</td></tr>
    <tr><th>Exceptions</th><td>{s.get('n_exceptions', 0)}</td></tr>
    <tr><th>Conviction reachable</th><td>{'yes' if s.get('conviction_reachable') else 'no'}</td></tr>
    <tr><th>Load-bearing elements</th><td>{s.get('n_load_bearing', 0)}</td></tr>
    <tr><th>Dead exceptions</th><td>{s.get('n_dead_exceptions', 0)}</td></tr>
  </table>
  {sat_html}
  {bord_html}
  {exc_html}
  <p class="muted" style="font-size:0.85em;margin-top:1.5rem">
    Counter-example exploration is structural only — it surfaces fact-pattern
    witnesses over the encoded grammar, not legal conclusions. Cross-reference
    the <a href="https://sso.agc.gov.sg/Act/PC1871">canonical SSO text</a>.
  </p>
</section>
"""
    return _page(f"Yuho — s{n} counter-examples", body)


def render_robots(base_url: str) -> str:
    base = base_url.rstrip("/")
    return ("User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {base}/sitemap.xml\n")


def render_about() -> str:
    body = """
<div class="about-hero">
  <img src="/static/yuho_mascot.png" alt="Yuho mascot" class="mascot">
  <div>
    <h2>About this site</h2>
    <p>Yuho is a domain-specific language for encoding statutes as
    executable, machine-checkable artefacts. The corpus encodes the
    entire Singapore Penal Code 1871 (524 sections); this site is a
    public, citable explorer over that corpus.</p>
  </div>
</div>

<h2>What is each page?</h2>
<ul>
  <li><a href="/index.html">Index</a> — search and browse all 524 sections by number or title.</li>
  <li><a href="/coverage.html">Coverage</a> — three-tier (L1 / L2 / L3) coverage dashboard.</li>
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


def render_section(rec: Dict[str, Any],
                   *,
                   prev_rec: Optional[Dict[str, Any]] = None,
                   next_rec: Optional[Dict[str, Any]] = None) -> str:
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
    mindmap_svg = rec.get("transpiled", {}).get("mindmap_svg") or ""

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

    # Section anchors are stable IDs we can link to and that the in-page TOC
    # references. Each <h2> gets one of these.
    sections_present = [("summary", "Summary", bool(summary)),
                        ("canonical", "Canonical SSO text", True),
                        ("english", "Controlled English", bool(en)),
                        ("structural", "Structural counts", True),
                        ("refs-out", "Outgoing references", True),
                        ("refs-in", "Incoming references", True),
                        ("diagram", "Diagram", bool(mermaid_svg)),
                        ("mindmap", "Mindmap", bool(mindmap_svg)),
                        ("source", "Encoded .yh source", True)]
    toc_items = "".join(
        f'<li><a href="#{aid}">{_esc(label)}</a></li>'
        for aid, label, present in sections_present if present
    )
    toc_html = f'<nav class="toc" aria-label="On this page"><ul>{toc_items}</ul></nav>'

    breadcrumb = (
        '<nav class="breadcrumb" aria-label="Breadcrumb">'
        '<a href="/index.html">Index</a> ›'
        f' <span aria-current="page">s{_esc(rec["section_number"])}</span>'
        '</nav>'
    )

    def _navchip(side, r):
        if not r:
            return f'<span class="navchip empty">{_esc(side)}</span>'
        return (
            f'<a class="navchip" href="/s/{_esc(r["number"])}.html">'
            f'<span class="dir">{_esc(side)}</span>'
            f'<span class="num">s{_esc(r["number"])}</span>'
            f'<span class="ttl">{_esc(r.get("title","") or "")}</span>'
            f'</a>'
        )
    nav_html = (
        '<nav class="prevnext" aria-label="Section navigation">'
        f'{_navchip("← prev", prev_rec)}'
        f'{_navchip("next →", next_rec)}'
        '</nav>'
    )

    n = rec["section_number"]
    download_html = (
        f'<span>·</span>'
        f'<span class="downloads">downloads: '
        f'<a href="/s/{_esc(n)}.json">JSON</a>'
        f' · <a href="/s/{_esc(n)}.yh">.yh</a>'
        f'{f"" if not en else f" · <a href=\"/s/{_esc(n)}.en.txt\">English</a>"}'
        f'</span>'
        f'<span>·</span>'
        f'<a href="/explore/{_esc(n)}.html">explore counter-examples</a>'
    )

    body = f"""
<section class="section-page">
  {breadcrumb}
  <header>
    <h1><span class="num">s{_esc(rec['section_number'])}</span>{_esc(title)}</h1>
    <div class="meta">
      <span>{' '.join(badges)}</span>
      <span>·</span>
      <a href="{_esc(rec.get('sso_url',''))}" target="_blank" rel="noopener">canonical text on SSO ↗</a>
      {download_html}
    </div>
  </header>

  {flag_html}

  {toc_html}

  {f'<h2 id="summary">Summary</h2><p>{_esc(summary)}</p>' if summary else ""}

  <h2 id="canonical">Canonical SSO text</h2>
  <pre class="lite">{_esc(raw_text) or "(no raw text)"}</pre>

  {f'<h2 id="english">Controlled English</h2><pre class="lite">{_esc(en)}</pre>' if en else ""}

  <h2 id="structural">Structural counts</h2>
  <table class="refs">
    <tbody>{''.join(structural_rows)}</tbody>
  </table>

  <h2 id="refs-out">Outgoing references</h2>
  <table class="refs">
    <thead><tr><th>To</th><th>Kind</th><th>Context</th></tr></thead>
    <tbody>{render_edge_rows(refs.get("outgoing", []), "outgoing")}</tbody>
  </table>

  <h2 id="refs-in">Incoming references</h2>
  <table class="refs">
    <thead><tr><th>From</th><th>Kind</th><th>Context</th></tr></thead>
    <tbody>{render_edge_rows(refs.get("incoming", []), "incoming")}</tbody>
  </table>

  {f'<h2 id="diagram">Diagram</h2><div class="diagram">{mermaid_svg}</div>' if mermaid_svg else ""}
  {f'<h2 id="mindmap">Mindmap</h2><div class="diagram">{mindmap_svg}</div>' if mindmap_svg else ""}

  <h2 id="source">Encoded <code>.yh</code> source</h2>
  <pre class="src">{_esc(yh) or "(no encoded source)"}</pre>

  {nav_html}

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
    ap.add_argument("--no-cache", action="store_true",
                    help="ignore .cache.json and rebuild every page")
    ap.add_argument("--base-path", default="",
                    help="URL prefix when deploying under a subpath (e.g. '/yuho'). "
                         "Default empty = served at site root.")
    args = ap.parse_args()
    # Normalize base path: strip trailing slash, ensure leading slash if non-empty.
    BASE = args.base_path.rstrip("/")
    if BASE and not BASE.startswith("/"):
        BASE = "/" + BASE
    # Make BASE visible to the page renderers via module-level rebind.
    global _BASE_PATH
    _BASE_PATH = BASE

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

    # Yuho mascot for the About page hero. Copied from assets/logo/.
    mascot_src = REPO / "assets" / "logo" / "yuho_mascot.png"
    if mascot_src.exists():
        shutil.copy2(mascot_src, STATIC / "yuho_mascot.png")

    # Favicons. The .ico carries 16/32/48/64/128/256 sizes; the .png is a
    # 32x32 single-resolution fallback for modern browsers.
    ico_src = REPO / "assets" / "logo" / "yuho_mascot.ico"
    if ico_src.exists():
        shutil.copy2(ico_src, STATIC / "favicon.ico")
    fav_png_src = REPO / "assets" / "logo" / "yuho_mascot_favicon.png"
    if fav_png_src.exists():
        shutil.copy2(fav_png_src, STATIC / "favicon-32.png")

    # Index.json copy for client-side search
    shutil.copy2(CORPUS / "index.json", STATIC / "index.json")

    # Top-level pages
    (BUILD / "index.html").write_text(render_index(index))
    (BUILD / "coverage.html").write_text(render_coverage(index))

    # Reference graph: build once, render the page + ship a JSON dump.
    try:
        from yuho.library.reference_graph import build_reference_graph
        graph = build_reference_graph(REPO / "library" / "penal_code")
        graph_dict = graph.to_dict()
    except Exception as exc:
        # Don't fail the whole site build if the library isn't present;
        # emit a stub graph and a placeholder page.
        graph_dict = {"nodes": [], "edges": [], "stats": {}, "_error": str(exc)}
    (STATIC / "graph.json").write_text(json.dumps(graph_dict, separators=(",", ":")))
    (STATIC / "graph.js").write_text(_GRAPH_JS)
    (BUILD / "graph.html").write_text(render_graph(graph_dict))

    # Semantic graph: typed multi-kind graph at element / definition
    # / exception granularity, distinct from the section-granular reference
    # graph above. Heavy: ~10k nodes typically; rendered client-side.
    try:
        from yuho.library.semantic_graph import build_semantic_graph
        semg = build_semantic_graph(REPO / "library" / "penal_code")
        semg_dict = semg.to_dict()
    except Exception as exc:
        semg_dict = {"nodes": [], "edges": [], "stats": {}, "_error": str(exc)}
    (STATIC / "semantic-graph.json").write_text(
        json.dumps(semg_dict, separators=(",", ":"))
    )
    (STATIC / "semantic-graph.js").write_text(_SEMANTIC_GRAPH_JS)
    (BUILD / "semantic-graph.html").write_text(render_semantic_graph(semg_dict))

    (BUILD / "about.html").write_text(render_about())
    (BUILD / "404.html").write_text(render_404())
    (BUILD / "sitemap.xml").write_text(render_sitemap(index, args.base_url))
    (BUILD / "robots.txt").write_text(render_robots(args.base_url))

    # Per-section pages + full-text search index (G2). Adjacency uses the
    # ordering already in index.json (G4 prev/next). G9: hash-based cache
    # keyed on (section JSON, neighbour ids, build.py source) skips
    # rebuilding sections whose inputs haven't changed.
    sect_dir = CORPUS / "sections"
    n_pages = 0
    n_skipped = 0
    search_index: Dict[str, str] = {}
    ordered_nums = [r["number"] for r in index["sections"]]
    by_num = {r["number"]: r for r in index["sections"]}
    paths_by_num = {p.stem[1:]: p for p in sect_dir.glob("s*.json")}

    builder_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
    cache_path = BUILD / ".cache.json"
    cache_in: Dict[str, str] = {}
    if cache_path.exists() and not args.no_cache:
        try:
            cache_in = json.loads(cache_path.read_text())
            if cache_in.get("_builder") != builder_hash:
                cache_in = {}  # generator changed; rebuild everything.
        except Exception:
            cache_in = {}
    cache_out: Dict[str, str] = {"_builder": builder_hash}

    for i, num in enumerate(ordered_nums):
        path = paths_by_num.get(num)
        if path is None:
            continue
        raw = path.read_bytes()
        with path.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        prev_rec = by_num.get(ordered_nums[i - 1]) if i > 0 else None
        next_rec = by_num.get(ordered_nums[i + 1]) if i < len(ordered_nums) - 1 else None
        prev_id = prev_rec["number"] if prev_rec else ""
        next_id = next_rec["number"] if next_rec else ""
        key = hashlib.sha256(raw + f"|{prev_id}|{next_id}".encode()).hexdigest()
        n = rec["section_number"]
        # search_index always recomputed (cheap, derived from rec)
        parts = [
            rec.get("section_title", ""),
            rec.get("metadata", {}).get("summary") or "",
            rec.get("raw", {}).get("text", "") or "",
            rec.get("transpiled", {}).get("english", "") or "",
        ]
        joined = "\n".join(p for p in parts if p)
        if len(joined) > 4000:
            joined = joined[:4000]
        search_index[n] = joined
        cache_out[n] = key
        out_html = BUILD / "s" / f"{n}.html"
        if cache_in.get(n) == key and out_html.exists():
            n_skipped += 1
            continue
        out_html.write_text(render_section(rec, prev_rec=prev_rec, next_rec=next_rec))
        n_pages += 1
        # G6: per-section raw artefacts.
        (BUILD / "s" / f"{n}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2)
        )
        yh_src = rec.get("encoded", {}).get("yh_source") or ""
        if yh_src:
            (BUILD / "s" / f"{n}.yh").write_text(yh_src)
        en_src = rec.get("transpiled", {}).get("english") or ""
        if en_src:
            (BUILD / "s" / f"{n}.en.txt").write_text(en_src)

    cache_path.write_text(json.dumps(cache_out, separators=(",", ":")))

    # Tier 3 #8: per-section explorer pages, shipped under /explore/<n>.html.
    explore_src = REPO / "editors" / "browser-yuho" / "data" / "explore"
    explore_out_dir = BUILD / "explore"
    explore_out_dir.mkdir(parents=True, exist_ok=True)
    n_explore_pages = 0
    for num in ordered_nums:
        path = paths_by_num.get(num)
        if path is None:
            continue
        with path.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        explore_payload = None
        explore_json = explore_src / f"s{num}.json"
        if explore_json.exists():
            try:
                explore_payload = json.loads(explore_json.read_text(encoding="utf-8"))
            except Exception:
                explore_payload = None
        out = explore_out_dir / f"{num}.html"
        out.write_text(render_explore_page(rec, explore_payload or {}))
        n_explore_pages += 1

    (STATIC / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, separators=(",", ":"))
    )

    print(f"site built: {BUILD}")
    print(f"  {n_pages} per-section pages rebuilt, {n_skipped} skipped (cache hit)")
    print(f"  index.html, coverage.html, about.html")
    print(f"  static/{{style.css, search.js, index.json}}")
    print(f"\npreview: python3 -m http.server -d {BUILD.relative_to(REPO)} 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
