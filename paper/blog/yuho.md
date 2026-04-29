# Yuho: encoding the Singapore Penal Code as executable statute

> A blog-style summary of the paper *Yuho: A Domain-Specific Language for Encoding the Singapore Penal Code as Executable Statute*. For the full version with citations, methodology, and proofs, see [`paper/main.tex`](../main.tex).

## TL;DR

I built **Yuho**, a domain-specific language whose grammar mirrors the structure of criminal statutes — section headers, elements, penalty combinators, illustrations, exceptions — and used it to encode every one of the **524 sections** of the Singapore Penal Code 1871. The encoding parses, lints, and carries an author-administered fidelity stamp at the strictest tier on all 524 sections. Around it sits a tree-sitter parser, eight transpilers (JSON, controlled English, LaTeX, Mermaid flowchart and mindmap, Alloy, DOCX, Akoma Ntoso), a reference-graph resolver, a Z3/Alloy verification hookup, a Language Server, an MCP server, and a VS Code extension. A Lean 4 mechanisation kernel-checks the soundness theorem.

The thesis: the gap between drafted penal sections and an executable artefact is **smaller than the literature suggests**, and an appropriately-shaped grammar dissolves a class of previously-reported encoding obstacles.

## The problem

Statutes are not free-form prose. A modern penal code is drafted to a tight internal grammar — numbered sections, enumerated elements, in-line illustration blocks, cross-cutting general exceptions, "or both" penalty clauses. Lawyers learn to read this structure as if it were a typed program. Computer scientists have noticed since at least Sergot et al.'s 1986 encoding of the British Nationality Act that statutes are amenable to symbolic representation.

The persistent gap is not the recognition that statute looks like code. It is the practical absence of a representation expressive enough to encode an *entire* production statute without falling back on free-text strings.

Existing work clusters into three camps:

- **Logic programming** — statute as Horn clauses (Sergot et al., bench-capon).
- **Markup** — statute as structured XML for archival and exchange (Akoma Ntoso, LegalRuleML).
- **Modern DSLs** — pick a sub-domain and build focused syntax (Catala for French tax code, lam4 for contracts and regulations, LexScript for contract compilation, LDOC for plain-text DOCX authoring).

None target a common-law **penal** code at full coverage. None expose primitives matching how penal sections are actually drafted: an offence is a typed conjunction of elements; a penalty is a small algebra over imprisonment / fine / caning / death; an exception is a prioritised override; an illustration is a verbatim worked example tied to a parent section; an amendment is a new `effective <date>` clause that doesn't erase the prior text.

## What Yuho looks like

The top-level construct is a `statute N { ... }` block:

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

Elements carry a **deontic type** (`actus_reus` / `mens_rea` / `circumstance` / `obligation` / `prohibition` / `permission`), an optional **burden qualifier** (`burden prosecution` / `burden defence`) with a named proof standard, and optional causal (`causedBy`) and temporal (`precedes` / `during` / `after`) edges to other elements.

Penalty clauses compose three top-level combinators (`cumulative` / `alternative` / `or_both`) plus a `when <ident>` conditional and a nested-combinator escape hatch.

Exceptions form a Catala-style **priority DAG** with optional `defeats` edges to the elements they override.

## The fourteen grammar gaps

Mass-encoding 524 sections surfaced a catalogue of **fourteen grammar gaps** (`G1`–`G14`). The methodological contribution is a discipline for distinguishing genuine grammar limitations from fidelity issues *masquerading* as grammar issues, by classifying each shortcoming according to the layer at which it gets resolved (parser, linter, semantic resolver, or not-a-gap-on-re-test).

Three gaps were reclassified during the work:

- **G2** and **G7** turned out not to be grammar gaps at all on re-test.
- **G10** is deferred — its remaining work is a semantic-resolver pass, not a parser extension.

The headline claim: conflating grammar gaps with linter gaps leads to grammar bloat with no corresponding gain in fidelity. The classification surfaces grammar-design feedback (e.g. a low-precision lint may indicate the grammar should disambiguate at the source) that a flat gap list does not.

## Numbers from the corpus

- **524 / 524** sections pass parse-and-build (L1+L2).
- **524 / 524** carry an author-administered L3 fidelity stamp. (External-reviewer validation is future work.)
- **2,179** elements across the corpus, mean 4.16 per section.
- **254** verbatim illustration blocks.
- **650** subsection nestings.
- **66** exception priority-DAG entries.
- **82** sections carry behavioural-test companions (28 hand-authored on high-traffic offences like s299/s300 homicide, s378 theft, s415 cheating, s463 forgery; 54 use a universal-shape predicate). The remaining 442 are interpretation/definition provisions where parse + lint is the appropriate bar.

