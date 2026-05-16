# WORKON-PIVOT-ASAP

Author: Claude (Opus 4.7), 2026-05-16
Owner: gabrielong@elegantelefant.com

## Goal (decided)

Primary: **GitHub stars** as validation. Secondary: portfolio/craft showcase.
Not a goal: SaaS revenue, paying customers, enterprise sales.

This means optimize for: HN front page hit, dev-Twitter screenshots, README virality, Awesome-list inclusion. Not: legal-tech sales motion.

## Direction (decided)

Pivot framing toward **legal / litigation timelines**, with adjacent legal use cases (investigations, depositions, discovery, regulatory chronologies). Keep **generative history / simulation** as a secondary HN angle.

Brand stays `Euclid`. New tagline candidates:
- "Litigation timelines as code."
- "git diff for facts."
- "Two narratives, one diff."

The killer demo is `euclid diff plaintiff.euclid defendant.euclid` rendering side-by-side timelines with contradictions highlighted. That is the screenshot.

## Honest market read (why this framing, not others)

[Inference, based on competitive scan 2026-05-16]

- *General timeline DSL*: dead-on-arrival vs Mermaid (85k stars, native GitHub render) + D2 (23.7k, commercial backing). No oxygen.
- *Writers / worldbuilders*: owned by GUI incumbents — Aeon Timeline, Plottr, World Anvil (3.5M users), Campfire. Audience does not install Haskell.
- *LLM agent memory / temporal KG*: hot but crowded — Zep/Graphiti, Mem0, MemoriesDB. Different product shape; abandons most code.
- *Legal / litigation*: incumbents are GUI SaaS (Casefleet, CaseBuilder, Resolver). The DSL-shaped surface is *empty*. Lawyers won't be users — but **devs who admire the framing will star it**. That's the stars-first play.
- *Generative / simulation*: small, loyal niche; pairs naturally w/ existing `for`/`while`/`fn`. Cheap to support as a second example pack.

Why "legal" works for *stars* even if no lawyer ever uses it: the framing is concrete and emotionally legible (everyone has watched a courtroom drama). "Two narratives, one diff" is a one-liner. HN loves legal-tech-meets-PL.

## Concrete IP that should remain front-and-center

These are already in the codebase. Reposition the README around them:

- `kind: branch | parallel | linear | loop` + `fork_from` + `merge_into` — formal branching/merging timelines. Mermaid timeline cannot do this.
- `euclid diff <a> <b>` — semantic diff of two timelines. The unique selling line.
- Custom `type`s w/ inheritance — schema for evidence/witness/claim/exhibit.
- Programmable: `fn`, `for`, `while`, `repeat`, `match` — generative timelines for the secondary angle.
- LSP + REPL + TUI — distinctive surface for devs (matters for stars, not for end-users).

## Phase 0 — repositioning (1–2 days, no new features)

Lowest cost. Do this even if everything else slips.

- [ ] Replace cabal `author: OpenAI Codex` w/ real name. Reads as AI-slop on HN; instant credibility hit.
- [ ] Rewrite `README.md` lede around "litigation timelines as code". Move syntax/usage below the fold.
- [ ] New top-of-README screenshot: `euclid diff plaintiff.euclid defendant.euclid` showing a side-by-side w/ contradictions highlighted (TUI screencap or SVG).
- [ ] New tagline beside logo: "git diff for facts."
- [ ] Replace `ww2.euclid` showcase position w/ a public-domain legal example (candidates: *Brown v Board*, *US v Microsoft*, *Watergate*, *Bridgegate*). Keep `ww2.euclid` and `lotr.euclid` under `examples/generative/` or `examples/historical/` as the secondary angle.
- [ ] Add `docs/LEGAL.md` walking through the killer demo end-to-end.
- [ ] Short asciinema/gif at top of README. // animated diff is the single most upvotable artifact

## Phase 1 — domain features (1–2 weeks)

Make the legal framing *credible* in code, not just docs.

Built-in entity types to add to `Euclid.Model.Types` and validation:

- [ ] `evidence` — fields: `citation: string`, `source: string`, `bates: string?`, `admissibility: string?`
- [ ] `witness` — fields: `affiliation: string?`, `credibility: int?`
- [ ] `claim` — contested assertion
- [ ] `fact` — uncontested assertion
- [ ] `exhibit` — fields: `number: string`, `description: string`
- [ ] `deposition` — fields: `deponent: string`, `date: date`

Built-in relationship labels w/ first-class semantics in the validator:

- [ ] `contradicts` — flag pairs in diagnostics
- [ ] `corroborates`
- [ ] `supersedes`
- [ ] `caused` / `enabled` / `preceded`
- [ ] `cites` (evidence -> claim/fact)
- [ ] `impeaches` (evidence -> witness)

New validator checks (extend `Euclid.Core.Validation`):

- [ ] Contradiction detection: if `A -["contradicts"]-> B` and both appear on the same timeline, surface as a structured diagnostic w/ source spans.
- [ ] Uncited-claim warning: `claim` entity with no inbound `cites` rel.
- [ ] Witness-without-deposition warning.
- [ ] Timeline-coverage check: gap detection between `appears_on` ranges for an entity that's marked `continuous: true`.

