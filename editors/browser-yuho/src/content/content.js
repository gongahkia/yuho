// Yuho content script.
//
// Activates on https://sso.agc.gov.sg/Act/PC1871* pages. Walks the SSO
// statute markup, identifies every section (e.g. "415", "377BD"), injects a
// small "[Yuho]" badge next to each section heading, and on demand opens a
// fixed side panel that shows the matching enriched record from the bundled
// corpus.
//
// Features (v0.3):
// - Section-heading badges with L1/L2/L3/FLAG status
// - Side panel with 6 tabs (Overview / English / Elements / References / Diagram / .yh)
// - **Inline citation tooltips** on `s415` mentions in body text
// - **Panel search box** filtering all 524 sections by number or title
// - **User-prefs persistence** (chrome.storage.sync): pin state, default tab
// - **Throttled MutationObserver** for whole-doc SSO views
// - **Per-tab badge** showing the focused section's coverage tier

(function () {
  "use strict";

  // ---------------------------------------------------------------------
  // Constants and lazy-loaded data
  // ---------------------------------------------------------------------

  const PANEL_ID = "yuho-panel";
  const TOOLTIP_ID = "yuho-tooltip";
  const BADGE_CLASS = "yuho-badge";
  const HIGHLIGHT_CLASS = "yuho-section-highlight";
  const TOOLTIP_DELAY_MS = 350;
  const TOOLTIP_HIDE_DELAY_MS = 200;
  const OBSERVER_DEBOUNCE_MS = 200;

  let CORPUS = null; // section_number -> slim record
  let PREFS = {
    pinned: false,
    default_tab: "overview",
  };

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
  // User preferences (chrome.storage.sync)
  // ---------------------------------------------------------------------

  async function loadPrefs() {
    return new Promise((resolve) => {
      try {
        chrome.storage.sync.get(["yuho_prefs"], (result) => {
          if (result && result.yuho_prefs) {
            PREFS = { ...PREFS, ...result.yuho_prefs };
          }
          resolve(PREFS);
        });
      } catch (err) {
        // chrome.storage may be unavailable in some contexts; fall back.
        resolve(PREFS);
      }
    });
  }

  function savePrefs() {
    try {
      chrome.storage.sync.set({ yuho_prefs: PREFS });
    } catch (err) {
      // Best-effort; permissions or context may not allow it.
    }
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
    const candidates = document.querySelectorAll("[id^='pr']");
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
  // Inline citation tooltips
  //
  // Walks text nodes outside the panel/badge UI looking for tokens like
  // "s415", "section 415", "Section 377BO". Wraps the matched span in a
  // `<span class="yuho-citation">` so it's hover-detectable. On hover we
  // pop a small card with marginal note + penalty range + L3 tier and a
  // button to open the full panel.
  //
  // We deliberately walk text nodes only — never modify element nodes —
  // so we don't break SSO's own scripts or layout.
  // ---------------------------------------------------------------------

  const CITATION_RE = /(\b[Ss]ection\s+|\b[Ss]\.?\s*)(\d+[A-Z]{0,3})\b/g;
  const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "INPUT", "BUTTON",
                             "A", "CODE", "PRE"]);

  function shouldSkipNode(node) {
    let cur = node.parentElement;
    while (cur) {
      if (cur.id === PANEL_ID || cur.id === TOOLTIP_ID) return true;
      if (cur.classList && (cur.classList.contains(BADGE_CLASS) ||
                            cur.classList.contains("yuho-citation"))) return true;
      if (SKIP_TAGS.has(cur.tagName)) return true;
      cur = cur.parentElement;
    }
    return false;
  }

  function injectCitationsIn(root) {
    if (!root) return 0;
    const walker = document.createTreeWalker(
      root, NodeFilter.SHOW_TEXT,
      { acceptNode: (n) => {
          if (!n.nodeValue || n.nodeValue.length < 3) return NodeFilter.FILTER_REJECT;
          if (shouldSkipNode(n)) return NodeFilter.FILTER_REJECT;
          if (!CITATION_RE.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
          CITATION_RE.lastIndex = 0; // test() advances; reset before walking
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );
    const targets = [];
    let n;
    while ((n = walker.nextNode())) targets.push(n);

    let count = 0;
    for (const textNode of targets) {
      const text = textNode.nodeValue;
      const matches = [...text.matchAll(CITATION_RE)];
      if (matches.length === 0) continue;
      const frag = document.createDocumentFragment();
      let lastIndex = 0;
      for (const m of matches) {
        const before = text.slice(lastIndex, m.index);
        if (before) frag.appendChild(document.createTextNode(before));
        const span = document.createElement("span");
        span.className = "yuho-citation";
        span.dataset.section = m[2];
        span.textContent = m[0];
        frag.appendChild(span);
        lastIndex = m.index + m[0].length;
        count++;
      }
      const tail = text.slice(lastIndex);
      if (tail) frag.appendChild(document.createTextNode(tail));
      textNode.parentNode.replaceChild(frag, textNode);
    }
    return count;
  }

  // ---------------------------------------------------------------------
  // Tooltip popup
  // ---------------------------------------------------------------------

  let TOOLTIP_SHOW_TIMER = null;
  let TOOLTIP_HIDE_TIMER = null;

  function ensureTooltip() {
    let tip = document.getElementById(TOOLTIP_ID);
    if (tip) return tip;
    tip = document.createElement("div");
    tip.id = TOOLTIP_ID;
    tip.setAttribute("role", "tooltip");
    document.body.appendChild(tip);
    // Keep tooltip alive while hovering it (e.g. clicking the button).
    tip.addEventListener("mouseenter", () => {
      if (TOOLTIP_HIDE_TIMER) {
        clearTimeout(TOOLTIP_HIDE_TIMER);
        TOOLTIP_HIDE_TIMER = null;
      }
    });
    tip.addEventListener("mouseleave", scheduleHideTooltip);
    return tip;
  }

  function showTooltipFor(citationEl) {
    if (TOOLTIP_HIDE_TIMER) {
      clearTimeout(TOOLTIP_HIDE_TIMER);
      TOOLTIP_HIDE_TIMER = null;
    }
    if (TOOLTIP_SHOW_TIMER) clearTimeout(TOOLTIP_SHOW_TIMER);
    TOOLTIP_SHOW_TIMER = setTimeout(async () => {
      const corpus = await loadCorpus();
      const section = citationEl.dataset.section;
      const record = corpus[section];
      const tip = ensureTooltip();
      tip.innerHTML = renderTooltip(section, record);
      // Position: prefer below, but clamp into viewport.
      const rect = citationEl.getBoundingClientRect();
      const tipRect = tip.getBoundingClientRect();
      let top = window.scrollY + rect.bottom + 6;
      let left = window.scrollX + rect.left;
      const margin = 8;
      const maxLeft = window.scrollX + window.innerWidth - tipRect.width - margin;
      if (left > maxLeft) left = Math.max(margin, maxLeft);
      tip.style.top = `${top}px`;
      tip.style.left = `${left}px`;
      tip.classList.add("visible");
      // Wire the "open panel" button if the record exists.
      const openBtn = tip.querySelector(".yuho-tooltip-open");
      if (openBtn) {
        openBtn.addEventListener("click", (ev) => {
          ev.preventDefault();
          openPanel(section);
          hideTooltip();
        });
      }
    }, TOOLTIP_DELAY_MS);
  }

  function scheduleHideTooltip() {
    if (TOOLTIP_SHOW_TIMER) {
      clearTimeout(TOOLTIP_SHOW_TIMER);
      TOOLTIP_SHOW_TIMER = null;
    }
    if (TOOLTIP_HIDE_TIMER) clearTimeout(TOOLTIP_HIDE_TIMER);
    TOOLTIP_HIDE_TIMER = setTimeout(hideTooltip, TOOLTIP_HIDE_DELAY_MS);
  }

  function hideTooltip() {
    const tip = document.getElementById(TOOLTIP_ID);
    if (tip) tip.classList.remove("visible");
  }

  function renderTooltip(section, record) {
    if (!record) {
      return `
        <div class="yuho-tooltip-card">
          <div class="yuho-tooltip-header">
            <span class="yuho-tooltip-section">s${section}</span>
            <span class="yuho-tooltip-tier yuho-tooltip-tier-none">no encoding</span>
          </div>
          <p class="yuho-tooltip-summary">Section ${section} is not present in the encoded library.</p>
        </div>`;
    }
    const cov = record.coverage || {};
    const ast = record.encoded?.ast_summary || {};
    const summary = record.metadata?.summary || record.raw?.marginal_note || record.raw?.text || "";
    const summary_short = summary.length > 180 ? summary.slice(0, 177) + "…" : summary;
    const tier =
      cov.L3 === "stamped" ? "L3" :
      cov.L3 === "flagged" ? "FLAG" :
      cov.L2 ? "L2" :
      cov.L1 ? "L1" : "?";
    const tierClass = `yuho-tooltip-tier-${tier.toLowerCase()}`;

    const penalty = record.transpiled?.english
      ? extractPenaltyShort(record.transpiled.english)
      : "";

    return `
      <div class="yuho-tooltip-card">
        <div class="yuho-tooltip-header">
          <span class="yuho-tooltip-section">s${section}</span>
          <span class="yuho-tooltip-title">${escapeHtml(record.section_title || "")}</span>
          <span class="yuho-tooltip-tier ${tierClass}">${tier}</span>
        </div>
        ${summary_short ? `<p class="yuho-tooltip-summary">${escapeHtml(summary_short)}</p>` : ""}
        <div class="yuho-tooltip-stats">
          ${ast.elements ? `<span>${ast.elements} elem</span>` : ""}
          ${ast.illustrations ? `<span>${ast.illustrations} illus</span>` : ""}
          ${ast.subsections ? `<span>${ast.subsections} subs</span>` : ""}
          ${penalty ? `<span class="yuho-tooltip-penalty">${escapeHtml(penalty)}</span>` : ""}
        </div>
        <div class="yuho-tooltip-actions">
          <button type="button" class="yuho-tooltip-open">Open in panel</button>
          <a href="${record.sso_url || `https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr${section}-#pr${section}-`}"
             target="_blank" rel="noopener">SSO ↗</a>
        </div>
      </div>`;
  }

  function extractPenaltyShort(english) {
    // Very rough: pull the first "imprisonment" or "fine" line as a teaser.
    const lines = english.split("\n").map(s => s.trim());
    for (const line of lines) {
      if (/^(imprisonment|fine|caning|death)\b/i.test(line)) {
        return line.length > 60 ? line.slice(0, 57) + "…" : line;
      }
    }
    return "";
  }

  function attachCitationListeners() {
    // Use event delegation on document body — newly injected citations
    // automatically inherit hover behaviour without per-element listeners.
    document.body.addEventListener("mouseover", (ev) => {
      const el = ev.target.closest(".yuho-citation");
      if (el) showTooltipFor(el);
    });
    document.body.addEventListener("mouseout", (ev) => {
      const el = ev.target.closest(".yuho-citation");
      if (el) scheduleHideTooltip();
    });
    // Hide tooltip on scroll (position would otherwise drift).
    window.addEventListener("scroll", hideTooltip, { passive: true });
    // Click on a citation: open the panel directly (skip the dwell delay).
    document.body.addEventListener("click", (ev) => {
      const el = ev.target.closest(".yuho-citation");
      if (!el) return;
      // Don't intercept if the user is also clicking a real link.
      if (ev.target.tagName === "A") return;
      ev.preventDefault();
      openPanel(el.dataset.section);
    });
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
      <div class="yuho-panel-search">
        <input type="search" class="yuho-search-input"
               placeholder="Search section number or title (e.g. 415, theft)"
               aria-label="Search Yuho corpus" />
        <ul class="yuho-search-results" role="listbox" hidden></ul>
      </div>
      <nav class="yuho-tabs" role="tablist">
        <button class="yuho-tab active" data-tab="overview" role="tab">Overview</button>
        <button class="yuho-tab" data-tab="english" role="tab">English</button>
        <button class="yuho-tab" data-tab="elements" role="tab">Elements</button>
        <button class="yuho-tab" data-tab="refs" role="tab">References</button>
        <button class="yuho-tab" data-tab="diagram" role="tab">Diagram</button>
        <button class="yuho-tab" data-tab="explore" role="tab">Explore</button>
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
      tab.addEventListener("click", () => switchTab(tab.dataset.tab, /*persist=*/ true));
    }
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && panel.classList.contains("open")) {
        const search = panel.querySelector(".yuho-search-input");
        if (search && document.activeElement === search) {
          // Esc inside search: just clear the box, don't close the panel.
          search.value = "";
          renderSearchResults("");
          return;
        }
        closePanel();
      }
    });

    // Search wiring.
    const searchInput = panel.querySelector(".yuho-search-input");
    searchInput.addEventListener("input", (ev) => renderSearchResults(ev.target.value));
    searchInput.addEventListener("focus", () => {
      const results = panel.querySelector(".yuho-search-results");
      if (searchInput.value) results.hidden = false;
    });
    panel.querySelector(".yuho-search-results").addEventListener("click", (ev) => {
      const item = ev.target.closest("li[data-section]");
      if (item) {
        openPanel(item.dataset.section);
        searchInput.value = "";
        renderSearchResults("");
      }
    });

    // Restore pinned state from prefs.
    if (PREFS.pinned) panel.classList.add("pinned");
    return panel;
  }

  function renderSearchResults(query) {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return;
    const results = panel.querySelector(".yuho-search-results");
    const q = (query || "").trim().toLowerCase();
    if (!q || !CORPUS) {
      results.innerHTML = "";
      results.hidden = true;
      return;
    }
    const hits = [];
    for (const num of Object.keys(CORPUS)) {
      const rec = CORPUS[num];
      const title = (rec.section_title || "").toLowerCase();
      if (num.toLowerCase().includes(q) || title.includes(q)) {
        hits.push(rec);
        if (hits.length >= 30) break;
      }
    }
    if (hits.length === 0) {
      results.innerHTML = `<li class="yuho-search-empty">No matches.</li>`;
      results.hidden = false;
      return;
    }
    results.innerHTML = hits.map(rec => {
      const cov = rec.coverage || {};
      const tier =
        cov.L3 === "stamped" ? "L3" :
        cov.L3 === "flagged" ? "FLAG" :
        cov.L2 ? "L2" :
        cov.L1 ? "L1" : "?";
      return `
        <li data-section="${rec.section_number}" role="option" tabindex="0">
          <span class="yuho-search-num">s${rec.section_number}</span>
          <span class="yuho-search-title">${escapeHtml(rec.section_title || "")}</span>
          <span class="yuho-search-tier yuho-search-tier-${tier.toLowerCase()}">${tier}</span>
        </li>`;
    }).join("");
    results.hidden = false;
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

    // Open the user's preferred default tab (or override via prefs).
    switchTab(PREFS.default_tab || "overview", /*persist=*/ false);
    highlightActiveSection(sectionNumber);
    notifyServiceWorker(sectionNumber, record);
  }

  function closePanel() {
    const panel = document.getElementById(PANEL_ID);
    if (panel) {
      const wasPinned = panel.classList.contains("pinned");
      panel.classList.remove("open");
      // Pinned state is preserved across closes by default; clear only on
      // explicit Esc / X. (Pin button toggles this independently.)
      panel.classList.remove("pinned");
      if (wasPinned !== false) {
        PREFS.pinned = false;
        savePrefs();
      }
    }
    clearHighlight();
    hideTooltip();
    CURRENT_SECTION = null;
    notifyServiceWorker(null, null);
  }

  function togglePin() {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return;
    panel.classList.toggle("pinned");
    PREFS.pinned = panel.classList.contains("pinned");
    savePrefs();
  }

  function switchTab(name, persist) {
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
    if (persist) {
      PREFS.default_tab = name;
      savePrefs();
    }
  }

  // ---------------------------------------------------------------------
  // Service-worker messaging (per-tab badge)
  //
  // Each time the panel opens / closes / changes section we send a
  // "section_active" message to the service worker; the SW updates the
  // toolbar action badge with the section's L3 tier so the user can see
  // status without opening the panel.
  // ---------------------------------------------------------------------

  function notifyServiceWorker(sectionNumber, record) {
    try {
      let badge = "";
      if (record) {
        const cov = record.coverage || {};
        badge =
          cov.L3 === "stamped" ? "L3" :
          cov.L3 === "flagged" ? "FLAG" :
          cov.L2 ? "L2" : "L1";
      }
      chrome.runtime.sendMessage({
        type: "yuho_section_active",
        section: sectionNumber,
        badge,
      });
    } catch (err) {
      // SW may not be reachable; ignore.
    }
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
      case "diagram":   return renderDiagram(record);
      case "explore":   return renderExplore(record);
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
    const yh = rec.encoded?.yh_source || "";
    if (!yh) return `<p class="yuho-empty">No encoded source.</p>`;
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

  // SVGs are lazy-loaded from data/svg/s{num}.svg on tab open and cached
  // in-memory thereafter so re-opening the same section is instant.
  const SVG_CACHE = new Map();
  const SVG_HOST_ID = "yuho-diagram-host";

  function renderDiagram(rec) {
    const url = rec.transpiled?.mermaid_svg_url;
    if (!url) {
      return `<p class="yuho-empty">No diagram available for this section. ` +
             `Re-run <code>scripts/build_corpus.py</code> with mmdc on PATH, ` +
             `then <code>build_data.py</code>, to populate <code>data/svg/</code>.</p>`;
    }
    // Render a host element synchronously, then populate it asynchronously.
    queueMicrotask(() => loadDiagram(rec.section_number, url));
    return `<div class="yuho-diagram" id="${SVG_HOST_ID}">
              <p class="yuho-empty">Loading diagram…</p>
            </div>`;
  }

  async function loadDiagram(section, url) {
    const host = document.getElementById(SVG_HOST_ID);
    if (!host) return;
    let svg = SVG_CACHE.get(section);
    if (!svg) {
      try {
        const res = await fetch(chrome.runtime.getURL(url));
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        svg = await res.text();
        SVG_CACHE.set(section, svg);
      } catch (err) {
        host.innerHTML = `<p class="yuho-empty">Failed to load diagram: ${escapeHtml(String(err))}</p>`;
        return;
      }
    }
    // Re-fetch host in case the user already switched away.
    const stillHost = document.getElementById(SVG_HOST_ID);
    if (stillHost) stillHost.innerHTML = svg;
  }

  // Counter-example explorer (Tier 3 #7): lazy-fetches the pre-rendered
  // explorer report for the current section. Pre-rendering happens at
  // corpus-build time via build_explore.py — the browser ext does not
  // run Z3 itself.
  const EXPLORE_CACHE = new Map();
  const EXPLORE_HOST_ID = "yuho-explore-host";

  function renderExplore(rec) {
    queueMicrotask(() => loadExplore(rec.section_number));
    return `<div id="${EXPLORE_HOST_ID}">
              <p class="yuho-empty">Loading counter-examples…</p>
            </div>`;
  }

  async function loadExplore(section) {
    const host = document.getElementById(EXPLORE_HOST_ID);
    if (!host) return;
    let payload = EXPLORE_CACHE.get(section);
    if (!payload) {
      try {
        const url = chrome.runtime.getURL(`data/explore/s${section}.json`);
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        payload = await res.json();
        EXPLORE_CACHE.set(section, payload);
      } catch (err) {
        host.innerHTML = `<p class="yuho-empty">No pre-rendered explorer report for s${escapeHtml(section)}.<br>` +
          `Run <code>editors/browser-yuho/build_explore.py</code> after the corpus build.</p>`;
        return;
      }
    }
    host.innerHTML = renderExploreReport(payload);
  }

  function renderExploreReport(p) {
    if (!p.available) {
      return `<p class="yuho-empty">${escapeHtml(p.reason || "Explorer unavailable for this section.")}</p>`;
    }
    const s = p.summary || {};
    const head = `
      <table class="yuho-stats">
        <tr><th>Elements</th><td>${s.n_leaf_elements ?? 0}</td></tr>
        <tr><th>Exceptions</th><td>${s.n_exceptions ?? 0}</td></tr>
        <tr><th>Conviction reachable</th><td>${s.conviction_reachable ? "yes" : "no"}</td></tr>
        <tr><th>Load-bearing elements</th><td>${s.n_load_bearing ?? 0}</td></tr>
        <tr><th>Dead exceptions</th><td>${s.n_dead_exceptions ?? 0}</td></tr>
      </table>
    `;
    const sat = (p.satisfying || []).map((sc, i) => {
      const tags = Object.entries(sc.elements || {})
        .map(([k, v]) => `<span class="yuho-elem-${v ? "t" : "f"}">${escapeHtml(k)}</span>`)
        .join(" ");
      return `<li><strong>#${i + 1}</strong> ${tags}</li>`;
    }).join("") || `<li class="yuho-empty">No satisfying scenarios found (conviction may be unreachable).</li>`;
    const dead = (p.dead_exceptions || []).map(d => `<li>${escapeHtml(d)}</li>`).join("");
    const exc = (p.exception_coverage || []).map(e => {
      const mark = e.reachable === true ? "REACHABLE" : (e.reachable === false ? "DEAD" : "UNKNOWN");
      return `<li>${escapeHtml(e.exception)} — ${mark}</li>`;
    }).join("");
    return `
      <h3>Summary</h3>
      ${head}
      <h3>Satisfying scenarios</h3>
      <ul class="yuho-explore-list">${sat}</ul>
      ${exc ? `<h3>Exception coverage</h3><ul class="yuho-explore-list">${exc}</ul>` : ""}
      ${dead ? `<h3>Dead exceptions</h3><ul class="yuho-explore-list">${dead}</ul>` : ""}
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

  /** Throttle: returns a function that fires at most once per `wait` ms. */
  function debounce(fn, wait) {
    let t = null;
    let pending = false;
    return function (...args) {
      if (t) {
        pending = true;
        return;
      }
      fn.apply(this, args);
      t = setTimeout(() => {
        t = null;
        if (pending) {
          pending = false;
          fn.apply(this, args);
        }
      }, wait);
    };
  }

  async function init() {
    await loadPrefs();
    const corpus = await loadCorpus();
    const n = injectBadges(corpus);
    if (n === 0) {
      console.warn("[Yuho] no section headers detected on this page");
      return;
    }
    console.info(`[Yuho] injected ${n} section badges`);

    // Inline citations: walk the body once on init.
    const cit = injectCitationsIn(document.body);
    if (cit > 0) {
      console.info(`[Yuho] wrapped ${cit} inline citations`);
    }
    attachCitationListeners();

    // Auto-pin on init if user previously pinned.
    if (PREFS.pinned) ensurePanel().classList.add("pinned");

    // Debounced re-injection: SSO sometimes streams in additional content.
    const reinject = debounce(() => {
      injectBadges(corpus);
      injectCitationsIn(document.body);
    }, OBSERVER_DEBOUNCE_MS);
    const obs = new MutationObserver(reinject);
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
