# Revision Roadmap

**Manuscript**: Yuho: A DSL for Encoding the Singapore Penal Code as Executable Statute
**Decision**: Major Revision
**Target before re-review**: Address all P0 + at least 80% of P1 items.

This roadmap is sorted by priority (P0 = blocks even arXiv post; P1 = blocks peer-venue Accept; P2 = strongly recommended; P3 = optional). Each item is traceable to a specific reviewer concern and ships with a concrete proposed fix.

---

## P0 — Blocks even arXiv preprint posting

### P0-1. Reconcile L3 coverage figures (100% vs 23%)
- **Origin**: CONS-1 (EIC W1, Methodology W4, DA C-1)
- **Files**: `paper/sections/limitations.tex` L69; `paper/sections/evaluation.tex` (`\subsec:coverage_eval`); `paper/methodology/methodology.tex` (\statLThreePass)
- **Fix**: Decide whether 23% or 100% is correct. If 100% is correct, delete the "23\%" sentence in limitations.tex. If 23% reflects an external-review subset, rename the variable (e.g., `\statLThreeExternalReviewed`) and report both numbers separately. Verify `library/penal_code/_coverage/coverage.json` produces the intended figure via `scripts/coverage_report.py`.
- **Effort**: 30 minutes.

### P0-2. Reconcile Alloy transpiler SLOC (26k vs 4.2k)
- **Origin**: CONS-4 (EIC SC-5, Perspective SC-13)
- **Files**: `paper/sections/implementation.tex` (`\subsec:transpilers` line referencing "~26k SLOC"); Table~\ref{tab:sloc}
- **Fix**: Run `wc -l src/yuho/transpile/alloy/*.py` (or equivalent) and report the actual figure. Almost certainly the prose should read "~2.6k" or the table aggregate should rise. Pick one and reconcile.
- **Effort**: 15 minutes.

### P0-3. Reframe "machine-checkable" to "encoding-well-formedness"
- **Origin**: CONS-9 (DA C-2, Perspective SC-7)
- **Files**: `paper/main.tex` abstract; `paper/sections/introduction.tex`; `paper/sections/implementation.tex` (`\subsec:verify`)
- **Fix**: In the abstract, replace "executable, machine-checkable artefacts" with "executable artefacts whose encoding is machine-checkable for structural and inter-section consistency." Add one sentence in `\subsec:verify` that the verification stack checks well-formedness of the encoding, not legal correctness. Move the existing `\sec:limitations` disclaimer ("for checking the encoding is well-formed, not for adjudicating the law") up to an early footnote in `\sec:intro`.
- **Effort**: 1 hour.

---

## P1 — Blocks peer-reviewed venue Accept

### P1-1. Propagate the L3-self-stamp disclaimer to the headline numbers
- **Origin**: CONS-2 (Methodology W1/SC-1, Domain §3, Perspective §4, DA C-1)
- **Files**: `paper/main.tex` abstract; `paper/sections/introduction.tex`; `paper/sections/evaluation.tex`; `paper/sections/conclusion.tex`
- **Fix**: Wherever 524/524 L3 appears, attach a clause: "L3 stamps are author-administered; external-reviewer validation is future work." Or rename `\statLThreePass` to `\statLThreeAuthorStamped` to make the unit explicit at the macro level. Or commission an external 30-section sample (P1-2) and report agreement, then keep the headline.
- **Effort**: 1 hour for in-place rewording; ~1 week if you commission the external sample.

### P1-2. Run the n=30 hand-rated fidelity-diagnostic spot-check (the punch-list item)
- **Origin**: CONS-3 (EIC W5, Methodology W2/SC-2, Perspective SC-9, DA C-3)
- **Files**: New harness; `paper/sections/evaluation.tex` (`\subsec:fidelity_eval`); `paper/methodology/fidelity_hits.json` (extend with TP/FP labels)
- **Fix**: For each of the 4 diagnostics, sample 30 warnings (stratified across G4 / fab-fine / fab-caning / G11), hand-rate TP vs FP against the canonical SSO text, compute Wilson 95% CI on precision. Report per-diagnostic precision in `\subsec:fidelity_eval`. Methodology reviewer recommends n=50 (n=30 gives borderline-wide CIs for G11) — adopt n=50 if the cost is moderate.
- **Effort**: 4–8 hours of careful hand-rating per check (16–32 hours total). The single most cost-effective improvement to the paper.