CLI additions:

- [ ] `--narrative <name>` filter flag on `run`/`export` — render only entities tagged with a given narrative (e.g. plaintiff vs defendant).
- [ ] `euclid contradict <file>` — list every `contradicts` edge w/ both sides' supporting evidence.
- [ ] `euclid exhibits <file>` — emit an exhibit list (CSV) for court filing aesthetics.

Render layer:

- [ ] Extend `Render/SVG.hs` and `Render/HTML.hs` to color-code by narrative tag.
- [ ] Diff-render: side-by-side two-column SVG/HTML w/ contradictions drawn as crossing lines. // this is the marketing screenshot

## Phase 2 — distribution (1–2 weeks)

Stars come from distribution, not features. Do at least the WASM playground and the Mermaid embed.

- [ ] **WASM build** of `euclid check` + `euclid export` so the landing page can run examples in-browser. Use `wasm32-wasi` via GHC's JS/Wasm backend or compile parser/eval to JS via Asterius/GHCJS — [Unverified] which is current-stable in May 2026; verify before committing.
- [ ] **Polish `Render/Mermaid.hs`** so a Euclid file can produce a Mermaid timeline embeddable in GitHub READMEs natively. This piggybacks on Mermaid's GitHub-native render moat instead of fighting it.
- [ ] **Landing page** at `gongahkia.github.io/euclid` (static): logo, tagline, animated diff gif, three runnable WASM examples (legal / generative / historical), install one-liner.
- [ ] **Static docs site** via `mdBook` or `hakyll` (already in Haskell ecosystem): SYNTAX.md, LEGAL.md, GENERATIVE.md, recipes.
- [ ] **Real legal-case example pack** in `examples/legal/`: 3–5 hand-modeled public-domain cases. *Brown v Board* and *US v Microsoft* are obvious. // emotional resonance matters for HN
- [ ] **VS Code extension** wrapping the existing LSP. Even a thin one. Star-bait for devs.

## Phase 3 — launch (1 day, do this last)

- [ ] **Show HN title** (test 2–3, pick one):
  - "Show HN: Euclid – a DSL for litigation timelines, with diff between two narratives"
  - "Show HN: Euclid – git diff, but for facts"
  - "Show HN: Modeling legal cases as code (Haskell DSL + TUI + diff)"
- [ ] **Body**: lead w/ the diff demo. Mention WASM playground link. Mention it's a side project. Be a present author in the thread.
- [ ] **Timing**: [Inference] HN US-morning weekday gets best front-page odds; [Unverified] check current HN posting-time analyses before submitting.
- [ ] **Crosspost** (staggered, not same day): `r/programming`, `r/haskell`, `r/programminglanguages`, `r/law` (carefully — community is allergic to "lawyer-replacing tech"; frame as visualization, not automation), Lobsters, dev.to.
- [ ] **Submit to Awesome lists**: awesome-haskell, awesome-legal-tech, awesome-dsl, awesome-diagrams.
- [ ] **Twitter/Bluesky thread** w/ the diff gif.

## What to explicitly NOT do

- Do not build a SaaS / hosted product. Not the stated goal.
- Do not pursue the writers' worldbuilding market. Saturated, GUI-locked.
- Do not chase the LLM-agent-memory pivot. Different product, crowded.
- Do not auto-refactor outside the diff implied by each task above.
- Do not strip the `lotr.euclid` / `ww2.euclid` examples — they become the "generative / historical" bonus angle, useful for variety in launch screenshots.
- Do not add floating-point, fuzzy dates, `*`/`/`, or unary `!` just because the syntax doc lists them as missing. Out of scope for this pivot.

## Risks / honest caveats

[Inference] on all of these:

- Real lawyers won't be users. The stars come from devs reacting to the framing. If "real legal adoption" later becomes a goal, the surface needs a full rebuild (GUI, hosted, integrations w/ Westlaw/PACER).
- HN reaction to "AI-built" tools is increasingly hostile. The `author: OpenAI Codex` line in cabal must go before launch.
- Mermaid timeline + GitHub-native render is the dominant gravity well. The Mermaid backend (Phase 2) is an alliance, not a competition — keep it.
- "git diff for facts" framing risks the legal-realism critique ("facts aren't binary, contradictions are interpretive"). Have a one-paragraph response ready. It's a *modeling tool*, not a truth oracle.

## Stars target (calibration)

[Speculation] given comparable Haskell-DSL + diagram-tool launches:

- Floor (do Phase 0 only): ~100–300 stars from a soft launch.
- Median (Phase 0–2 done, decent Show HN): ~800–2000 stars in week 1, settling ~1.5–3k over 6 months.
- Ceiling (everything lands + Mermaid embed catches on + a tech-influencer signal-boosts): ~5–8k stars. Beyond that requires becoming infrastructure, which contradicts the stated goal.

## Decision log

- 2026-05-16: Goal set to stars-first / portfolio. Direction set to legal-litigation pivot w/ generative-history as secondary. SaaS, writers, agent-memory pivots rejected.
