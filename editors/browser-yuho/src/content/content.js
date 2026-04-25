// Yuho content script.
//
// Activates on https://sso.agc.gov.sg/Act/PC1871* pages. Walks the SSO
// statute markup, identifies every section (e.g. "415", "377BD"), injects a
// small "[Yuho]" badge next to each section heading, and on demand opens a
// fixed side panel that shows the matching enriched record from the bundled
// corpus (English transpilation, element / penalty breakdown, illustrations,
// references in / out, SSO anchor, L1/L2/L3 status).
//
// Implementation notes:
// - Manifest V3 + content_scripts + web_accessible_resources are how we ship
//   data/sections.json into the page context.
// - We deliberately avoid mutating the canonical SSO DOM beyond inserting
//   our badge spans; the side panel is a fixed-position overlay.
// - All lookups go through a section-number key (string), e.g. "415", "377BD".

(function () {
  "use strict";

  // ---------------------------------------------------------------------
  // Constants and lazy-loaded data
  // ---------------------------------------------------------------------

  const PANEL_ID = "yuho-panel";
  const BADGE_CLASS = "yuho-badge";
  const HIGHLIGHT_CLASS = "yuho-section-highlight";

  let CORPUS = null; // section_number -> slim record

  /** Load the bundled corpus once, return it as an object. */
  async function loadCorpus() {
    if (CORPUS !== null) return CORPUS;
    const url = chrome.runtime.getURL("data/sections.json");
    try {
      const resp = await fetch(url);
      CORPUS = await resp.json();
    } catch (err) {
      console.error("[Yuho] failed to load corpus:", err);
      CORPUS = {};
    }
    return CORPUS;
  }

  // ---------------------------------------------------------------------
  // SSO DOM walk
  // ---------------------------------------------------------------------

  // SSO marks each provision header with an anchor id like "pr415-" or
  // "pr377BD-". We use that as the canonical signal for a section heading
  // and derive the section number from it.
  const SSO_ANCHOR_RE = /\bpr(\d+[A-Z]{0,3})-?\b/;

  /** Yield {anchorId, sectionNumber, headerEl} for every section header. */
  function* findSectionHeaders() {
    // SSO uses different markup for different provision tiers; we look for
    // any element whose id matches the prN- shape and whose tag is heading-
    // or paragraph-shaped.
    const candidates = document.querySelectorAll(
      "[id^='pr']"
    );
    const seen = new Set();
    for (const el of candidates) {
      const m = SSO_ANCHOR_RE.exec(el.id);
      if (!m) continue;
      const num = m[1];
      if (seen.has(num)) continue;
      seen.add(num);
      yield { anchorId: el.id, sectionNumber: num, headerEl: el };
    }
  }

  // ---------------------------------------------------------------------
  // Badge injection
  // ---------------------------------------------------------------------

  function makeBadge(sectionNumber, record) {
    const badge = document.createElement("button");
    badge.type = "button";
    badge.className = BADGE_CLASS;
    badge.dataset.section = sectionNumber;
    badge.title = record
      ? `Yuho: open enriched view for s${sectionNumber} (${labelFor(record)})`
      : `Yuho: not encoded yet`;
    badge.textContent = badgeText(record);
    badge.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      openPanel(sectionNumber);
    });
    return badge;
  }

  function badgeText(record) {
    if (!record) return "Yuho ·";
    const cov = record.coverage || {};
    const tier =
      cov.L3 === "stamped" ? "L3" :
      cov.L3 === "flagged" ? "FLAG" :
      cov.L2 ? "L2" :
      cov.L1 ? "L1" : "?";
    return `Yuho · ${tier}`;
  }

  function labelFor(record) {
    const cov = record.coverage || {};
    if (cov.L3 === "stamped") return "L3 stamped";
    if (cov.L3 === "flagged") return "flagged for review";
    if (cov.L2) return "L1+L2 passing";
    return "no coverage";
  }

  function injectBadges(corpus) {
    let inserted = 0;
    for (const { sectionNumber, headerEl } of findSectionHeaders()) {
      // Avoid double-insertion on re-runs.
      if (headerEl.querySelector(`.${BADGE_CLASS}`)) continue;
      const record = corpus[sectionNumber] || null;
      const badge = makeBadge(sectionNumber, record);
      headerEl.appendChild(badge);
      inserted++;
    }
    return inserted;
  }

  // ---------------------------------------------------------------------
  // Side panel
  // ---------------------------------------------------------------------

  function ensurePanel() {
    let panel = document.getElementById(PANEL_ID);
    if (panel) return panel;

    panel = document.createElement("aside");
    panel.id = PANEL_ID;
    panel.setAttribute("role", "complementary");
    panel.setAttribute("aria-label", "Yuho enrichment panel");
    panel.innerHTML = `
      <div class="yuho-panel-header">
        <span class="yuho-panel-title">Yuho</span>
        <span class="yuho-panel-subtitle"></span>
        <div class="yuho-panel-actions">
          <button type="button" class="yuho-pin" title="Pin / unpin panel">📌</button>
          <button type="button" class="yuho-close" title="Close panel">✕</button>
        </div>
      </div>
      <nav class="yuho-tabs" role="tablist">
        <button class="yuho-tab active" data-tab="overview" role="tab">Overview</button>
        <button class="yuho-tab" data-tab="english" role="tab">English</button>
        <button class="yuho-tab" data-tab="elements" role="tab">Elements</button>
        <button class="yuho-tab" data-tab="refs" role="tab">References</button>
        <button class="yuho-tab" data-tab="source" role="tab">.yh source</button>
      </nav>
      <main class="yuho-panel-body" tabindex="0"></main>
      <footer class="yuho-panel-footer">
        <span class="yuho-version-tag"></span>
        <a class="yuho-link" target="_blank" rel="noopener">Open on SSO ↗</a>
      </footer>
    `;
    document.body.appendChild(panel);

    panel.querySelector(".yuho-close").addEventListener("click", closePanel);
    panel.querySelector(".yuho-pin").addEventListener("click", togglePin);
    for (const tab of panel.querySelectorAll(".yuho-tab")) {
      tab.addEventListener("click", () => switchTab(tab.dataset.tab));
    }
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && panel.classList.contains("open")) {
        closePanel();
      }
    });
    return panel;
  }

  let CURRENT_SECTION = null;

  async function openPanel(sectionNumber) {
    const corpus = await loadCorpus();
    const record = corpus[sectionNumber];
    const panel = ensurePanel();
    panel.classList.add("open");
    CURRENT_SECTION = sectionNumber;

    panel.querySelector(".yuho-panel-subtitle").textContent =
      record ? `s${sectionNumber} — ${record.section_title || ""}` : `s${sectionNumber} — not encoded`;
    panel.querySelector(".yuho-version-tag").textContent =
      record ? `yuho ${record.provenance?.yuho_version || "?"} · ${record.coverage?.L3 || "no L3"}` : "";
    const linkEl = panel.querySelector(".yuho-link");
    linkEl.href = record?.sso_url || `https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr${sectionNumber}-#pr${sectionNumber}-`;

    if (!record) {
      panel.querySelector(".yuho-panel-body").innerHTML = `
        <div class="yuho-empty">
          <p>Section <code>s${sectionNumber}</code> is not present in the encoded library.</p>
          <p>This means Yuho hasn't produced a structured encoding yet, or this is a sub-item / chapter heading rather than a section.</p>
        </div>`;
      return;
    }

    // Default to overview tab.
    switchTab("overview");
    highlightActiveSection(sectionNumber);
  }

  function closePanel() {
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.classList.remove("open", "pinned");
    clearHighlight();
    CURRENT_SECTION = null;
  }

  function togglePin() {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return;
    panel.classList.toggle("pinned");
  }

  function switchTab(name) {
    const panel = document.getElementById(PANEL_ID);
    if (!panel || !CURRENT_SECTION) return;
    for (const tab of panel.querySelectorAll(".yuho-tab")) {
      tab.classList.toggle("active", tab.dataset.tab === name);
    }
    const corpus = CORPUS || {};
    const record = corpus[CURRENT_SECTION];
    const body = panel.querySelector(".yuho-panel-body");
    body.innerHTML = renderTab(name, record);
    body.scrollTop = 0;
  }

  // ---------------------------------------------------------------------
  // Tab rendering
  // ---------------------------------------------------------------------

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) =>
      ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])
    );
  }

  function renderTab(name, record) {
    switch (name) {
      case "overview":  return renderOverview(record);
      case "english":   return renderEnglish(record);
      case "elements":  return renderElements(record);
      case "refs":      return renderRefs(record);
      case "source":    return renderSource(record);
      default:          return `<p>unknown tab: ${escapeHtml(name)}</p>`;
    }
  }

  function renderOverview(rec) {
    const ast = rec.encoded?.ast_summary || {};
    const cov = rec.coverage || {};
    const summary = rec.metadata?.summary || rec.raw?.text || "(no summary)";
    const flag = cov.L3_flag;
    const flagBlock = flag
      ? `<div class="yuho-flag">
           <strong>Flagged for L3 review.</strong>
           <p>${escapeHtml(flag.reason || flag.raw || "")}</p>
           ${flag.suggested_fix ? `<p><em>Suggested fix:</em> ${escapeHtml(flag.suggested_fix)}</p>` : ""}
         </div>` : "";
    return `
      ${flagBlock}
      <h3>Summary</h3>
      <p class="yuho-summary">${escapeHtml(summary)}</p>
      <h3>Structure</h3>
      <table class="yuho-stats">
        <tr><th>Elements</th><td>${ast.elements ?? 0}</td></tr>
        <tr><th>Illustrations</th><td>${ast.illustrations ?? 0}</td></tr>
        <tr><th>Subsections</th><td>${ast.subsections ?? 0}</td></tr>
        <tr><th>Exceptions</th><td>${ast.exceptions ?? 0}</td></tr>
        <tr><th>Case law</th><td>${ast.case_law ?? 0}</td></tr>
        <tr><th>Effective</th><td>${(ast.effective_dates || []).join(", ") || "—"}</td></tr>
        <tr><th>Penalty</th><td>${ast.has_penalty ? "yes" : "no"}</td></tr>
        ${ast.subsumes ? `<tr><th>Subsumes</th><td>s${escapeHtml(ast.subsumes)}</td></tr>` : ""}
        ${ast.amends ? `<tr><th>Amends</th><td>s${escapeHtml(ast.amends)}</td></tr>` : ""}
      </table>
      <h3>Coverage</h3>
      <table class="yuho-stats">
        <tr><th>L1 (parse)</th><td>${cov.L1 ? "✓" : "✗"}</td></tr>
        <tr><th>L2 (lint)</th><td>${cov.L2 ? "✓" : "✗"}</td></tr>
        <tr><th>L3 (human)</th><td>${escapeHtml(cov.L3 || "—")}</td></tr>
        ${cov.L3_stamp_date ? `<tr><th>L3 stamped</th><td>${escapeHtml(cov.L3_stamp_date)}</td></tr>` : ""}
      </table>
    `;
  }

  function renderEnglish(rec) {
    const en = rec.transpiled?.english;
    if (!en) return `<p class="yuho-empty">No controlled-English transpilation available.</p>`;
    return `<pre class="yuho-pre">${escapeHtml(en)}</pre>`;
  }

  function renderElements(rec) {
    const ast = rec.encoded?.ast_summary || {};
    const yh = rec.encoded?.yh_source || "";
    if (!yh) return `<p class="yuho-empty">No encoded source.</p>`;
    // Naive but honest: extract the elements block from the .yh source.
    const elementsBlock = extractBlock(yh, "elements");
    const exceptionsBlock = extractBlock(yh, "exceptions");
    const penaltyBlock = extractBlock(yh, "penalty");
    let html = "";
    if (penaltyBlock) html += `<h3>Penalty</h3><pre class="yuho-pre">${escapeHtml(penaltyBlock)}</pre>`;
    if (elementsBlock) html += `<h3>Elements</h3><pre class="yuho-pre">${escapeHtml(elementsBlock)}</pre>`;
    if (exceptionsBlock) html += `<h3>Exceptions</h3><pre class="yuho-pre">${escapeHtml(exceptionsBlock)}</pre>`;
    if (!html) html = `<p class="yuho-empty">No elements / penalty / exceptions blocks found in the encoding.</p>`;
    return html;
  }

  /** Pull the body of a `name { ... }` block out of a .yh source string. */
  function extractBlock(source, name) {
    const idx = source.indexOf(`\n${name} `);
    const start = idx >= 0 ? idx : (source.startsWith(name + " ") ? 0 : source.indexOf(`\n${name} {`));
    if (start < 0) return null;
    const open = source.indexOf("{", start);
    if (open < 0) return null;
    let depth = 1;
    for (let i = open + 1; i < source.length; i++) {
      const c = source[i];
      if (c === "{") depth++;
      else if (c === "}") {
        depth--;
        if (depth === 0) return source.slice(start, i + 1).trim();
      }
    }
    return null;
  }

  function renderRefs(rec) {
    const refs = rec.references || {};
    const out = refs.outgoing || [];
    const inc = refs.incoming || [];
    const renderEdge = (e, side) => {
      const other = side === "out" ? e.dst : e.src;
      const cls = `yuho-edge yuho-edge-${e.kind}`;
      const snippet = e.snippet ? `<small class="yuho-snippet">${escapeHtml(e.snippet)}</small>` : "";
      return `<li class="${cls}">
                <a href="https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr${other}-#pr${other}-"
                   target="_blank" rel="noopener">s${escapeHtml(other)}</a>
                <span class="yuho-edge-kind">${e.kind}</span>
                ${snippet}
              </li>`;
    };
    return `
      <h3>Outgoing (${out.length})</h3>
      ${out.length ? `<ul class="yuho-edges">${out.map(e => renderEdge(e, "out")).join("")}</ul>` : `<p class="yuho-empty">No outgoing references.</p>`}
      <h3>Incoming (${inc.length})</h3>
      ${inc.length ? `<ul class="yuho-edges">${inc.map(e => renderEdge(e, "in")).join("")}</ul>` : `<p class="yuho-empty">No incoming references.</p>`}
    `;
  }

  function renderSource(rec) {
    const yh = rec.encoded?.yh_source || "";
    if (!yh) return `<p class="yuho-empty">No encoded source.</p>`;
    return `<pre class="yuho-pre yuho-source">${escapeHtml(yh)}</pre>`;
  }

  // ---------------------------------------------------------------------
  // Section highlighting
  // ---------------------------------------------------------------------

  let HIGHLIGHTED = null;

  function highlightActiveSection(sectionNumber) {
    clearHighlight();
    const el = document.getElementById(`pr${sectionNumber}-`)
            || document.getElementById(`pr${sectionNumber}`);
    if (el) {
      el.classList.add(HIGHLIGHT_CLASS);
      HIGHLIGHTED = el;
    }
  }

  function clearHighlight() {
    if (HIGHLIGHTED) {
      HIGHLIGHTED.classList.remove(HIGHLIGHT_CLASS);
      HIGHLIGHTED = null;
    }
  }

  // ---------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------

  async function init() {
    const corpus = await loadCorpus();
    const n = injectBadges(corpus);
    if (n === 0) {
      console.warn("[Yuho] no section headers detected on this page");
      return;
    }
    console.info(`[Yuho] injected ${n} section badges`);

    // SSO sometimes streams in additional content via XHR for whole-doc views;
    // observe DOM mutations and re-inject as needed.
    const obs = new MutationObserver(() => {
      injectBadges(corpus);
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
