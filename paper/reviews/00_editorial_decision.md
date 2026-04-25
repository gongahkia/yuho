# Editorial Decision Letter

**Manuscript**: Yuho: A Domain-Specific Language for Encoding the Singapore Penal Code as Executable Statute
**Mode**: ARS academic-paper-reviewer `full` (5-panel review, arXiv-preprint calibration)
**Synthesizer**: Editorial Synthesizer
**Date**: 2026-04-25

---

## Decision

**Major Revision.**

**Critical-issue count (Devil's Advocate)**: 3 → per ARS Iron Rule #4, Accept is foreclosed.
**Reviewer convergence**: 5/5 reviewers independently recommend Major Revision.
**Confidence**: All five reviewers reported confidence 4/5.

For arXiv preprint posting, the paper is publishable *now* after the two objective consistency fixes (L3 100%-vs-23% and Alloy 26k-vs-4.2k SLOC) — these are factual contradictions any careful reader will notice and they erode trust in the rest of the quantitative claims. For peer-reviewed venue submission (Onward! / Programming Journal / SLE / ICAIL / JURIX), Major Revision is required.

---

## Per-Dimension Score Synthesis (0–100)

| Dimension | EIC | Methodology | Domain | Perspective | Median |
|---|---|---|---|---|---|
| Originality | 70 | — | — | 45 | 57 |
| Significance / Field Contribution | 65 | — | 70 | — | 67 |
| Clarity | 70 | — | — | — | 70 |
| Soundness / Internal Validity | 55 | 35 | — | — | 45 |
| Reproducibility | 80 | 62 | — | — | 71 |
| Methodological Rigor | — | 38 | — | — | 38 |
| Statistical Reporting | — | 25 | — | — | 25 |
| Sample Adequacy | — | 45 | — | — | 45 |
| Literature Coverage | — | — | 35 | 35 | 35 |
| Theoretical Framing | — | — | 45 | 50 | 47 |
| Domain Accuracy | — | — | 65 | — | 65 |
| Comparison Fairness | — | — | 55 | — | 55 |
| Practical Impact | — | — | — | 65 | 65 |
| Cross-Disciplinary Reach | — | — | — | 60 | 60 |

**Lowest scores**: Statistical Reporting (25), Literature Coverage (35), Methodological Rigor (38), Internal Validity (35), PL Engagement (35). The paper's empirical and bibliographic foundations are the binding constraints.

**Highest scores**: Reproducibility (80) and Domain Accuracy (65). The artefact is real and most factual claims about competitor systems are accurate.

---

## Consensus Findings (≥3 reviewers, evidence-traced)

These are the issues every careful reader will see. Each is traced to the originating reviewer report; the synthesizer does not invent any of them.

### CONS-1: 100%-vs-23% L3 coverage inconsistency
- **Reviewers**: EIC (Weakness 1), Methodology (Weakness 4 / SC-11), DA (C-1)
- **Evidence**: `\subsec:coverage_eval` reports `\statLThreePass/\statRawSections (100%)`; `limitations.tex` L69 says "The 23% L3 coverage figure is honest in this respect."
- **Severity**: Hard correctness defect. Internal contradiction.
- **Status**: Blocks even arXiv posting per EIC.

### CONS-2: L3 stamp is self-administered (encoder = reviewer = dispatcher author = checklist author)
- **Reviewers**: Methodology (Weakness 1, SC-1), Domain (§3), Perspective (§4), DA (C-1)
- **Evidence**: `limitations.tex` L59-72 admits encoder=reviewer; abstract/intro/conclusion foreground 524/524 without the disclaimer.
- **Severity**: Critical (DA C-1). Headline number trades on epistemic content the same paper disclaims elsewhere.
- **Status**: Blocks Accept.

### CONS-3: Fidelity diagnostic precision unestablished but central
- **Reviewers**: EIC (Weakness 5), Methodology (Weakness 2 / SC-2), Perspective (§4 weakness 2 / SC-9), DA (C-3)
- **Evidence**: `evaluation.tex` L122 explicitly says the n=30 hand-rate is "on the punch list before submission". Largest bucket (G11=208) is "lowest precision" by author admission.
- **Severity**: Critical (DA C-3). One of the paper's two empirical pillars is unmeasured.
- **Status**: Blocks Accept.

### CONS-4: Alloy transpiler 26k vs Table~\ref{tab:sloc} 4.2k SLOC contradiction
- **Reviewers**: EIC (SC-5), Perspective (SC-13)
- **Evidence**: `\subsec:transpilers` says Alloy is ~26k SLOC; Table 2 reports 4,200 SLOC for all six transpilers combined.
- **Severity**: Hard correctness defect. Likely a typo (probably 2.6k).
- **Status**: Must be reconciled before any release.

### CONS-5: Throughput median = p95 = 1 day is degenerate; conflates calendar with compute
- **Reviewers**: EIC (Weakness 5), Methodology (Weakness 3 / SC-3 / Threat 6), DA (M-6)
- **Evidence**: `methodology.tex` confirms `\statThroughputMedian = \statThroughputP95 = 1`. `throughput.json` shows 499/524 sections committed on a single day (2026-04-24). Min=-1 indicates a measurement bug.
- **Severity**: Major. Headline throughput claim is meaningless as currently presented.
- **Status**: Drop the metric or replace with per-section agent-min distribution.

### CONS-6: Bibliography is too thin / has placeholders / has uncited entries
- **Reviewers**: EIC (Minor / Weakness), Domain (Weakness 1 / Missing Prior Art / SC-12-14)
- **Evidence**: 14 entries; `lam4`, `lexscript`, `ldoc`, `hammond1983rights` flagged as placeholder/secondary; `lessig1999code` appears uncited; the field has 30+ years of literature on deontic logic, isomorphism, burdens, contracts, normative systems that the paper substantially ignores.
- **Severity**: Major for any peer venue; minor for arXiv.
- **Critical missing refs (Domain reviewer)**: eFLINT, Bench-Capon & Coenen 1992 (isomorphism), DMN, Symboleo, Governatori on RuleML, Prakken on burden of proof, von Wright/SDL.

### CONS-7: Comparison matrix has factual errors and cherry-picked columns
- **Reviewers**: Domain (§4 audit), DA (M-3)
- **Evidence**:
  - LegalRuleML / Burden qualifiers: `---` is wrong — LegalRuleML has `<lrml:hasReversedBurdenOfProof>`. Should be `~` or `\checkmark`.
  - Catala compilation framing: `\subsec:rel_catala` "compilation to Z3 follows Catala's prioritised-rewriting algorithm" risks suggesting Catala has a Z3 backend — it compiles to OCaml/Python; the Z3 hookup is the authors' own.
  - AKN amendment-lineage description (`<modifies>` family) is imprecise — should be `<activeModifications>`/`<passiveModifications>` containing `<textualMod>`/`<meaningMod>`.
  - Several `---` cells should be `~` (Catala / illustration; LegalRuleML / temporal).
  - Columns chosen post-hoc to favor Yuho — omits proven semantics, soundness theorem, deployed users, peer-reviewed publication, multilingual, jurisdictional variety.
- **Severity**: Major. Comparison matrix is the strongest editorial artefact (per EIC §3) and its credibility is damaged by these errors.

### CONS-8: Worked example s415 is the easy case
- **Reviewers**: EIC (SC-3), DA (M-2)
- **Evidence**: s415 has typed elements + simple penalty + 3 illustrations + no exceptions in fragment; does not exercise G10, G12, G13, abetment chapter (s107–s120 explicitly future work).
- **Severity**: Major. The contribution claims (penalty algebra, exception priority, nested combinators) are not exercised in the only worked example.

### CONS-9: Verification-scope frame mismatch ("machine-checkable")
- **Reviewers**: Perspective (SC-7), DA (C-2 / M-10)
- **Evidence**: Abstract: "executable, machine-checkable artefacts". `\sec:limitations`: "the verification stack is for checking that the *encoding* is well-formed, not for adjudicating the *law*."
- **Severity**: Critical (DA C-2). Reframes the paper's positioning.
- **Status**: Blocks Accept.

### CONS-10: G11 (40% flag rate) is operationally close to "warn on every section"
- **Reviewers**: Methodology (Weakness 2), Perspective (SC-14), DA (m-1)
- **Evidence**: 208/524 = 39.7%. Author admits low precision.
- **Severity**: Major. Removing G11 collapses the headline 360 fidelity warnings to 152.

---

## Disagreements / Single-Reviewer Issues (kept for record)

The synthesizer surfaces these without taking a position; the author may judge their weight:

- **EIC**: Re-order four contributions into three (artefact / tooling / methodology). [Editorial preference; no other reviewer raised it.]
- **Methodology (SC-10)**: Tag pre-Phase-C grammar in git, run the L1+L2 pipeline against it, report the pre-fix-vs-post-fix delta. [Cited by Methodology only; high-value if cheap to run.]
- **Methodology (Threat 5)**: Agent reviewer drift — `gpt-5.4` is implicitly bound to a model snapshot the authors do not pin. [Cited by Methodology only.]
- **Domain (Theory Concern 1, 5, 7)**: Engage the isomorphism principle (Bench-Capon & Coenen 1992); reframe "common-law penal code" to acknowledge codified-civil-style heritage; promote "statute-shaped" from pragmatic engineering choice to position in a long-running debate. [Cited by Domain only; high theoretical value but non-blocking for arXiv.]
- **Perspective (§5)**: Engage language-workbench / MDE / BX / projectional-editing literatures (MPS, Spoofax, Erdweg et al.). [Cited by Perspective only; required for a top-tier PL venue.]
- **Perspective (FA-1)**: Consider projectional editing as an alternative surface for legal encoding. [Cited by Perspective only.]
- **DA (M-9)**: Disclose chronological order of grammar-vs-gap discovery (iterative-grammar hypothesis). [DA only.]
- **DA (M-7)**: Demote case-law anchors from "structural primitive" to "metadata field" since holdings are opaque text. [DA only; substantive.]
- **DA (M-4)**: Drop or appendix-relegate the SLOC density-ratio heuristic (38.7k:16.4k). [DA only.]

---

## Devil's Advocate Strongest Counter-Argument (verbatim)

> The paper's headline finding — "524/524 at L1+L2 + 524/524 at L3" — is a coverage statistic produced by a closed loop in which the author is simultaneously the grammar designer, the encoder, the L3 reviewer dispatcher, the checklist author, and the agent operator. … Yet the abstract, intro contributions, and conclusion all foreground 524/524 as if it were external validation, and the paper's central thesis — that "the gap between drafted penal section and executable encoding is mostly a grammar gap" — is supported by no evidence other than the author's own encoding pass.

The synthesizer notes this is the binding rhetorical defect in the paper: the disclaimers exist (`\sec:limitations` is unusually candid) but they are quarantined and do not propagate to the abstract, intro, evaluation summary, or conclusion. The fix is not new evidence — it is propagation of existing hedges to the headline claims.

---

## Editorial Recommendation Summary

**For arXiv preprint posting (current target)**:
- **Required before posting**: CONS-1 (L3 100/23 reconciliation), CONS-4 (Alloy SLOC reconciliation), CONS-9 (machine-checkable framing).
- **Strongly recommended before posting**: CONS-2 (propagate L3 self-stamp disclaimer to abstract/intro), CONS-3 (run the n=30 hand-rate; report Wilson CIs), CONS-5 (drop or replace throughput).
- **Optional but valuable**: CONS-6 placeholder bibs, CONS-7 matrix corrections, CONS-8 add s302 / abetment worked example.

**For peer-reviewed venue (Onward! Essays, TPJ, SLE, ICAIL, JURIX)**:
- **All consensus findings (CONS-1 through CONS-10) must be addressed.**
- **Plus**: at least 8 of the missing prior-art references (CONS-6 detail), engagement with isomorphism principle (Domain Theory Concern 1), language-workbench literature engagement (Perspective §5), and either a 50-section Indian Penal Code pilot or downgrade of the cross-jurisdiction claim.
- Best venue fits identified: Onward! Essays > TPJ > SLE > ICAIL/JURIX. Not a fit for top-tier PL venues (PLDI, POPL, ICFP) without a soundness theorem.

**For top-tier PL venue**: This is a Major-and-then-some path. Requires (a) a formal property of the grammar or the verification stack (e.g., a soundness sketch for the priority-rewriting compilation to Z3), (b) at least one external user with task-completion data, (c) cross-jurisdiction empirical evidence. Currently outside the paper's design budget.

---

## Phase 2.5: Revision Coaching (offered)

ARS Phase 2.5 (Socratic Revision Coaching) is available — the EIC agent walks you through five questions to help you build your own revision strategy:
1. After reading the reviews, what surprised you most?
2. Which consensus issue did you already know about, and which did you not?
3. If you could only fix three things before re-posting, which three?
4. How will you respond to the Devil's Advocate's circularity claim?
5. What's your prioritisation rule for the major issues?

You may also choose **"just fix it"** to skip Coaching and go directly to the Revision Roadmap (next file: `00_revision_roadmap.md`).
