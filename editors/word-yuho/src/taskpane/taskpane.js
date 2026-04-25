// Yuho Word taskpane.
//
// Loads sections.json (the same slim corpus the browser extension ships)
// and renders a search/select UI. Selected section can be inserted into the
// active Word document in three forms: full English transpilation, plain
// citation ("Penal Code 1871, s.415 (Cheating)"), or a bulleted element
// list. The active document mutation goes through Office.js Word APIs.

/* global Office, Word */

let CORPUS = null;
let SELECTED = null;

Office.onReady(() => {
  document.getElementById("search").addEventListener("input", onSearch);
  document.getElementById("action-insert-en").addEventListener("click", () => insert("english"));
  document.getElementById("action-insert-cite").addEventListener("click", () => insert("citation"));
  document.getElementById("action-insert-elements").addEventListener("click", () => insert("elements"));
  document.getElementById("action-insert-diagram").addEventListener("click", () => insert("diagram"));
  loadCorpus();
});

async function loadCorpus() {
  // The data bundle is hosted alongside the taskpane assets; same shape
  // as the browser extension's data/sections.json.
  try {
    const resp = await fetch("../data/sections.json");
    CORPUS = await resp.json();
    renderTopHits();
  } catch (err) {
    console.error("[Yuho] failed to load corpus", err);
    document.getElementById("results").innerHTML =
      `<li class="empty">Could not load Yuho corpus. The extension expects <code>data/sections.json</code> next to the taskpane bundle.</li>`;
  }
}

function renderTopHits() {
  const sample = Object.values(CORPUS).slice(0, 50);
  renderResults(sample);
}

function bodyForRecord(rec) {
  // Concatenate the searchable fields. Title is included so a token-AND
  // query like "induces delivery" hits s415 even when the word "delivery"
  // is in the body but the title is just "Cheating".
  const parts = [
    rec.section_title || "",
    rec.metadata?.summary || "",
    rec.raw?.text || "",
    rec.transpiled?.english || "",
  ];
  return parts.filter(Boolean).join("\n").toLowerCase();
}

function snippet(body, q) {
  const i = body.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return "";
  const start = Math.max(0, i - 30);
  const end = Math.min(body.length, i + q.length + 60);
  let s = (start > 0 ? "…" : "") + body.slice(start, end) + (end < body.length ? "…" : "");
  s = escape(s);
  const reEsc = q.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&");
  return s.replace(new RegExp(reEsc, "gi"), m => `<mark>${m}</mark>`);
}

function onSearch(ev) {
  const q = ev.target.value.trim();
  if (!CORPUS) return;
  if (!q) { renderTopHits(); return; }
  const ql = q.toLowerCase();
  const tokens = ql.split(/\s+/).filter(Boolean);
  const hits = [];
  for (const rec of Object.values(CORPUS)) {
    const num = rec.section_number.toLowerCase();
    const title = (rec.section_title || "").toLowerCase();
    const body = bodyForRecord(rec);
    const hay = `${num}\n${title}\n${body}`;
    if (!tokens.every(t => hay.includes(t))) continue;
    const annotated = Object.assign({}, rec);
    if (!num.includes(ql) && !title.includes(ql)) {
      // Pull a snippet from the original (non-lowercased) body for display.
      const origBody = [
        rec.metadata?.summary || "",
        rec.raw?.text || "",
        rec.transpiled?.english || "",
      ].filter(Boolean).join("\n");
      annotated._snippet = snippet(origBody, q);
    }
    hits.push(annotated);
    if (hits.length >= 100) break;
  }
  renderResults(hits);
}

function renderResults(records) {
  const ul = document.getElementById("results");
  ul.innerHTML = "";
  if (records.length === 0) {
    ul.innerHTML = `<li class="empty">No matches.</li>`;
    return;
  }
  for (const rec of records) {
    const li = document.createElement("li");
    const cov = rec.coverage || {};
    const tier = cov.L3 === "stamped" ? "L3" :
                 cov.L3 === "flagged" ? "FLAG" :
                 cov.L2 ? "L2" : "L1";
    li.innerHTML = `
      <button type="button" data-section="${rec.section_number}">
        <span class="num">s${escape(rec.section_number)}</span>
        <span class="title">${escape(rec.section_title || "(untitled)")}</span>
        <span class="tier tier-${tier.toLowerCase()}">${tier}</span>
        ${rec._snippet ? `<span class="snippet">${rec._snippet}</span>` : ""}
      </button>
    `;
    li.querySelector("button").addEventListener("click", () => selectSection(rec));
    ul.appendChild(li);
  }
}

