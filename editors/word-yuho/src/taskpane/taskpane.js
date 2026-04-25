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

function onSearch(ev) {
  const q = ev.target.value.trim().toLowerCase();
  if (!CORPUS) return;
  if (!q) { renderTopHits(); return; }
  const hits = Object.values(CORPUS).filter(rec => {
    return rec.section_number.toLowerCase().includes(q)
        || (rec.section_title || "").toLowerCase().includes(q);
  }).slice(0, 100);
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
}

async function insert(kind) {
  if (!SELECTED) return;
  const rec = SELECTED;
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
