# What I learned encoding 524 sections of penal law into a DSL

> Companion to the paper *Yuho: A Domain-Specific Language for Encoding the Singapore Penal Code as Executable Statute*. The paper has the citations, methodology, and proofs; this post is the messier story of what the work actually looked like from inside it. For the formal version see [`paper/main.tex`](../main.tex).

## TL;DR

I spent a year building **Yuho**, a domain-specific language whose grammar mirrors the way a criminal statute is actually drafted, and used it to encode all **524 sections** of the Singapore Penal Code 1871. Around it grew a tree-sitter parser, eight transpilers, a reference-graph resolver, a Z3/Alloy verification hookup, an LSP, an MCP server, a VS Code extension, and a Lean 4 mechanisation of the soundness theorem. Two things stand out from the journey: (1) the gap between drafted penal text and an executable artefact is **smaller than I expected** going in, and (2) most of my early "grammar bugs" turned out not to be grammar bugs at all.

## Why I started

I'd been reading Sergot et al.'s 1986 paper on the British Nationality Act, Catala on French tax code, and Akoma Ntoso on legal markup. The pattern across all of them is that statute *looks* like code — numbered sections, enumerated elements, "or both" penalty clauses, illustrations, exceptions — but the gap between recognising that and actually encoding a whole production statute kept defeating people. Every published encoding I found stopped at toy examples, or sampled a few sections, or fell back on free-text strings the moment the prose got dense.