## The verification stack (and what it does *not* claim)

The verification stack does **not** adjudicate legal correctness. What "machine-checkable" means in this paper is narrower: the encoding's structural and inter-section consistency is checkable.

What that buys you in practice:

- **Z3 / Alloy hookup** — every encoded section's elements, exceptions, and penalty combinators emit SMT-LIB and Alloy formulas. The "defeats-edge structural-coverage sweep" exercises every general-defence override; 91.1% of 1,253 edges across 147 sections clear SAT.
- **Lean 4 mechanisation** — the soundness theorem (5 lemmas spanning element evaluation, exception priority, penalty composition, cross-section composition, and sentinel-propagation) kernel-checks under Lean 4.10.0 with no `sorry`s. The conviction-layer oracle is discharged constructively via `Generator.lean`'s `canonicalSMTModel` / `canonicalGraphModel`.
- **Reference-graph resolver** — Tarjan-SCC analysis on cross-references plus the lam4-style `is_infringed` and Catala-style `apply_scope` cross-section predicates.
- **Fidelity diagnostics** — a separate linter pass cross-checks encodings against the canonical SSO scrape. Phase D cleared four diagnostic buckets (G4=98 hits, fab-fine=48, fab-caning=2, G11=208).

## The LLM benchmark

We ran a 205-fixture benchmark against three OpenAI models (gpt-4o-mini, gpt-4o, o3-mini) under four prompt variants (baseline / polarity / polarity-soft / polarity-conditional). The headline finding: **`polarity-conditional` is the only Pareto-improving variant on gpt-4o-mini** (T1 48.8% / T2 exact 37.1% / F1 0.699 / T3 93.7%).

A more interesting finding: a polarity-negative collapse — where the model misclassifies fact patterns whose null-cues invert the doctrinal polarity — reproduces on o3-mini *despite* its reasoning-token spend, but **not** on gpt-4o. The cross-model split is itself a benchmark finding.

## Case-law differential testing

A separate evaluation strand checks Yuho's recommend-mode outputs against 38 reported Singapore Penal Code judgments using three scorers:

- **Top-1**: 44.7% / **Top-3**: 47.4% / **MRR**: 0.461.
- **Contrast-F1**: 0.239 (a strict scorer that penalises both false-positive and false-negative section recommendations on the same fact pattern).
- **Constrained-contrast consistency**: 100% (n=25). Within the constrained scorer's vocabulary, Yuho is internally consistent on the 25 fixtures we have.

## Why criminal law and why Singapore?

Three pragmatic reasons:

1. **Public**. Singapore Statutes Online hosts the canonical text under permissive terms.
2. **Modestly sized**. 524 sections is small enough to mass-encode, large enough to surface structural patterns hand-picked toy examples would miss.
3. **Lineage**. Singapore inherits the Anglo-Indian drafting tradition (short numbered sections, in-line illustrations, "or both" penalty clauses, Chapter IV general exceptions) shared with Indian, Pakistani, Bruneian, and (with adjustments) Malaysian penal codes. Whether a grammar that fits Singapore is portable across the wider family is an empirical question we have not yet tested. The structural overlap makes it worth asking.

## What this paper is *not*

It is not a claim that the encoded sections constitute legal advice. The author-administered L3 fidelity stamp does not replace a court's reading or a legal practitioner's judgement. Yuho is not the right tool for every legal-encoding problem — regulatory corpora, contract drafting, treaty interpretation, and judgment summarisation each have grammars Yuho does not natively model.

It *is* a claim that the gap between a drafted penal section and an executable artefact is **narrower** than the existing literature suggests, and that an appropriately-shaped grammar dissolves a class of previously-reported encoding obstacles, leaving a residue tractable at full coverage for one statute family.

## Future work

Three concrete strands:

1. **Cross-jurisdiction generalisation.** Encoding a 50-section sample of the Indian Penal Code to test grammar fit and tooling reuse across the wider Anglo-Indian penal-code family. The Akoma Ntoso transpiler is the on-ramp.
2. **Deeper precedent integration.** Lifting case-law holding strings into structured constraints that modify element burden qualifiers when the matching predicate fires.
3. **Evaluator-side `apply_scope`.** Elaborating the cross-section composition primitive into a full element-graph executor that returns bindings, not just a structural "does this scope exist" predicate.

## Artefact

The Yuho compiler, encoded library, and tooling are open-source at <https://github.com/gongahkia/yuho>. The paper itself — including the build pipeline that injects coverage statistics into the manuscript at compile time — lives in the same repository under [`paper/`](../).
