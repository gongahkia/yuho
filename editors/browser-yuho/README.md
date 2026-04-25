# Yuho — Singapore Penal Code companion (browser extension)

A browser extension that overlays Yuho's structured encoding on top of the
canonical Singapore Penal Code on
[Singapore Statutes Online](https://sso.agc.gov.sg/Act/PC1871). On every
section heading you get a small `Yuho · L1/L2/L3` badge; clicking it opens a
side panel with:

- **Overview** — one-paragraph summary, structural counts, coverage state, L3 flag (if any).
- **English** — controlled-English transpilation of the encoded `.yh`.
- **Elements** — extracted `elements`, `penalty`, and `exceptions` blocks.
- **References** — outgoing and incoming cross-section edges (G10).
- **.yh source** — the raw Yuho encoding for the section.

The extension reads from a bundled JSON corpus generated from the
version-controlled `library/penal_code/`. Nothing is fetched from external
servers; nothing leaves the browser. The corpus refreshes only when the
extension is rebuilt.

## Layout

```
editors/browser-yuho/
├── manifest.json                   # Manifest V3
├── build_data.py                   # Slim corpus → data/sections.json
├── data/                           # generated, do not edit by hand
│   ├── index.json
│   └── sections.json
└── src/
    ├── content/
    │   ├── content.js              # SSO DOM walker + panel UI
    │   └── panel.css
    ├── background/
    │   └── service_worker.js       # toolbar action handler
    └── assets/
        └── icon-{16,32,48,128}.png
```

## Build

```sh
# 1. Make sure the canonical corpus exists
python3 scripts/build_corpus.py

# 2. Generate the slim bundle the extension ships with
python3 editors/browser-yuho/build_data.py
```

That populates `editors/browser-yuho/data/{index.json,sections.json}`.

## Install (developer mode)

### Chrome / Edge / Brave / Arc / Vivaldi

1. Visit `chrome://extensions` (or the equivalent for your browser).
2. Toggle **Developer mode** on.
3. Click **Load unpacked** and pick `editors/browser-yuho/`.
4. Visit any page under `https://sso.agc.gov.sg/Act/PC1871`.

### Firefox

Manifest V3 support is now stable in Firefox 115+. Steps:

1. Visit `about:debugging#/runtime/this-firefox`.
2. Click **Load Temporary Add-on…** and pick `editors/browser-yuho/manifest.json`.
3. Visit any page under `https://sso.agc.gov.sg/Act/PC1871`.

### Safari

Safari requires conversion via Xcode's
[`safari-web-extension-converter`](https://developer.apple.com/documentation/safariservices/safari_web_extensions/converting_a_web_extension_for_safari).
Not yet automated.

## Permissions and data flow

- `host_permissions: ["https://sso.agc.gov.sg/*"]` — required for the
  content script to attach to SSO pages.
- `storage` — reserved for future user prefs (panel pinning state, default
  tab). Currently unused.
- No outbound network requests. The bundled corpus is loaded via
  `chrome.runtime.getURL`, never via `fetch` to a remote host.

## Roadmap

This is the v0 implementation. Outstanding before publication:

- [ ] Inline citation tooltips: hover over an `s415` mention anywhere on
      the SSO page, see the marginal note + penalty range without leaving
      the body of the rendered section.
- [ ] Search box at the top of the panel: jump between sections without
      navigating SSO.
- [ ] User preferences: pinned vs floating panel, default tab, dark mode
      override.
- [ ] Per-tab badges: section number in the toolbar action shows the
      currently focused section's coverage tier.
- [ ] Re-render Mermaid diagrams in the panel (today the panel skips the
      Mermaid block to keep the bundle small; would need to ship a
      Mermaid renderer or pre-render the SVG into the corpus).
- [ ] Marketplace publish: Chrome Web Store, Firefox AMO, Edge Add-ons,
      Safari Extensions Gallery (each is a separate review pipeline).

## Disclaimer

The extension is a research / educational artefact. It does not provide
legal advice. The encoded statute is a structural representation of the
Penal Code drafted from publicly available SSO text; cross-reference with
the canonical SSO source for any decision that matters.