### P1-3. Replace throughput metric with per-section agent run-time distribution
- **Origin**: CONS-5 (EIC W5, Methodology W3/SC-3, DA M-6)
- **Files**: `paper/sections/evaluation.tex` (`\subsec:throughput`); `paper/methodology/throughput.json`; `scripts/paper_methodology.py`
- **Fix**: Drop the median-1-day / p95-1-day claim. Replace with: per-section agent-minutes distribution (you already estimate 60–120s/section in `evaluation.tex` L257). Report median, IQR, max. Investigate the `min=-1` data point (probably a `last_verified` written before first commit; fix the measurement pipeline). If you keep the calendar number, demote it to a footnote with the dispatcher-artefact caveat already in §subsec:threats.
- **Effort**: 2–4 hours.

### P1-4. Preserve the original 14-gap taxonomy honestly
- **Origin**: DA M-1 (post-hoc trimming); also touches Methodology SC-4 (catalogue construction not reproducible)
- **Files**: `paper/sections/design.tex` (Table~\ref{tab:gaps}); `paper/sections/introduction.tex` contribution #4
- **Fix**: Add columns to Table~\ref{tab:gaps}: (a) initial classification when the gap was first named, (b) final classification, (c) chronological discovery date. Be explicit in §sec:intro that 3/14 (G2, G7, G10) were re-classified or deferred, and that G10 is the hardest and remains future work. Cite the discovery log (`docs/researcher/phase-c-gaps.md` per `paper_methodology.py:303`) so the catalogue is reproducible.
- **Effort**: 2 hours.

### P1-5. Add a hard worked example (s302 or abetment)
- **Origin**: CONS-8 (EIC SC-3, DA M-2)
- **Files**: `paper/sections/design.tex` (after `\subsec:s415`)
- **Fix**: Promote s302 (already referenced for nested-combinator example) to a full figure showing nested penalty + `when` conditional + at least one Chapter IV exception cross-reference. Or add an abetment example (s107) that exercises the planned-but-deferred G10 cross-section reference, using it as a worked future-work demonstration. Either way, the paper needs at least one example that exercises the contributions claimed as distinctive.
- **Effort**: 4 hours.

### P1-6. Correct comparison matrix factual errors and add adversarial columns
- **Origin**: CONS-7 (Domain §4, DA M-3)
- **Files**: `paper/sections/related.tex` (Tables~\ref{tab:expressivity} and \ref{tab:tooling}); `paper/sections/background.tex` (`\subsec:rel_catala`)
- **Fix**:
  - Table 3 LegalRuleML / Burden qualifiers: change `---` to `\checkmark` (LegalRuleML has `<lrml:hasReversedBurdenOfProof>`).
  - Table 3 LegalRuleML / Causal-temporal: change `---` to `~` (LegalRuleML has `<lrml:hasTemporalCharacteristics>`).
  - Table 3 Catala / Verbatim illustration: change `---` to `~` (Catala source supports rendered annotations).
  - Add 2 columns where Yuho is not first: e.g., "Soundness theorem" and "Deployed external users". Acknowledge the inversion in the prose ("Catala dominates these axes").
  - `\subsec:rel_catala` rephrase: "We adopt Catala's prioritised-default *semantics* and re-implement it as a Z3 encoding; Catala itself compiles to OCaml/Python and we do not inherit its soundness proof." Currently the prose risks suggesting Catala has a Z3 backend.
  - Tighten `\subsec:rel_akn` "<modifies> element family" → cite the AKN spec section on `<activeModifications>`/`<passiveModifications>` with `<textualMod>` / `<meaningMod>` etc.
