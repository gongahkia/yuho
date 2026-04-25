# Yuho — Penal Code explorer (static site)

A static HTML site over the encoded Singapore Penal Code 1871 corpus.
Citable URLs, search-indexable, no build chain — single-file generator
that writes a flat tree to `build/` from the canonical JSON corpus.

This is the third UI over the same data layer. The browser extension
(`editors/browser-yuho/`) is the headline product demo; this static
site is the citable research artefact tail.

## Layout

```
editors/explorer-site/
├── build.py        # generator (Python stdlib only, no deps)
├── build/          # generated output (deploy this)
│   ├── index.html
│   ├── coverage.html
│   ├── flags.html
│   ├── about.html
│   ├── s/<N>.html   # 524 per-section pages
│   └── static/{style.css,search.js,index.json}
└── README.md
```

## Build

```sh
# Pre-req: corpus
python3 scripts/build_corpus.py

# Generate the site
python3 editors/explorer-site/build.py

# Preview
python3 -m http.server -d editors/explorer-site/build 8000
# → http://localhost:8000
```

## Pages

- `/` and `/index.html` — searchable index of all 524 sections with badges.
- `/coverage.html` — L1 / L2 / L3 dashboard.
- `/flags.html` — table of L3-flagged sections.
- `/about.html` — methodology, citation, disclaimer.
- `/s/<N>.html` — per-section pages (e.g. `/s/415.html` for cheating).

Each per-section page renders:
- Coverage badges and SSO deep-link
- Flag callout (if flagged for L3 review)
- Summary
- Canonical SSO text
- Controlled-English transpilation
- Structural counts (elements, illustrations, subsections, exceptions, case law, effective dates)
- Outgoing and incoming reference tables (G10) with link-through
- Full encoded `.yh` source
- Provenance footer (raw SHA-256, Yuho version, generation timestamp)

## Deploy

The `build/` directory is plain static HTML. Deploy by copying it to
any static host:

- **GitHub Pages**: push `build/` to a `gh-pages` branch.
- **Cloudflare Pages**: point at the repo, set build command to
  `python3 scripts/build_corpus.py && python3 editors/explorer-site/build.py`,
  output dir `editors/explorer-site/build`.
- **Netlify**: same as Cloudflare.
- **Plain S3 / R2 / Spaces**: `aws s3 sync build/ s3://my-bucket/`.

## Why static?

- Every page has a citable URL (`https://yuho.dev/s/415.html` etc.).
- Search-indexable: Google can pick up a per-section page when a researcher
  searches for "section 415 Singapore cheating".
- Survives the project: even if the codebase moves on, an old `build/`
  remains a dated, auditable snapshot.
- No JS framework, no Node toolchain, no Webpack. The generator is one
  Python file with stdlib-only imports.

## Disclaimer

Same as the rest of the project: research / educational artefact, not
legal advice. Cross-reference with the
[canonical SSO source](https://sso.agc.gov.sg/Act/PC1871) for any
decision that matters.