I wanted to find out where the wall actually was. So I picked one statute (the Singapore Penal Code, because it's public and modestly sized) and tried to encode every section.

## What surprised me

**The grammar fell out faster than I thought.** I started with what I thought was a minimum viable shape: section header, elements list, penalty, exceptions. By section 30 I had a rough catalogue of every recurring drafting pattern. By section 100 the grammar had converged. The remaining 424 sections didn't introduce a single new top-level construct — only refinements (deontic types, burden qualifiers, cross-reference edges) that fit into the existing skeleton.

**Most "grammar bugs" weren't grammar bugs.** Mass-encoding surfaced fourteen things I initially flagged as `G1`–`G14` grammar gaps. I went back through them at the end and found:

- **G2 and G7** weren't grammar gaps on re-test. They were artefacts of how I was running the tests.
- **G10** (cross-section composition) was a semantic-resolver problem, not a parser one. The grammar already accepted the syntax; what was missing was the runtime that resolves `is_infringed(s79)` to s79's actual conviction predicate.
- The other eleven were genuine grammar limitations and got fixed.

This was the methodological lesson of the whole project: it's tempting to bolt new grammar features on every time something looks weird, but the resulting grammar bloats with no fidelity gain. Classifying each shortcoming by the layer that resolves it (parser / linter / semantic resolver / not-a-gap) caught the misclassifications before they hardened into syntax.

**The longest tail wasn't grammar — it was prose-to-structure fidelity.** Once the grammar settled, the slow work was checking that each encoded section faithfully represents what the SSO text actually says. I built an 11-point human-audit checklist (the "L3 stamp") and ran it on every section. It took weeks. The paper's §Limitations is honest about this: L3 is author-administered. External-reviewer validation is genuinely future work, not a polite shrug.

## A worked example

```yuho
statute 378 {
  title: "Theft"
  elements: [
    actus_reus  movesProperty,
    mens_rea    intendsToTake { intent: dishonestly },
    circumstance withoutConsent,
  ]
  penalty: cumulative {
    imprisonment(max: 3 years),
    fine(max: any_amount),
  }
  illustration "A takes B's umbrella from a stand without consent..."
  effective: 1872-09-16
}
```

Every element carries a **deontic type** (`actus_reus` / `mens_rea` / `circumstance` / `obligation` / `prohibition` / `permission`) and an optional **burden qualifier** (`burden prosecution` / `burden defence`) with a named proof standard. Penalty clauses compose three top-level combinators (`cumulative` / `alternative` / `or_both`) plus a `when <ident>` conditional. Exceptions form a Catala-style **priority DAG**.

Reading a section and reading its `.yh` encoding side-by-side feels like reading the same thing in two notations. That was the bar I was aiming for.

## What I got wrong

**I underestimated how much work the verification stack would generate.** I started building Yuho because I wanted *one* clean encoding of penal law. Halfway through I realised that without verification — Z3, Alloy, structural diffs, runtime tests — I had no answer to the obvious question "how do you know your encoding is right?" So I built the verification stack, and that took roughly as long as the encoding itself.

**Defeats-edge SAT was a humbling moment.** I built a Z3-backed sweep that exercises every general-defence override edge in the corpus — for each `(offence, defence)` pair, can the solver find a fact pattern where both fire simultaneously? Initial run: **91.1%** SAT (1141 of 1253 edges). My first reaction was to assume the encoder was wrong on the failing 112. Six hours of investigation later: zero of those 112 were Z3-level inconsistencies. They split as **39 doctrinal mis-pairings** (interpretation-only sections that aren't standalone offences and shouldn't be paired with general defences in the first place — a fixture-corpus shape problem) and **73 CLI-side encoder gaps** (`narrow-defence` couldn't follow `referencing penal_code/sN_*` directives or recurse into nested `subsection` blocks, so the host-section's elements weren't visible). After filtering the doctrinal mis-pairings and patching the CLI: **1214/1214 = 100%** SAT on the well-posed corpus.

The lesson: when a fancy verification tool tells you something is wrong, the bug is usually in the part of the system you didn't think of as the system. The Z3 backend was correct end-to-end; the input-shaping layer wasn't.

**I overestimated how much the LLM benchmark would tell me about the encoding.** I ran a 205-fixture benchmark across three OpenAI models under four prompt variants. The headline that *one* prompt variant Pareto-improves on gpt-4o-mini (T1 48.8% / T2 exact 37.1% / F1 0.699) was a clean finding. But the deeper lesson was a **polarity-negative collapse**: o3-mini misclassifies fact patterns whose null-cues invert the doctrinal polarity, *despite* its reasoning-token spend, while gpt-4o doesn't. That's a benchmark finding about cross-model variance, not a finding about Yuho. I had hoped for stronger model-vs-encoded-library agreement; the benchmark mostly told me about model failure modes.

## Numbers from the corpus

- **524 / 524** sections pass parse-and-build (L1+L2).
- **524 / 524** carry an L3 fidelity stamp.
- **2 179** elements across the corpus, mean 4.16 per section.
- **254** verbatim illustration blocks.
- **650** subsection nestings.
- **66** exception priority-DAG entries.
- **139** sections carry behavioural-test companions (`test_statute.yh`); CI gate is `make verify-runtime-tests` reporting **139/139** pass. The remaining 385 are interpretation/definition provisions where parse + lint + structural-diff is the appropriate bar.
- **524 / 524** verbose-Mermaid render (0 orphan nodes; `make verify-mermaid-verbose`).
- **524 / 524** structural-diff matched between the Python Z3 emitter and the verified Lean spec (`make verify-structural-diff-full --strict`).
- **1214 / 1214 = 100%** defeats-edge SAT on the well-posed corpus.

## The verification stack — and what it does *not* claim

The stack does **not** adjudicate legal correctness. "Machine-checkable" in the paper means narrower: structural and inter-section consistency. What that buys in practice:

- **Z3 / Alloy hookup** — every encoded section's elements, exceptions, and penalty combinators emit SMT-LIB and Alloy formulas. The defeats-edge sweep above is the headline empirical claim from this layer.
- **Lean 4 mechanisation** — the soundness theorem (5 lemmas spanning element evaluation, exception priority, penalty composition, cross-section composition, and sentinel propagation) kernel-checks under Lean 4.10.0 with no `sorry`s. The conviction-layer oracle is discharged constructively. The most recent layer (v9) ships an `ElementDeep` AST with `crossRef` / `applyScope` constructors, a fuel-bounded recursive evaluator, and a conservative-extension theorem showing the v9 layer adds capacity without perturbing v4–v8 correctness.
- **Reference-graph resolver** — Tarjan-SCC analysis on cross-references plus the lam4-style `is_infringed` and Catala-style `apply_scope` cross-section predicates.
- **Fidelity diagnostics** — a separate linter pass cross-checks encodings against the canonical SSO scrape.

## Case-law differential testing

I built a parallel evaluation against reported Singapore Penal Code judgments — 43 fixtures, three scorers:

- **Top-1**: 51.2% / **Top-3**: 53.5% (the recommender picks the right charge from the encoded library given the court's fact pattern).
- **Contrast-F1**: 0.239 (a strict scorer that penalises both false-positive and false-negative section recommendations).
- **Constrained-contrast consistency**: 100% on n=25 (within the constrained scorer's vocabulary, the encoding is internally consistent on every tested fixture).

The recommender top-1 of 51.2% is honestly weak. The failure cases are mostly cross-chapter near-misses (e.g. theft vs. criminal-breach-of-trust on facts where the principal was technically an agent), which is exactly the doctrinally-hard distinction. I think with a bigger fixture corpus this number moves, but I'm not going to oversell what I have.

## Cross-jurisdiction — the IPC experiment

Singapore inherits the Anglo-Indian drafting tradition. Two days before the deadline I asked: does the grammar I built for SG transfer? I scraped the full Indian Penal Code 1860 (493 sections) and encoded 8 representative pairs — s300 (Murder), s302, s375 (Rape), s376, s378 (Theft), s420 (Cheating), s497 (Adultery — IPC criminalises, SG never did), s509 (Insulting modesty — SG repealed and replaced with the gender-neutral s377BA).

Result: every encoded IPC section parses + lints clean under the SG-derived grammar. Zero grammar extensions needed. The `yuho refs --compare-libraries` tool reports **399 shared section numbers** between the two corpora — about 80% structural overlap. That's a much stronger transferability signal than I expected from such a small sample.

The headline divergences (s497 — adultery; s509 → s377BA migration) are exactly the doctrinal modernisation points worth pulling into the paper §8 prose. Full IPC encoding (493 sections) is months of agent runs and is explicitly future work.

## Why criminal law and why Singapore?

Three reasons that all turned out to matter:

1. **Public.** Singapore Statutes Online hosts the canonical text under permissive terms. No paywall to fight.
2. **Modestly sized.** 524 sections is small enough to mass-encode by hand, large enough that you can't pretend hand-picked toy examples are representative.
3. **Lineage.** Singapore inherits Anglo-Indian drafting (short numbered sections, in-line illustrations, "or both" penalty clauses, Chapter IV general exceptions) shared with Indian, Pakistani, Bruneian, and Malaysian penal codes. The IPC experiment above suggests the grammar travels.

## What this paper is *not*

It is not a claim that the encoded sections constitute legal advice. The author-administered L3 fidelity stamp is not a court reading or a practitioner's judgement. Yuho is not the right tool for every legal-encoding problem — regulatory corpora, contract drafting, treaty interpretation, and judgment summarisation each have grammars Yuho doesn't natively model.

It *is* a claim that the gap between a drafted penal section and an executable artefact is **narrower** than the existing literature suggests, and that an appropriately-shaped grammar dissolves a class of previously-reported encoding obstacles, leaving a residue tractable at full coverage for one statute family.

## What's next

Three concrete strands, plus an honest roadmap of bigger deferred work:

1. **Cross-jurisdiction at full coverage.** Extend the IPC encoding from 8 sections to all 493 via the agent-dispatch pipeline. Phase 2 of `yuho refs --compare-libraries` (SCC overlap, divergent amendment paths, sections renumbered/added/repealed) unlocks once the IPC corpus is fully encoded.
2. **Deeper precedent integration.** Lifting case-law holding strings into structured constraints that modify element burden qualifiers when the matching predicate fires. Right now the L3 stamp records caselaw anchors as opaque strings; the next step is making them load-bearing.
3. **Evaluator-side `apply_scope`.** Elaborating the cross-section composition primitive into a full element-graph executor that returns bindings, not just a structural "does this scope exist" predicate.

Beyond these, three deferred-but-explicit phases (the paper's §Conclusion roadmap):

- **Phase 2A — diachronic depth.** Every section gets every historical version since 1872; `yuho check --as-of 1995-06-15` becomes a first-class query.
- **Phase 2B — vision pivot.** Move beyond Penal Code into Evidence Act, CPC, Constitution, Contract Law.
- **Phase 2C — interactive learn-by-doing.** Per-section JS fact-builders for law students. Co-author a classroom trial.

Each of those is months of work and I'd rather defer them honestly than gesture at them as imminent.

## What I'd tell my past self

If I were starting again I'd do four things differently:

1. **Build the verification stack at section 30, not section 524.** I encoded most of the corpus before the verification harness was load-bearing. Half the bugs the harness eventually found could have been caught earlier if I'd had it sooner.
2. **Distinguish grammar gaps from linter gaps from semantic-resolver gaps from the start.** I learned this discipline halfway through; before that I shipped grammar features that should have been linter rules.
3. **Don't over-trust your own L3 stamps.** The 11-point checklist is honest but partial. External-reviewer validation is the missing piece.
4. **The cross-jurisdiction question is worth asking earlier.** I treated IPC as future work for most of the project; the actual experiment took two days. Two days at month three would have shaped a lot of grammar decisions differently.

That's most of what I learned. The rest is in the paper.

## Artefact

The Yuho compiler, encoded library, and tooling are open-source at <https://github.com/gongahkia/yuho>. The paper itself — including the build pipeline that injects coverage statistics into the manuscript at compile time — lives in the same repository under [`paper/`](../).