- **Effort**: 3–4 hours.

### P1-7. Expand the bibliography with critical missing prior art
- **Origin**: CONS-6 (Domain Missing Prior Art §5, EIC Minor Comments)
- **Files**: `paper/references.bib`; `paper/sections/background.tex`; `paper/sections/related.tex`
- **CRITICAL refs to add (Domain §5)**:
  1. eFLINT (van Doesburg, van Engers, Searls — GPCE 2020) — closest peer to Yuho's deontic element types
  2. Bench-Capon & Coenen 1992 (isomorphism) — the theoretical home of "statute-as-source-of-truth"
  3. DMN (OMG Decision Model and Notation v1.4) — deployed competitor
  4. Symboleo (Soavi et al., RE 2020) — contract-spec language with formal semantics
  5. Governatori on RuleML / defeasible deontic logic — mandatory for the deontic-types claim
  6. Prakken & Sartor 2009 on burden of proof — mandatory for the burden-qualifier claim
  7. von Wright 1951 / SDL handbook — deontic-logic foundations
- **SUGGESTED refs (Domain)**: Boella & van der Torre on normative systems; RegelSpraak; Stipula; Hohfeld; Atkinson & Bench-Capon 2005.
- **Replace placeholder**: `hammond1983rights` (cited via secondary literature) — find a verifiable Hammond reference or drop. Augment `lam4` / `lexscript` / `ldoc` with retrieval dates and commit hashes.
- **Drop**: `lessig1999code` if it remains uncited, or cite and engage Lessig's "code is law" thesis (which is the inverse of "law as code").
- **Effort**: 1–2 days for substantive engagement (read each ref, write a few sentences in `\sec:background` or `\sec:related`).

### P1-8. Engage the isomorphism principle as the home of the "statute-as-source-of-truth" thesis
- **Origin**: Domain Theory Concerns 1, 5, 7
- **Files**: `paper/sections/conclusion.tex`; new ½-page in `paper/sections/background.tex` (after `\subsec:logic_programming_origins`)
- **Fix**: Add a paragraph in §sec:background discussing isomorphism (Bench-Capon & Coenen 1992) as the principle of clause-for-clause representation. Acknowledge the standard objections (normalisation tension, open-textured terms). State whether Yuho takes the isomorphism position or departs from it. The §sec:conclusion thesis "statute-as-source-of-truth is a viable posture" can then land as a defended position rather than an asserted one.
- **Effort**: 4 hours.

---

## P2 — Strongly recommended

### P2-1. Tighten the "engineering exercise" framing
- **Origin**: EIC Weakness 4
- **Files**: `paper/sections/introduction.tex` (last paragraph); `paper/sections/conclusion.tex` (last sentence)
- **Fix**: Replace "closing the gap [...] is mostly an engineering exercise once the grammar is right" with: "the empirical claim of this paper is that an appropriately-shaped grammar dissolves a class of previously-reported encoding obstacles." Keep the substance, lose the self-deprecation. For arXiv this is fine; for TPJ/SLE/ICAIL it reads as the authors arguing their own work is non-research.
- **Effort**: 30 minutes.

### P2-2. Add G11 separated reporting + grammar-design feedback
- **Origin**: CONS-10 (Methodology W2, Perspective SC-14, DA m-1)
- **Files**: `paper/sections/evaluation.tex` (`\subsec:fidelity_eval`)
- **Fix**: Report fidelity hits with G11 separated: "152 hits across G4 + fab-fine + fab-caning; 208 additional G11 hits at low precision (precision X% per spot-check, P1-2)". Add a sentence considering the grammar-design implication: if the all_of-vs-any_of ambiguity cannot be resolved by heuristic, perhaps the grammar should require explicit per-pair connectives — a grammar-design response to a lint signal, exactly the gap-vs-lint feedback loop §subsec:gaps articulates.
- **Effort**: 1 hour (after P1-2).