function selectSection(rec) {
  SELECTED = rec;
  const detail = document.getElementById("detail");
  detail.hidden = false;
  document.getElementById("detail-title").textContent = `s${rec.section_number} — ${rec.section_title}`;
  document.getElementById("detail-sso").href = rec.sso_url || `https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr${rec.section_number}-#pr${rec.section_number}-`;
  document.getElementById("detail-summary").textContent =
    rec.metadata?.summary || rec.raw?.text || "(no summary)";
  document.getElementById("detail-yh").textContent = rec.encoded?.yh_source || "";
  loadDiagram(rec).catch(() => { /* non-fatal */ });
}

// Lazy-fetch + cache SVGs by section number. The diagram tab populates
// asynchronously so the panel doesn't block on file IO when scrolling
// search results.
const SVG_CACHE = new Map();

async function loadDiagram(rec) {
  const host = document.getElementById("detail-diagram");
  if (!host) return;
  const url = rec.transpiled?.mermaid_svg_url;
  if (!url) {
    host.innerHTML = `<p class="empty">No diagram for s${escape(rec.section_number)}.</p>`;
    return;
  }
  let svg = SVG_CACHE.get(rec.section_number);
  if (!svg) {
    host.innerHTML = `<p class="empty">Loading…</p>`;
    try {
      const res = await fetch(`../${url}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      svg = await res.text();
      SVG_CACHE.set(rec.section_number, svg);
    } catch (err) {
      host.innerHTML = `<p class="empty">Could not load diagram (${escape(String(err))}).</p>`;
      return;
    }
  }
  if (SELECTED && SELECTED.section_number === rec.section_number) {
    host.innerHTML = svg;
  }
}

// Convert an inline SVG string to a PNG dataURL by drawing it to a
// canvas. Returns the base64 PNG (without the "data:" prefix) suitable
// for Word's insertInlinePictureFromBase64.
async function svgToPngBase64(svg, scale = 2) {
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  try {
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = url;
    });
    const w = (img.naturalWidth || img.width || 800) * scale;
    const h = (img.naturalHeight || img.height || 600) * scale;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(img, 0, 0, w, h);
    return canvas.toDataURL("image/png").split(",", 2)[1];
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function insert(kind) {
  if (!SELECTED) return;
  const rec = SELECTED;

  // Diagram is a binary insert (PNG), not text — handle it separately.
  if (kind === "diagram") {
    const url = rec.transpiled?.mermaid_svg_url;
    if (!url) return;
    let svg = SVG_CACHE.get(rec.section_number);
    if (!svg) {
      try {
        const res = await fetch(`../${url}`);
        svg = await res.text();
        SVG_CACHE.set(rec.section_number, svg);
      } catch (err) {
        console.error("[Yuho] diagram fetch failed", err);
        return;
      }
    }
    let pngB64;
    try {
      pngB64 = await svgToPngBase64(svg);
    } catch (err) {
      console.error("[Yuho] svg → png conversion failed", err);
      return;
    }
    await Word.run(async (context) => {
      const range = context.document.getSelection();
      range.insertInlinePictureFromBase64(pngB64, Word.InsertLocation.replace);
      await context.sync();
    });
    return;
  }

  let text = "";
  switch (kind) {
    case "english":
      text = rec.transpiled?.english || "(no English transpilation available)";
      break;
    case "citation":
      text = `Penal Code 1871, s.${rec.section_number} (${rec.section_title}), `
           + `available at ${rec.sso_url}`;
      break;
    case "elements": {
      const yh = rec.encoded?.yh_source || "";
      const lines = yh.split("\n");
      const elements = [];
      let inElems = false, depth = 0;
      for (const line of lines) {
        if (!inElems && /^\s*elements\s*\{/.test(line)) {
          inElems = true; depth = (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length;
          continue;
        }
        if (inElems) {
          depth += (line.match(/\{/g) || []).length;
          depth -= (line.match(/\}/g) || []).length;
          if (depth <= 0) break;
          const m = line.match(/\b(actus_reus|mens_rea|circumstance|obligation|prohibition|permission)\s+\w+\s*:=\s*"([^"]+)"/);
          if (m) elements.push(`• [${m[1]}] ${m[2]}`);
        }
      }
      text = `Elements of s${rec.section_number} (${rec.section_title}):\n` +
             (elements.length ? elements.join("\n") : "(no typed elements found)");
      break;
    }
  }

  await Word.run(async (context) => {
    const range = context.document.getSelection();
    range.insertText(text, Word.InsertLocation.replace);
    await context.sync();
  });
}

function escape(s) {
  return (s || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}
