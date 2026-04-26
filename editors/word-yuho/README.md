# Yuho — Singapore Penal Code companion (Word add-in)

Office Add-in that lives in the **Insert** ribbon of Microsoft Word
(desktop + web). Lawyers and law students working in Word can:

- search the encoded Singapore Penal Code 1871 by section number or title
- inspect Yuho's enrichment for a section: summary, English transpilation, encoded `.yh`
- insert the controlled-English transpilation, a formatted citation, or
  a bulleted element list directly into the active document

This is the **practitioner-facing surface** described in the project's
delivery order — it sequences after the citable research artefacts
(paper, JSON corpus, browser extension, static explorer site) per the
plan in [`/TODO.md`](../../TODO.md).

## Layout

```
editors/word-yuho/
├── manifest.xml                      # Office Add-in manifest (taskpane + ribbon)
├── package.json                      # office-addin-debugging tooling
├── data/                             # symlink/copy of browser-yuho/data/
└── src/
    ├── taskpane/
    │   ├── taskpane.html
    │   ├── taskpane.css
    │   └── taskpane.js               # search + insert via Word.run()
    ├── commands/                     # (reserved for future ribbon commands)
    └── assets/                       # icons (16/32/80/128 PNG)
```

## Build the data bundle

The Word add-in reads the same slim corpus as the browser extension. To
populate `data/sections.json`:

```sh
# pre-req: encoded corpus
python3 scripts/build_corpus.py

# generate the slim bundle, then copy into the Word add-in
python3 editors/browser-yuho/build_data.py
cp -r editors/browser-yuho/data editors/word-yuho/
```

(The `npm run build:data` script in `package.json` automates this.)

## Sideload during development

Office Add-ins require a host machine with Office installed (desktop) or
a Microsoft 365 account (web). Steps:

```sh
cd editors/word-yuho
npm install                                  # one-time
npm start                                    # starts dev server + sideloads
```

Then in Word, the **Yuho** group appears under the **Home** ribbon.

For Word for the Web, open
[https://office.com](https://office.com), open a new doc, and follow
[Microsoft's sideload guide](https://learn.microsoft.com/en-us/office/dev/add-ins/testing/sideload-office-add-ins-for-testing).

## Distribution (deferred)

- Microsoft AppSource publish (stretch) — same data, vendor-reviewed.
- Centralised tenant deployment for organisations.

Both are stretch goals; for now the add-in runs in developer/sideload mode.

## Permissions

- `ReadWriteDocument` — required so the add-in can insert the selected
  text into the document.

## Disclaimer

The add-in is a research / educational artefact. It does not provide
legal advice. The encoded statute is a structural representation of the
Penal Code drafted from publicly available SSO text; cross-reference
with the [canonical SSO source](https://sso.agc.gov.sg/Act/PC1871) for
any decision that matters.