### P2-3. Add gap-frequency column to Table~\ref{tab:gaps}
- **Origin**: EIC SC-4
- **Files**: `paper/sections/design.tex`
- **Fix**: Add a "Frequency" column — number of sections that triggered each gap, from `paper/methodology/gap_frequency.json`. The narrative in `\subsec:gaps_eval` already describes G6/G8/G12 as dominant; surface the numbers in the table.
- **Effort**: 1 hour.

### P2-4. Promote the gap-classification methodology to headline contribution
- **Origin**: Perspective §6 (SC-4), partially EIC SC-1
- **Files**: `paper/sections/introduction.tex` (Contributions paragraph); abstract
- **Fix**: Currently the gap catalogue is contribution #4 of four. Per Perspective, this is the most defensible PL-research-shaped contribution. Reframe as: "We propose a methodology — *gap classification by resolution mechanism* — that distinguishes grammar bloat from diagnostic enrichment, and apply it to a 524-section corpus surfacing fourteen gaps (ten genuine grammar limitations resolved by parser extension, four diagnostic-layer issues resolved by linter extension, two reclassified as not-a-gap, and one deferred semantic resolver)." Re-order the four contributions: (1) artefact = grammar + corpus, (2) tooling, (3) gap-classification methodology, (4) empirical findings on the 524-section sweep.
- **Effort**: 2 hours.

### P2-5. Address single-jurisdiction either by piloting IPC or downgrading the claim
- **Origin**: EIC §2.4, Methodology Threat 4, Domain SC-10, Perspective §6 (SC-12), DA M-8
- **Files**: `paper/sections/limitations.tex`; `paper/sections/conclusion.tex`; `paper/sections/introduction.tex`
- **Two paths**:
  - **(a) Run the 50-section Indian Penal Code pilot promised in §sec:limitations.** Report grammar-fit, tooling-reuse rate, and any new gaps surfaced. This converts "plausibly portable" into evidence and substantially strengthens contribution #4. Effort: 1–2 weeks.
  - **(b) Downgrade the cross-jurisdiction claim everywhere.** Replace "plausibly portable" with "an empirical question we have not yet tested" in §sec:intro and §sec:limitations. Effort: 1 hour.
- The DA flags this as M-8 ("case study masquerading as research") — without (a), the contribution is honestly a case study.

### P2-6. Replace the SLOC density-ratio heuristic
- **Origin**: DA M-4; partial Methodology SC-7
- **Files**: `paper/sections/implementation.tex` (`\subsec:engineering-numbers` last paragraph)
- **Fix**: Either drop the "1:1-to-2:1 productive range" heuristic entirely (it is unsourced and reads like motivated reasoning), or replace SLOC with a logical-LOC counter (`cloc` / `scc`) and add a measure that supports the density argument (e.g., tokens-per-statute-section ratio between .yh and canonical text).
- **Effort**: 1 hour.

### P2-7. Methodology section / appendix consolidation
- **Origin**: Methodology Reproducibility §"What's missing"
- **Files**: New `paper/methodology/methodology.tex` prose; or appendix
- **Fix**: The current `paper/methodology/methodology.tex` is 7 `\newcommand` definitions and no prose. Add a methodology section (or appendix) that consolidates: (a) gap-discovery procedure, (b) the 11-point L3 checklist verbatim, (c) the diagnostic definitions (formal predicate per check), (d) the n=50 spot-check sample plan with Wilson-CI calculation, (e) the `coverage.json` schema. This dramatically improves methodological reproducibility.
- **Effort**: 1 day.

### P2-8. Engage language-workbench / MDE / BX / projectional-editing literatures
- **Origin**: Perspective §5
- **Files**: `paper/sections/related.tex` (new subsection `\subsec:rel_pl`); `paper/sections/background.tex` (additions to `\subsec:tooling`)
- **Fix**: Add ½-page subsection in §sec:related citing: Erdweg et al. (state-of-the-art of language workbenches, 2013/2015); Voelter on projectional editing / MPS; Visser et al. on Spoofax; Foster et al. on bidirectional transformations / lenses; Mernik/Heering/Sloane on when-to-build-a-DSL (ACM CSUR 2005). For an SLE/Onward! audience this is required; for arXiv it is recommended.
- **Effort**: 4–6 hours.

---

## P3 — Optional / nice-to-have

- **EIC SC-1**: Re-order four contributions to three (artefact, tooling, methodology).
- **EIC SC-2**: Reframe "the gap is mostly a grammar gap" from declarative claim to research question.
- **EIC SC-7**: Expand `\subsec:rel_catala` with side-by-side Catala-vs-Yuho encoding sketch of s415.
- **EIC SC-8**: State the empirical falsifier for the implicit grammar-completeness claim ("a successor amendment introducing a novel pattern would surface as G15").
- **EIC Minor**: Verify all 4 figures exist; resolve "six transpilers" vs project-memory's 13 targets; align title subtitle with body's four contributions; tighten "L3" terminology (tier vs procedure).
- **Methodology SC-10**: Tag pre-Phase-C grammar in git, run the L1+L2 pipeline, report pre-fix-vs-post-fix delta.
- **Methodology SC-9**: Pre-register inter-rater agreement metric (Cohen's kappa, item-level).
- **Domain Theory 5**: Reframe "common-law penal code" → "codified penal statute applied within a common-law jurisdiction".
- **Domain SC-1**: Separate the criminal-doctrine kind (actus_reus / mens_rea / circumstance) from the deontic-modality flag (obligation / prohibition / permission), or explain why mixing them is intentional.
- **Domain SC-2**: Acknowledge in `\subsec:exceptions` that integer-priority encoding is an encoder choice, not a doctrinal fact.
- **Domain SC-3**: Specify the verification semantics that distinguish `or_both` from `alternative` (Z3 encoding).
- **Domain SC-4**: Resolve `guard` vs `condition` keyword inconsistency in `\subsec:exceptions`.
- **Domain SC-5**: Qualify the AKN amendment-lineage match as "first-order temporal versioning, not full textual-modification tracking" (or deepen the model).
- **Perspective FA-1, FA-2**: Acknowledge projectional-editing as an alternative surface; clarify that "statute-shape" is one drafting tradition, not a fundamental primitive.
- **Perspective SC-7**: Walk through s299/s300 mutual-exclusion verification query end-to-end.
- **Perspective SC-8**: Acknowledge LSP adoption is single-user (the author).
- **DA M-7**: Demote case-law anchors from "structural primitive" to "metadata field" since holdings are opaque text.

---

## Estimated Revision Effort

| Path | Items | Total effort |
|------|-------|--------------|
| arXiv-ready (P0 only) | P0-1, P0-2, P0-3 | ~2 hours |
| arXiv-respectable (P0 + minimum P1 propagation) | P0 + P1-1, P1-3, P1-4 | ~6 hours |
| Peer-venue submittable (P0 + all P1) | All P0 + all P1 | ~4–6 days |
| Strong peer-venue (P0 + P1 + P2) | + P2 items | ~2 weeks |
| Top-tier PL venue | + soundness sketch, external user, IPC pilot | ~2 months |

The single highest-leverage item is **P1-2 (run the n=30 hand-rate)** — it converts the central evaluation finding from "raw warnings, true-positive rate not yet measured" to "warrant-bearing precision claim" at the cost of 16–32 hours of hand-rating.

---

## R&R Mode (next step)

When revisions are complete, run ARS academic-paper-reviewer in `re-review` mode. The re-review verifies each item in this roadmap against the revised manuscript using an R&R Traceability Matrix (Author's Claim + Verified? columns). Re-review uses a reduced 3-agent panel (field_analyst + EIC + editorial_synthesizer) and produces a residual-issues list rather than a fresh Phase 1.
